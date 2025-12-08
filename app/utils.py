from datetime import datetime, timedelta
from collections import defaultdict
from app.models import HabitEntry

def calculate_current_streak(habit_entries):
    """Calculate current streak counting backwards from today."""
    if not habit_entries:
        return 0
    
    # Sort entries by date descending
    sorted_entries = sorted(habit_entries, key=lambda x: x.date, reverse=True)
    
    streak = 0
    expected_date = datetime.now().date()
    
    for entry in sorted_entries:
        if entry.date == expected_date and entry.completed:
            streak += 1
            expected_date -= timedelta(days=1)
        elif entry.date < expected_date:
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

def calculate_completion_rate(habit_entries, total_days=21):
    """Calculate completion percentage."""
    if not habit_entries:
        return 0.0
    
    completed = sum(1 for entry in habit_entries if entry.completed)
    total = len(habit_entries)
    
    if total == 0:
        return 0.0
    
    return round((completed / total) * 100, 1)

def get_habit_stats(habit):
    """Get comprehensive statistics for a habit."""
    entries = habit.entries
    
    return {
        'current_streak': calculate_current_streak(entries),
        'longest_streak': calculate_longest_streak(entries),
        'completion_rate': calculate_completion_rate(entries),
        'total_completed': sum(1 for e in entries if e.completed),
        'total_days': len(entries)
    }

def get_overall_stats(habits):
    """Get overall statistics across all habits."""
    total_entries = 0
    total_completed = 0
    habit_stats = []
    
    for habit in habits:
        stats = get_habit_stats(habit)
        habit_stats.append({
            'habit': habit,
            'stats': stats
        })
        total_entries += stats['total_days']
        total_completed += stats['total_completed']
    
    # Sort habits by completion rate
    habit_stats.sort(key=lambda x: x['stats']['completion_rate'], reverse=True)
    
    overall_rate = round((total_completed / total_entries * 100), 1) if total_entries > 0 else 0.0
    
    return {
        'overall_completion_rate': overall_rate,
        'total_completed': total_completed,
        'total_possible': total_entries,
        'best_habit': habit_stats[0] if habit_stats else None,
        'worst_habit': habit_stats[-1] if habit_stats else None,
        'habit_stats': habit_stats
    }

def get_date_range_for_challenge(start_date, days=21):
    """Get list of dates for the challenge period."""
    dates = []
    for i in range(days):
        dates.append(start_date + timedelta(days=i))
    return dates

def get_week_day_stats(habits):
    """Calculate which day of the week has best completion rate."""
    day_counts = defaultdict(lambda: {'completed': 0, 'total': 0})
    
    for habit in habits:
        for entry in habit.entries:
            day_name = entry.date.strftime('%A')
            day_counts[day_name]['total'] += 1
            if entry.completed:
                day_counts[day_name]['completed'] += 1
    
    # Calculate percentages
    day_percentages = {}
    for day, counts in day_counts.items():
        if counts['total'] > 0:
            day_percentages[day] = round((counts['completed'] / counts['total']) * 100, 1)
        else:
            day_percentages[day] = 0.0
    
    return day_percentages
