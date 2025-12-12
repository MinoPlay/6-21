from datetime import datetime, timedelta
from collections import defaultdict
from app.models import HabitEntry, Habit
from app import db

def calculate_current_streak(habit_entries):
    """Calculate current streak counting backwards from yesterday (today never affects streak)."""
    if not habit_entries:
        return 0
    
    # Sort entries by date descending
    sorted_entries = sorted(habit_entries, key=lambda x: x.date, reverse=True)
    
    today = datetime.now().date()
    
    streak = 0
    # Always start from yesterday - today never counts for or against the streak
    expected_date = today - timedelta(days=1)
    
    for entry in sorted_entries:
        if entry.date == expected_date and entry.completed:
            streak += 1
            expected_date -= timedelta(days=1)
        elif entry.date < expected_date:
            # There's a gap, streak is broken
            break
    
    return streak

def calculate_longest_streak(habit_entries):
    """Calculate the longest streak ever achieved."""
    if not habit_entries:
        return 0
    
    # Sort entries by date
    sorted_entries = sorted(habit_entries, key=lambda x: x.date)
    
    max_streak = 0
    current_streak = 0
    prev_date = None
    
    for entry in sorted_entries:
        if entry.completed:
            if prev_date is None or (entry.date - prev_date).days == 1:
                current_streak += 1
            else:
                current_streak = 1
            max_streak = max(max_streak, current_streak)
            prev_date = entry.date
        else:
            current_streak = 0
            prev_date = entry.date
    
    return max_streak

def calculate_completion_rate(habit_entries, start_date, global_challenge_start_date=None):
    """Calculate completion percentage with dual percentages (tracked vs challenge).
    
    Args:
        habit_entries: List of HabitEntry objects for a habit
        start_date: Date when habit tracking started (habit.created_at.date())
        global_challenge_start_date: Optional global start date for the entire challenge
    
    Returns:
        Dict with tracked and challenge completion stats
    """
    if not habit_entries:
        # If no entries but we have a global start date, calculate challenge days from that
        if global_challenge_start_date:
            today = datetime.now().date()
            challenge_days = (today - global_challenge_start_date).days + 1
            challenge_days = max(1, challenge_days)
        else:
            challenge_days = 0
            
        return {
            'tracked_completed': 0,
            'tracked_total': 0,
            'tracked_percent': 0.0,
            'challenge_completed': 0,
            'challenge_days': challenge_days,
            'challenge_percent': 0.0
        }
    
    # Tracked percentage (of days that were tracked)
    completed = sum(1 for entry in habit_entries if entry.completed)
    tracked_total = len(habit_entries)
    tracked_percent = round((completed / tracked_total) * 100, 1) if tracked_total > 0 else 0.0
    
    # Challenge percentage - use global start date if provided, otherwise use earliest entry
    if global_challenge_start_date:
        actual_start_date = global_challenge_start_date
    else:
        # Fallback to earliest entry date for this habit
        earliest_entry_date = min(entry.date for entry in habit_entries)
        actual_start_date = min(start_date, earliest_entry_date)
    
    today = datetime.now().date()
    # Count all days from actual start to today (inclusive)
    challenge_days = (today - actual_start_date).days + 1  # +1 to include start date
    challenge_days = max(1, challenge_days)  # Ensure at least 1 day
    challenge_percent = round((completed / challenge_days) * 100, 1) if challenge_days > 0 else 0.0
    
    return {
        'tracked_completed': completed,
        'tracked_total': tracked_total,
        'tracked_percent': tracked_percent,
        'challenge_completed': completed,
        'challenge_days': challenge_days,
        'challenge_percent': challenge_percent
    }

def get_perfect_days(user_id):
    """Count days where all 6 habits were completed."""
    # Get all habits for user
    habit_ids = [h.id for h in Habit.query.filter_by(user_id=user_id).all()]
    
    if len(habit_ids) != 6:
        return 0
    
    # Get all dates with entries
    dates_with_entries = db.session.query(HabitEntry.date).filter(
        HabitEntry.habit_id.in_(habit_ids)
    ).distinct().all()
    
    perfect_count = 0
    for (date,) in dates_with_entries:
        # Check if all 6 habits were completed on this date
        completed = db.session.query(db.func.count(HabitEntry.id)).filter(
            HabitEntry.habit_id.in_(habit_ids),
            HabitEntry.date == date,
            HabitEntry.completed == True
        ).scalar()
        
        if completed == 6:
            perfect_count += 1
    
    return perfect_count

def get_almost_perfect_days(user_id):
    """Count days where exactly 5 out of 6 habits were completed."""
    # Get all habits for user
    habit_ids = [h.id for h in Habit.query.filter_by(user_id=user_id).all()]
    
    if len(habit_ids) != 6:
        return 0
    
    # Get all dates with entries
    dates_with_entries = db.session.query(HabitEntry.date).filter(
        HabitEntry.habit_id.in_(habit_ids)
    ).distinct().all()
    
    almost_perfect_count = 0
    for (date,) in dates_with_entries:
        # Check if exactly 5 habits were completed on this date
        completed = db.session.query(db.func.count(HabitEntry.id)).filter(
            HabitEntry.habit_id.in_(habit_ids),
            HabitEntry.date == date,
            HabitEntry.completed == True
        ).scalar()
        
        if completed == 5:
            almost_perfect_count += 1
    
    return almost_perfect_count

def get_days_active(user_id):
    """Count total unique days with at least one habit entry."""
    habit_ids = [h.id for h in Habit.query.filter_by(user_id=user_id).all()]
    
    if not habit_ids:
        return 0
    
    unique_days = db.session.query(db.func.count(db.func.distinct(HabitEntry.date))).filter(
        HabitEntry.habit_id.in_(habit_ids)
    ).scalar()
    
    return unique_days or 0



def get_habit_stats(habit, global_challenge_start_date=None):
    """Get comprehensive statistics for a habit.
    
    Args:
        habit: Habit object
        global_challenge_start_date: Optional global start date for challenge calculations
    """
    entries = habit.entries
    completion_data = calculate_completion_rate(entries, habit.created_at.date(), global_challenge_start_date)
    
    return {
        'current_streak': calculate_current_streak(entries),
        'longest_streak': calculate_longest_streak(entries),
        'completion_rate': completion_data['tracked_percent'],  # For backwards compatibility
        'tracked_completed': completion_data['tracked_completed'],
        'tracked_total': completion_data['tracked_total'],
        'tracked_percent': completion_data['tracked_percent'],
        'challenge_completed': completion_data['challenge_completed'],
        'challenge_days': completion_data['challenge_days'],
        'challenge_percent': completion_data['challenge_percent']
    }

def get_overall_stats(habits, user_id):
    """Get overall statistics across all habits."""
    # Find the global challenge start date (earliest entry across ALL habits)
    global_challenge_start_date = None
    for habit in habits:
        if habit.entries:
            earliest_for_habit = min(entry.date for entry in habit.entries)
            if global_challenge_start_date is None or earliest_for_habit < global_challenge_start_date:
                global_challenge_start_date = earliest_for_habit
    
    total_entries = 0
    total_completed = 0
    total_challenge_days = 0
    habit_stats = []
    
    for habit in habits:
        # Pass the global challenge start date to each habit
        stats = get_habit_stats(habit, global_challenge_start_date)
        habit_stats.append({
            'habit': habit,
            'stats': stats
        })
        total_entries += stats['tracked_total']
        total_completed += stats['challenge_completed']
        total_challenge_days += stats['challenge_days']
    
    # Sort habits by completion rate
    habit_stats.sort(key=lambda x: x['stats']['challenge_percent'], reverse=True)
    
    # Overall rate based on challenge days (total possible), not just tracked days
    overall_rate = round((total_completed / total_challenge_days * 100), 1) if total_challenge_days > 0 else 0.0
    
    # Get new metrics
    perfect_days = get_perfect_days(user_id)
    almost_perfect_days = get_almost_perfect_days(user_id)
    days_active = get_days_active(user_id)
    
    return {
        'overall_completion_rate': overall_rate,
        'total_completed': total_completed,
        'total_possible': total_challenge_days,  # Use challenge days, not tracked entries
        'best_habit': habit_stats[0] if habit_stats else None,
        'worst_habit': habit_stats[-1] if habit_stats else None,
        'habit_stats': habit_stats,
        'perfect_days': perfect_days,
        'almost_perfect_days': almost_perfect_days,
        'days_active': days_active
    }


def get_date_range_for_challenge(start_date, days=21):
    """Get list of dates for the challenge period."""
    dates = []
    for i in range(days):
        dates.append(start_date + timedelta(days=i))
    return dates

def get_week_day_stats(habits):
    """Calculate which day of the week has best completion rate.
    
    For each unique date across all habits, calculates what percentage of habits
    were completed on that date.
    """
    if not habits:
        return {}
    
    num_habits = len(habits)
    
    # Get all unique dates that have entries
    all_dates = set()
    for habit in habits:
        for entry in habit.entries:
            all_dates.add(entry.date)
    
    # Group dates by day of week
    day_stats = defaultdict(lambda: {'completed': 0, 'possible': 0})
    
    for date in all_dates:
        day_name = date.strftime('%A')
        
        # For this date, count how many habits were completed
        completed_count = 0
        for habit in habits:
            # Check if this habit has an entry for this date and it's completed
            for entry in habit.entries:
                if entry.date == date and entry.completed:
                    completed_count += 1
                    break
        
        day_stats[day_name]['completed'] += completed_count
        day_stats[day_name]['possible'] += num_habits
    
    # Calculate percentages
    day_percentages = {}
    for day, stats in day_stats.items():
        if stats['possible'] > 0:
            day_percentages[day] = round((stats['completed'] / stats['possible']) * 100, 1)
        else:
            day_percentages[day] = 0.0
    
    return day_percentages


def get_achievement_tooltip(achievement_key, definition, progress=None):
    """Generate a detailed tooltip for an achievement that explains what it means."""
    name = definition['name']
    desc = definition['description']
    category = definition['category']
    
    # Create detailed explanations
    tooltips = {
        # Milestones
        'first_habit': 'Your journey begins! This unlocks when you mark your very first habit as complete on any day.',
        'day_1': 'Track at least one habit on your first day. This shows you\'ve started building your routine.',
        'perfect_day_1': 'Complete all 6 habits on the same day. This is your first perfect day - every habit done!',
        'habits_5': 'Mark any 5 habits as complete (across any days). Small steps add up!',
        'habits_10': 'Complete 10 habits total. You\'re building momentum!',
        'day_3': 'Be active for 3 different days (doesn\'t need to be consecutive). Consistency is forming!',
        'habits_25': 'Reach 25 total completed habits. You\'re getting serious about your goals!',
        'week_1': 'Track habits on 7 different days. You\'ve been active for a full week!',
        'habits_50': 'Hit 50 total habit completions. Halfway to 100!',
        'perfect_days_5': 'Achieve 5 days where you complete all 6 habits. Excellence is becoming a habit!',
        'day_14': 'Be active for 14 different days. Two weeks of staying engaged!',
        'habits_75': 'Complete 75 habits in total. You\'re a habit-building machine!',
        'perfect_days_10': 'Reach 10 perfect days (all 6 habits completed). Consistency meets excellence!',
        'habits_100': 'Complete 100 habits! A major milestone showing dedication.',
        'day_21': 'Be active for all 21 days of the challenge. You made it through the entire journey!',
        'perfect_days_15': '15 perfect days achieved. You\'re mastering your routine!',
        'habits_126': 'Complete all 126 possible habits (6 habits × 21 days). Absolute perfection!',
        'perfect_days_21': 'All 21 days perfect! Every single habit done every single day. Ultimate achievement!',
        
        # Streaks
        'streak_2': 'Complete at least one habit for 2 days in a row (streak of consecutive days).',
        'streak_3': 'Build a 3-day streak - 3 consecutive days with at least one completed habit.',
        'streak_5': 'Maintain a 5-day streak. Consistency is building!',
        'streak_7': 'A full week of consecutive days! 7 days in a row with completed habits.',
        'streak_10': '10 days in a row! Your longest ever streak hits double digits.',
        'streak_14': '14 consecutive days - two full weeks! Your commitment is showing.',
        'streak_21': '21 days in a row - the full challenge as a perfect streak!',
        'current_streak_3': 'Your current active streak is 3 days. Keep it going!',
        'current_streak_5': 'Currently on a 5-day streak. Don\'t break it now!',
        'current_streak_7': 'A week-long active streak! You\'re on fire right now.',
        'current_streak_10': '10 days and counting! Your current streak is impressive.',
        'current_streak_14': 'Two weeks of current streak! Momentum is strong.',
        'current_streak_21': '21-day active streak! You\'re currently perfect.',
        'all_habits_streak_3': 'Every single one of your habits has at least a 3-day streak. All cylinders firing!',
        'all_habits_streak_7': 'All 6 habits with 7+ day streaks each. Complete synchronization!',
        
        # Excellence
        'completion_50': 'Your overall success rate reaches 50% - half of all possible habits completed since you started.',
        'completion_75': '75% overall success rate. You\'re hitting three-quarters of your daily goals!',
        'completion_90': '90% success rate! Nearly perfect across all your tracked days.',
        'completion_100': '100% success rate - every single habit you could have done, you did!',
        'best_habit_100': 'One of your habits has 100% success rate - you\'ve never missed it since tracking started!',
        'all_habits_50': 'Every single habit is above 50% success rate. No weak spots in your routine!',
        'all_habits_75': 'All habits above 75% - your entire routine is strong!',
        'almost_perfect_5': '5 days where you completed 5 out of 6 habits. So close to perfect!',
        'almost_perfect_10': '10 almost-perfect days (5/6 habits). Consistent excellence!',
        'high_performer': '15 total days of either perfect (6/6) or almost perfect (5/6). You\'re crushing it!',
        
        # Recovery
        'comeback_kid': 'You came back after missing a day. Setbacks don\'t stop you!',
        'persistent': 'Active for 7+ days but with breaks in between. You keep coming back!',
        'resilient': 'Reached 14 active days despite not having a 14-day streak. You recover from setbacks!',
        'phoenix': 'Built a 5-day streak after breaking a previous streak. Rising from the ashes!',
        'determined': 'Hit 50% success rate even without many perfect days. Steady wins the race!',
        'grinder': '21 active days but fewer than 10 were perfect. You grind through the tough days!',
        'never_quit': '21 days active but not all consecutive. You never gave up despite interruptions!',
    }
    
    tooltip = tooltips.get(achievement_key, desc)
    
    # Add progress info if provided
    if progress and progress['target'] > 1:
        tooltip += f" (Progress: {progress['current']}/{progress['target']})"
    
    return f"{definition['emoji']} {name} - {tooltip}"


# ==================== Achievement System ====================

# Define all 50 achievements with categories, emojis, and unlock criteria
ACHIEVEMENT_DEFINITIONS = {
    # ===== MILESTONES (18 achievements) =====
    'first_habit': {
        'category': 'Milestones',
        'name': 'First Steps',
        'description': 'Complete your first habit',
        'emoji': '🎯',
        'check': lambda stats: stats['total_completed'] >= 1
    },
    'day_1': {
        'category': 'Milestones',
        'name': 'Day 1 Complete',
        'description': 'Finish your first day',
        'emoji': '🌱',
        'check': lambda stats: stats['days_active'] >= 1
    },
    'perfect_day_1': {
        'category': 'Milestones',
        'name': 'First Perfect Day',
        'description': 'Complete all 6 habits in one day',
        'emoji': '⭐',
        'check': lambda stats: stats['perfect_days'] >= 1
    },
    'habits_5': {
        'category': 'Milestones',
        'name': '5 Habits',
        'description': 'Complete 5 total habits',
        'emoji': '🔥',
        'check': lambda stats: stats['total_completed'] >= 5
    },
    'habits_10': {
        'category': 'Milestones',
        'name': '10 Habits',
        'description': 'Complete 10 total habits',
        'emoji': '💪',
        'check': lambda stats: stats['total_completed'] >= 10
    },
    'day_3': {
        'category': 'Milestones',
        'name': '3-Day Warrior',
        'description': 'Stay active for 3 days',
        'emoji': '🏃',
        'check': lambda stats: stats['days_active'] >= 3
    },
    'habits_25': {
        'category': 'Milestones',
        'name': 'Quarter Century',
        'description': 'Complete 25 total habits',
        'emoji': '🎖️',
        'check': lambda stats: stats['total_completed'] >= 25
    },
    'week_1': {
        'category': 'Milestones',
        'name': 'One Week Strong',
        'description': 'Stay active for 7 days',
        'emoji': '📅',
        'check': lambda stats: stats['days_active'] >= 7
    },
    'habits_50': {
        'category': 'Milestones',
        'name': 'Half Hundred',
        'description': 'Complete 50 total habits',
        'emoji': '🏆',
        'check': lambda stats: stats['total_completed'] >= 50
    },
    'perfect_days_5': {
        'category': 'Milestones',
        'name': '5 Perfect Days',
        'description': 'Achieve 5 perfect days',
        'emoji': '🌟',
        'check': lambda stats: stats['perfect_days'] >= 5
    },
    'day_14': {
        'category': 'Milestones',
        'name': 'Two Week Titan',
        'description': 'Stay active for 14 days',
        'emoji': '🦸',
        'check': lambda stats: stats['days_active'] >= 14
    },
    'habits_75': {
        'category': 'Milestones',
        'name': '75 Habits',
        'description': 'Complete 75 total habits',
        'emoji': '💎',
        'check': lambda stats: stats['total_completed'] >= 75
    },
    'perfect_days_10': {
        'category': 'Milestones',
        'name': '10 Perfect Days',
        'description': 'Achieve 10 perfect days',
        'emoji': '✨',
        'check': lambda stats: stats['perfect_days'] >= 10
    },
    'habits_100': {
        'category': 'Milestones',
        'name': 'Centurion',
        'description': 'Complete 100 total habits',
        'emoji': '👑',
        'check': lambda stats: stats['total_completed'] >= 100
    },
    'day_21': {
        'category': 'Milestones',
        'name': '21-Day Champion',
        'description': 'Complete the full 21-day challenge',
        'emoji': '🎉',
        'check': lambda stats: stats['days_active'] >= 21
    },
    'perfect_days_15': {
        'category': 'Milestones',
        'name': '15 Perfect Days',
        'description': 'Achieve 15 perfect days',
        'emoji': '🌈',
        'check': lambda stats: stats['perfect_days'] >= 15
    },
    'habits_126': {
        'category': 'Milestones',
        'name': 'Perfect Challenge',
        'description': 'Complete all 126 possible habits (6 × 21)',
        'emoji': '🏅',
        'check': lambda stats: stats['total_completed'] >= 126
    },
    'perfect_days_21': {
        'category': 'Milestones',
        'name': 'Perfection Personified',
        'description': 'Achieve 21 perfect days',
        'emoji': '🔱',
        'check': lambda stats: stats['perfect_days'] >= 21
    },
    
    # ===== STREAKS (15 achievements) =====
    'streak_2': {
        'category': 'Streaks',
        'name': 'Streak Starter',
        'description': 'Maintain a 2-day streak',
        'emoji': '🔗',
        'check': lambda stats: stats['max_streak'] >= 2
    },
    'streak_3': {
        'category': 'Streaks',
        'name': '3-Day Streak',
        'description': 'Maintain a 3-day streak',
        'emoji': '⚡',
        'check': lambda stats: stats['max_streak'] >= 3
    },
    'streak_5': {
        'category': 'Streaks',
        'name': '5-Day Streak',
        'description': 'Maintain a 5-day streak',
        'emoji': '🔥',
        'check': lambda stats: stats['max_streak'] >= 5
    },
    'streak_7': {
        'category': 'Streaks',
        'name': 'Week Warrior',
        'description': 'Maintain a 7-day streak',
        'emoji': '⚔️',
        'check': lambda stats: stats['max_streak'] >= 7
    },
    'streak_10': {
        'category': 'Streaks',
        'name': '10-Day Streak',
        'description': 'Maintain a 10-day streak',
        'emoji': '💫',
        'check': lambda stats: stats['max_streak'] >= 10
    },
    'streak_14': {
        'category': 'Streaks',
        'name': 'Fortnight Force',
        'description': 'Maintain a 14-day streak',
        'emoji': '🌠',
        'check': lambda stats: stats['max_streak'] >= 14
    },
    'streak_21': {
        'category': 'Streaks',
        'name': 'Unstoppable',
        'description': 'Maintain a 21-day streak',
        'emoji': '🚀',
        'check': lambda stats: stats['max_streak'] >= 21
    },
    'current_streak_3': {
        'category': 'Streaks',
        'name': 'On Fire',
        'description': 'Current streak of 3 days',
        'emoji': '🌶️',
        'check': lambda stats: stats['current_streak'] >= 3
    },
    'current_streak_5': {
        'category': 'Streaks',
        'name': 'Blazing Trail',
        'description': 'Current streak of 5 days',
        'emoji': '🔥',
        'check': lambda stats: stats['current_streak'] >= 5
    },
    'current_streak_7': {
        'category': 'Streaks',
        'name': 'Hot Streak',
        'description': 'Current streak of 7 days',
        'emoji': '🌋',
        'check': lambda stats: stats['current_streak'] >= 7
    },
    'current_streak_10': {
        'category': 'Streaks',
        'name': 'Inferno',
        'description': 'Current streak of 10 days',
        'emoji': '🔆',
        'check': lambda stats: stats['current_streak'] >= 10
    },
    'current_streak_14': {
        'category': 'Streaks',
        'name': 'Burning Bright',
        'description': 'Current streak of 14 days',
        'emoji': '☀️',
        'check': lambda stats: stats['current_streak'] >= 14
    },
    'current_streak_21': {
        'category': 'Streaks',
        'name': 'Eternal Flame',
        'description': 'Current streak of 21 days',
        'emoji': '🌞',
        'check': lambda stats: stats['current_streak'] >= 21
    },
    'all_habits_streak_3': {
        'category': 'Streaks',
        'name': 'Triple Threat',
        'description': 'All habits with 3-day streaks',
        'emoji': '🎯',
        'check': lambda stats: stats['min_habit_streak'] >= 3
    },
    'all_habits_streak_7': {
        'category': 'Streaks',
        'name': 'Synchronized Success',
        'description': 'All habits with 7-day streaks',
        'emoji': '🎼',
        'check': lambda stats: stats['min_habit_streak'] >= 7
    },
    
    # ===== EXCELLENCE (10 achievements) =====
    'completion_50': {
        'category': 'Excellence',
        'name': 'Halfway There',
        'description': 'Reach 50% overall success rate',
        'emoji': '🎯',
        'check': lambda stats: stats['overall_completion'] >= 50.0
    },
    'completion_75': {
        'category': 'Excellence',
        'name': 'Excellence',
        'description': 'Reach 75% overall success rate',
        'emoji': '🌟',
        'check': lambda stats: stats['overall_completion'] >= 75.0
    },
    'completion_90': {
        'category': 'Excellence',
        'name': 'Near Perfect',
        'description': 'Reach 90% overall success rate',
        'emoji': '💯',
        'check': lambda stats: stats['overall_completion'] >= 90.0
    },
    'completion_100': {
        'category': 'Excellence',
        'name': 'Perfection',
        'description': 'Reach 100% overall success rate',
        'emoji': '👑',
        'check': lambda stats: stats['overall_completion'] >= 100.0
    },
    'best_habit_100': {
        'category': 'Excellence',
        'name': 'Master of One',
        'description': 'One habit at 100% success rate',
        'emoji': '🏆',
        'check': lambda stats: stats['best_habit_completion'] >= 100.0
    },
    'all_habits_50': {
        'category': 'Excellence',
        'name': 'Balanced Effort',
        'description': 'All habits above 50%',
        'emoji': '⚖️',
        'check': lambda stats: stats['worst_habit_completion'] >= 50.0
    },
    'all_habits_75': {
        'category': 'Excellence',
        'name': 'Well Rounded',
        'description': 'All habits above 75%',
        'emoji': '🎯',
        'check': lambda stats: stats['worst_habit_completion'] >= 75.0
    },
    'almost_perfect_5': {
        'category': 'Excellence',
        'name': 'Close Calls',
        'description': '5 almost perfect days (5/6 habits)',
        'emoji': '🎲',
        'check': lambda stats: stats['almost_perfect_days'] >= 5
    },
    'almost_perfect_10': {
        'category': 'Excellence',
        'name': 'Consistently Great',
        'description': '10 almost perfect days',
        'emoji': '🎪',
        'check': lambda stats: stats['almost_perfect_days'] >= 10
    },
    'high_performer': {
        'category': 'Excellence',
        'name': 'High Performer',
        'description': '15 perfect + almost perfect days combined',
        'emoji': '🌠',
        'check': lambda stats: (stats['perfect_days'] + stats['almost_perfect_days']) >= 15
    },
    
    # ===== RECOVERY (7 achievements) =====
    'comeback_kid': {
        'category': 'Recovery',
        'name': 'Comeback Kid',
        'description': 'Return after missing a day',
        'emoji': '🔄',
        'check': lambda stats: stats['days_active'] >= 3 and stats['total_completed'] >= 7
    },
    'persistent': {
        'category': 'Recovery',
        'name': 'Persistent',
        'description': 'Stay active for 7 days with gaps',
        'emoji': '🧗',
        'check': lambda stats: stats['days_active'] >= 7 and stats['current_streak'] < 7
    },
    'resilient': {
        'category': 'Recovery',
        'name': 'Resilient',
        'description': 'Reach 14 active days despite setbacks',
        'emoji': '🛡️',
        'check': lambda stats: stats['days_active'] >= 14 and stats['current_streak'] < 14
    },
    'phoenix': {
        'category': 'Recovery',
        'name': 'Phoenix Rising',
        'description': 'Build a 5-day streak after breaking one',
        'emoji': '🦅',
        'check': lambda stats: stats['current_streak'] >= 5 and stats['max_streak'] > stats['current_streak']
    },
    'determined': {
        'category': 'Recovery',
        'name': 'Determined',
        'description': 'Reach 50% success rate despite imperfect days',
        'emoji': '💪',
        'check': lambda stats: stats['overall_completion'] >= 50.0 and stats['perfect_days'] < (stats['days_active'] // 2)
    },
    'grinder': {
        'category': 'Recovery',
        'name': 'The Grinder',
        'description': 'Complete 21 days with less than 10 perfect days',
        'emoji': '⚙️',
        'check': lambda stats: stats['days_active'] >= 21 and stats['perfect_days'] < 10
    },
    'never_quit': {
        'category': 'Recovery',
        'name': 'Never Quit',
        'description': 'Stay active through 21 days with gaps',
        'emoji': '🏃',
        'check': lambda stats: stats['days_active'] >= 21 and stats['current_streak'] < 21
    }
}


def get_achievement_stats(user_id):
    """Calculate all stats needed for achievement checking."""
    from app.models import Habit, HabitEntry, Achievement
    
    habits = Habit.query.filter_by(user_id=user_id).all()
    
    if not habits:
        return None
    
    # Get overall stats
    overall_stats = get_overall_stats(habits, user_id)
    
    # Calculate max streak across all habits
    max_streak = 0
    current_streak = 0
    min_habit_streak = float('inf')
    best_habit_completion = 0.0
    worst_habit_completion = 100.0
    
    for habit in habits:
        habit_stats = get_habit_stats(habit)
        max_streak = max(max_streak, habit_stats['longest_streak'])
        current_streak = max(current_streak, habit_stats['current_streak'])
        min_habit_streak = min(min_habit_streak, habit_stats['current_streak'])
        best_habit_completion = max(best_habit_completion, habit_stats['challenge_percent'])
        worst_habit_completion = min(worst_habit_completion, habit_stats['challenge_percent'])
    
    if min_habit_streak == float('inf'):
        min_habit_streak = 0
    
    return {
        'total_completed': overall_stats['total_completed'],
        'days_active': overall_stats['days_active'],
        'perfect_days': overall_stats['perfect_days'],
        'almost_perfect_days': overall_stats['almost_perfect_days'],
        'max_streak': max_streak,
        'current_streak': current_streak,
        'min_habit_streak': min_habit_streak,
        'overall_completion': overall_stats['overall_completion_rate'],
        'best_habit_completion': best_habit_completion,
        'worst_habit_completion': worst_habit_completion
    }


def get_achievement_unlock_date(user_id, achievement_key):
    """Determine the actual date when an achievement was earned based on habit entries."""
    from app.models import Habit, HabitEntry
    from datetime import datetime
    
    # Get all habits and entries for the user
    habits = Habit.query.filter_by(user_id=user_id).all()
    if not habits:
        return datetime.now()
    
    # Get all entries sorted by date
    all_entries = []
    for habit in habits:
        all_entries.extend(habit.entries)
    
    if not all_entries:
        return datetime.now()
    
    all_entries.sort(key=lambda x: x.date)
    
    # For different achievement types, determine the unlock date differently
    definition = ACHIEVEMENT_DEFINITIONS.get(achievement_key)
    if not definition:
        return datetime.now()
    
    # Check achievements day by day to find when it was first unlocked
    unique_dates = sorted(set(entry.date for entry in all_entries))
    
    for date in unique_dates:
        # Calculate stats up to this date
        stats = get_achievement_stats_up_to_date(user_id, date)
        if stats and definition['check'](stats):
            # Convert date to datetime (end of day)
            return datetime.combine(date, datetime.max.time())
    
    # If we can't determine, use current time
    return datetime.now()


def get_achievement_stats_up_to_date(user_id, end_date):
    """Calculate achievement stats up to a specific date (inclusive)."""
    from app.models import Habit, HabitEntry
    
    habits = Habit.query.filter_by(user_id=user_id).all()
    if not habits:
        return None
    
    # Filter entries up to end_date
    filtered_habits = []
    for habit in habits:
        filtered_entries = [e for e in habit.entries if e.date <= end_date]
        if filtered_entries:
            # Create a temporary habit object with filtered entries
            class TempHabit:
                def __init__(self, habit, entries):
                    self.id = habit.id
                    self.user_id = habit.user_id
                    self.name = habit.name
                    self.order = habit.order
                    self.created_at = habit.created_at
                    self.entries = entries
            
            filtered_habits.append(TempHabit(habit, filtered_entries))
    
    if not filtered_habits:
        return None
    
    # Calculate stats for this date range
    # Get overall stats
    total_completed = sum(len([e for e in h.entries if e.completed]) for h in filtered_habits)
    
    # Get perfect and almost perfect days up to this date
    dates_dict = defaultdict(lambda: {'completed': 0, 'total': 0})
    for habit in filtered_habits:
        for entry in habit.entries:
            dates_dict[entry.date]['total'] += 1
            if entry.completed:
                dates_dict[entry.date]['completed'] += 1
    
    perfect_days = sum(1 for d in dates_dict.values() if d['completed'] == 6 and d['total'] == 6)
    almost_perfect_days = sum(1 for d in dates_dict.values() if d['completed'] == 5 and d['total'] >= 5)
    days_active = len(dates_dict)
    
    # Calculate total possible entries up to this date
    if filtered_habits:
        earliest_start = min(h.created_at.date() for h in filtered_habits)
        days_since_start = (end_date - earliest_start).days + 1
        total_possible = len(filtered_habits) * days_since_start
        overall_completion = round((total_completed / total_possible) * 100, 1) if total_possible > 0 else 0.0
    else:
        overall_completion = 0.0
    
    # Calculate streaks
    max_streak = 0
    current_streak = 0
    min_habit_streak = float('inf')
    best_habit_completion = 0.0
    worst_habit_completion = 100.0
    
    for habit in filtered_habits:
        habit_stats = calculate_habit_stats_for_entries(habit.entries, end_date)
        max_streak = max(max_streak, habit_stats['longest_streak'])
        current_streak = max(current_streak, habit_stats['current_streak'])
        min_habit_streak = min(min_habit_streak, habit_stats['current_streak'])
        best_habit_completion = max(best_habit_completion, habit_stats['success_rate'])
        worst_habit_completion = min(worst_habit_completion, habit_stats['success_rate'])
    
    if min_habit_streak == float('inf'):
        min_habit_streak = 0
    
    return {
        'total_completed': total_completed,
        'days_active': days_active,
        'perfect_days': perfect_days,
        'almost_perfect_days': almost_perfect_days,
        'max_streak': max_streak,
        'current_streak': current_streak,
        'min_habit_streak': min_habit_streak,
        'overall_completion': overall_completion,
        'best_habit_completion': best_habit_completion,
        'worst_habit_completion': worst_habit_completion
    }


def calculate_habit_stats_for_entries(entries, end_date):
    """Calculate habit stats for a set of entries up to a specific date."""
    if not entries:
        return {
            'longest_streak': 0,
            'current_streak': 0,
            'success_rate': 0.0
        }
    
    # Sort entries
    sorted_entries = sorted(entries, key=lambda x: x.date)
    
    # Calculate longest streak
    max_streak = 0
    temp_streak = 0
    prev_date = None
    
    for entry in sorted_entries:
        if entry.completed:
            if prev_date is None or (entry.date - prev_date).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1
            max_streak = max(max_streak, temp_streak)
            prev_date = entry.date
        else:
            temp_streak = 0
            prev_date = entry.date
    
    # Calculate current streak (counting backwards from day before end_date)
    # Today should never affect the streak - always start from yesterday
    current_streak = 0
    expected_date = end_date - timedelta(days=1)
    sorted_entries_desc = sorted(entries, key=lambda x: x.date, reverse=True)
    
    for entry in sorted_entries_desc:
        if entry.date == expected_date and entry.completed:
            current_streak += 1
            expected_date = expected_date - timedelta(days=1)
        elif entry.date < expected_date:
            break
    
    # Calculate success rate
    completed = sum(1 for e in entries if e.completed)
    success_rate = round((completed / len(entries)) * 100, 1) if entries else 0.0
    
    return {
        'longest_streak': max_streak,
        'current_streak': current_streak,
        'success_rate': success_rate
    }


def check_achievements(user_id):
    """Check and unlock new achievements for a user. Returns list of newly unlocked achievement keys."""
    from app.models import Achievement
    
    stats = get_achievement_stats(user_id)
    if not stats:
        return []
    
    # Get already unlocked achievements
    unlocked_keys = set(
        a.achievement_key for a in Achievement.query.filter_by(user_id=user_id).all()
    )
    
    # Check all achievements
    newly_unlocked = []
    for key, definition in ACHIEVEMENT_DEFINITIONS.items():
        if key not in unlocked_keys:
            try:
                if definition['check'](stats):
                    # Determine the actual unlock date
                    unlock_date = get_achievement_unlock_date(user_id, key)
                    
                    # Unlock achievement
                    new_achievement = Achievement(
                        user_id=user_id,
                        achievement_key=key,
                        unlocked_at=unlock_date,
                        viewed=False
                    )
                    db.session.add(new_achievement)
                    newly_unlocked.append({
                        'key': key,
                        'name': definition['name'],
                        'description': definition['description'],
                        'emoji': definition['emoji'],
                        'category': definition['category']
                    })
            except Exception as e:
                # Skip achievements that fail to check
                print(f"Error checking achievement {key}: {e}")
                continue
    
    if newly_unlocked:
        db.session.commit()
    
    return newly_unlocked


def get_unlocked_achievements(user_id, category=None):
    """Get all unlocked achievements for a user, optionally filtered by category."""
    from app.models import Achievement
    
    query = Achievement.query.filter_by(user_id=user_id)
    unlocked = query.all()
    
    result = []
    for achievement in unlocked:
        definition = ACHIEVEMENT_DEFINITIONS.get(achievement.achievement_key)
        if definition and (category is None or definition['category'] == category):
            result.append({
                'key': achievement.achievement_key,
                'name': definition['name'],
                'description': definition['description'],
                'emoji': definition['emoji'],
                'category': definition['category'],
                'unlocked_at': achievement.unlocked_at,
                'viewed': achievement.viewed,
                'definition': definition  # Include for tooltip generation
            })
    
    # Sort by unlock date (newest first)
    result.sort(key=lambda x: x['unlocked_at'], reverse=True)
    
    return result


def get_locked_with_progress(user_id, category=None):
    """Get locked achievements with progress information."""
    from app.models import Achievement
    
    stats = get_achievement_stats(user_id)
    if not stats:
        return []
    
    # Get already unlocked achievement keys
    unlocked_keys = set(
        a.achievement_key for a in Achievement.query.filter_by(user_id=user_id).all()
    )
    
    result = []
    for key, definition in ACHIEVEMENT_DEFINITIONS.items():
        if key in unlocked_keys:
            continue
        
        if category and definition['category'] != category:
            continue
        
        # Calculate progress for this achievement
        progress = calculate_achievement_progress(key, definition, stats)
        
        result.append({
            'key': key,
            'name': definition['name'],
            'description': definition['description'],
            'emoji': definition['emoji'],
            'category': definition['category'],
            'progress': progress,
            'definition': definition  # Include for tooltip generation
        })
    
    # Sort by progress (highest first) then by name
    result.sort(key=lambda x: (-x['progress']['percent'], x['name']))
    
    return result


def calculate_achievement_progress(key, definition, stats):
    """Calculate progress toward an achievement."""
    # Extract the target value from achievement key or description
    # This is a simplified version - you could make this more sophisticated
    
    # Check for specific patterns first (most specific to least specific)
    if key.startswith('all_habits_streak_'):
        target = int(key.split('_')[3])
        current = stats.get('all_habits_streak', 0)
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif key.startswith('all_habits_'):
        target = int(key.split('_')[2])
        current = stats.get('overall_completion', 0)
        return {
            'current': round(current, 1),
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif key.startswith('habits_') and key.split('_')[1].isdigit():
        target = int(key.split('_')[1])
        current = stats['total_completed']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif 'current_streak_' in key:
        target = int(key.split('_')[2])
        current = stats['current_streak']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif 'perfect_days_' in key:
        target = int(key.split('_')[2])
        current = stats['perfect_days']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif 'almost_perfect_' in key:
        target = int(key.split('_')[2])
        current = stats['almost_perfect_days']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif 'streak_' in key and 'current' not in key and 'all' not in key:
        target = int(key.split('_')[1])
        current = stats['max_streak']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif key.startswith('day_') and key.split('_')[1].isdigit():
        target = int(key.split('_')[1])
        current = stats['days_active']
        return {
            'current': current,
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    elif 'completion_' in key:
        target = float(key.split('_')[1])
        current = stats['overall_completion']
        return {
            'current': round(current, 1),
            'target': target,
            'percent': min(100, round((current / target) * 100, 1))
        }
    else:
        # For complex achievements, just return 0 or 100
        try:
            is_unlocked = definition['check'](stats)
            return {
                'current': 1 if is_unlocked else 0,
                'target': 1,
                'percent': 100 if is_unlocked else 0
            }
        except:
            return {
                'current': 0,
                'target': 1,
                'percent': 0
            }


def run_retroactive_achievements(user_id):
    """Run achievement check for existing user data (used in migration)."""
    return check_achievements(user_id)
