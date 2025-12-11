from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, session
from datetime import datetime, timedelta
from functools import wraps
from app import db
from app.models import Habit, HabitEntry, User, Achievement
from app.utils import get_habit_stats, get_overall_stats, get_date_range_for_challenge, get_week_day_stats, check_achievements
import json
import io
import re

bp = Blueprint('main', __name__)

# ==================== User Session Management ====================

def get_current_user():
    """Get the current user from session or None."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def user_required(f):
    """Decorator to require user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.user_select'))
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            return redirect(url_for('main.user_select'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/user/select', methods=['GET', 'POST'])
def user_select():
    """User selection or creation page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        
        # Validate username
        if not username:
            return render_template('user_select.html', 
                                 error='Username cannot be empty',
                                 users=User.query.all())
        
        # Validate length (2-20 chars)
        if len(username) < 2 or len(username) > 20:
            return render_template('user_select.html', 
                                 error='Username must be 2-20 characters',
                                 users=User.query.all())
        
        # Validate characters (alphanumeric, spaces, hyphens only)
        if not re.match(r'^[a-zA-Z0-9 -]+$', username):
            return render_template('user_select.html', 
                                 error='Username can only contain letters, numbers, spaces, and hyphens',
                                 users=User.query.all())
        
        # Check if user exists (case-insensitive)
        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        
        if not user:
            # Create new user
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        return redirect(url_for('main.index'))
    
    # GET request - show user selection page
    users = User.query.order_by(User.created_at).all()
    return render_template('user_select.html', users=users)

@bp.route('/api/user/current')
def user_current():
    """Get current user info."""
    user = get_current_user()
    if not user:
        return jsonify({'username': None})
    
    # Get unviewed achievement count
    unviewed_count = Achievement.query.filter_by(
        user_id=user.id,
        viewed=False
    ).count()
    
    return jsonify({
        'username': user.username,
        'unviewed_achievements': unviewed_count
    })

@bp.route('/api/user/switch', methods=['POST'])
def user_switch():
    """Switch to a different user."""
    data = request.get_json()
    user_id = data.get('user_id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    session['user_id'] = user.id
    return jsonify({'success': True, 'username': user.username})

@bp.route('/api/user/list')
def user_list():
    """Get list of all users."""
    users = User.query.order_by(User.created_at).all()
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'created_at': u.created_at.isoformat()
        } for u in users]
    })

@bp.route('/api/user/delete', methods=['POST'])
@user_required
def user_delete():
    """Delete current user and all their data."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'No user logged in'}), 401
    
    # Delete user (cascades to habits, entries, achievements)
    db.session.delete(user)
    db.session.commit()
    
    # Clear session
    session.pop('user_id', None)
    
    return jsonify({'success': True})

# ==================== Achievement Management ====================

@bp.route('/api/achievements/new')
@user_required
def achievements_new():
    """Get list of new (unviewed) achievements."""
    from app.utils import ACHIEVEMENT_DEFINITIONS
    
    user = get_current_user()
    new_achievements = Achievement.query.filter_by(
        user_id=user.id,
        viewed=False
    ).order_by(Achievement.unlocked_at.desc()).all()
    
    return jsonify({
        'achievements': [{
            'key': a.achievement_key,
            'name': ACHIEVEMENT_DEFINITIONS.get(a.achievement_key, {}).get('name', 'Achievement'),
            'description': ACHIEVEMENT_DEFINITIONS.get(a.achievement_key, {}).get('description', ''),
            'emoji': ACHIEVEMENT_DEFINITIONS.get(a.achievement_key, {}).get('emoji', '🏆'),
            'unlocked_at': a.unlocked_at.isoformat()
        } for a in new_achievements]
    })

@bp.route('/api/achievements/mark-viewed', methods=['POST'])
@user_required
def achievements_mark_viewed():
    """Mark achievements as viewed."""
    user = get_current_user()
    data = request.get_json()
    achievement_keys = data.get('achievement_keys', [])
    
    Achievement.query.filter(
        Achievement.user_id == user.id,
        Achievement.achievement_key.in_(achievement_keys)
    ).update({'viewed': True}, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== Main Application Routes ====================

@bp.route('/')
@user_required
def index():
    """Daily habit tracking view."""
    user = get_current_user()
    habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.order).all()
    
    # If no habits exist, redirect to setup
    if not habits:
        return redirect(url_for('main.setup'))
    
    # Get date from query parameter or use today
    date_str = request.args.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.now().date()
    else:
        current_date = datetime.now().date()
    
    # Get or create entries for this date
    entries = {}
    for habit in habits:
        entry = HabitEntry.query.filter_by(habit_id=habit.id, date=current_date).first()
        if not entry:
            entry = HabitEntry(habit_id=habit.id, date=current_date, completed=False)
        entries[habit.id] = entry
    
    # Calculate navigation dates
    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)
    today = datetime.now().date()
    
    return render_template('index.html', 
                         habits=habits, 
                         entries=entries, 
                         current_date=current_date,
                         prev_date=prev_date,
                         next_date=next_date,
                         today=today)

@bp.route('/setup', methods=['GET', 'POST'])
@user_required
def setup():
    """Initial habit setup form."""
    user = get_current_user()
    
    if request.method == 'POST':
        # Delete existing habits if any (cascades to entries)
        Habit.query.filter_by(user_id=user.id).delete()
        
        # Create 6 new habits
        for i in range(1, 7):
            habit_name = request.form.get(f'habit_{i}')
            if habit_name and habit_name.strip():
                habit = Habit(name=habit_name.strip(), order=i, user_id=user.id)
                db.session.add(habit)
        
        db.session.commit()
        return redirect(url_for('main.index'))
    
    # Check if habits already exist
    existing_habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.order).all()
    
    return render_template('setup.html', existing_habits=existing_habits, user=user)

@bp.route('/api/toggle', methods=['POST'])
@user_required
def toggle_entry():
    """Toggle habit completion for a specific date."""
    user = get_current_user()
    data = request.get_json()
    habit_id = data.get('habit_id')
    date_str = data.get('date')
    
    # Verify habit belongs to current user
    habit = Habit.query.filter_by(id=habit_id, user_id=user.id).first()
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get or create entry
    entry = HabitEntry.query.filter_by(habit_id=habit_id, date=date_obj).first()
    
    if not entry:
        entry = HabitEntry(habit_id=habit_id, date=date_obj, completed=True)
        db.session.add(entry)
    else:
        entry.completed = not entry.completed
    
    db.session.commit()
    
    # Check for new achievements
    new_achievements = check_achievements(user.id)
    
    return jsonify({
        'success': True,
        'completed': entry.completed,
        'habit_id': habit_id,
        'date': date_str,
        'new_achievements': new_achievements
    })

@bp.route('/stats')
@user_required
def stats():
    """Statistics dashboard."""
    from .utils import get_unlocked_achievements, get_locked_with_progress, get_achievement_tooltip
    
    user = get_current_user()
    habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.order).all()
    
    if not habits:
        return redirect(url_for('main.setup'))
    
    overall_stats = get_overall_stats(habits, user.id)
    week_day_stats = get_week_day_stats(habits)
    
    return render_template('stats.html', 
                         overall_stats=overall_stats,
                         week_day_stats=week_day_stats,
                         current_user=user,
                         get_unlocked_achievements=get_unlocked_achievements,
                         get_locked_with_progress=get_locked_with_progress,
                         get_achievement_tooltip=get_achievement_tooltip)

@bp.route('/calendar')
@user_required
def calendar():
    """21-day calendar overview."""
    user = get_current_user()
    habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.order).all()
    
    if not habits:
        return redirect(url_for('main.setup'))
    
    # Get the start date (first entry or 21 days ago)
    first_entry = HabitEntry.query.join(Habit).filter(
        Habit.user_id == user.id
    ).order_by(HabitEntry.date).first()
    
    if first_entry:
        start_date = first_entry.date
    else:
        start_date = datetime.now().date() - timedelta(days=20)
    
    # Generate 21-day range
    dates = get_date_range_for_challenge(start_date, 21)
    
    # Build calendar data structure
    calendar_data = []
    for habit in habits:
        habit_row = {
            'habit': habit,
            'entries': {}
        }
        
        for date in dates:
            entry = HabitEntry.query.filter_by(habit_id=habit.id, date=date).first()
            habit_row['entries'][date.isoformat()] = entry.completed if entry else False
        
        calendar_data.append(habit_row)
    
    return render_template('calendar.html', 
                         calendar_data=calendar_data, 
                         dates=dates,
                         today=datetime.now().date())

@bp.route('/export')
@user_required
def export_data():
    """Export all habit data as JSON."""
    user = get_current_user()
    habits = Habit.query.filter_by(user_id=user.id).order_by(Habit.order).all()
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'username': user.username,
        'habits': []
    }
    
    for habit in habits:
        habit_data = {
            'id': habit.id,
            'name': habit.name,
            'order': habit.order,
            'created_at': habit.created_at.isoformat(),
            'stats': get_habit_stats(habit),
            'entries': []
        }
        
        for entry in sorted(habit.entries, key=lambda x: x.date):
            habit_data['entries'].append({
                'date': entry.date.isoformat(),
                'completed': entry.completed
            })
        
        export_data['habits'].append(habit_data)
    
    # Create JSON file in memory
    json_str = json.dumps(export_data, indent=2)
    json_bytes = io.BytesIO(json_str.encode('utf-8'))
    
    filename = f'habit_tracker_{user.username}_{datetime.now().strftime("%Y%m%d")}.json'
    
    return send_file(
        json_bytes,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


@bp.route('/import', methods=['POST'])
@user_required
def import_data():
    """Import habit data from JSON file (not implemented for multi-user)."""
    # Import functionality removed for multi-user version
    # Users start fresh - no import needed
    return jsonify({'error': 'Import not available'}), 400

@bp.route('/reset', methods=['POST'])
@user_required
def reset_challenge():
    """Reset and start a new 21-day challenge."""
    user = get_current_user()
    
    # Delete all entries for this user's habits
    HabitEntry.query.filter(
        HabitEntry.habit_id.in_(
            db.session.query(Habit.id).filter_by(user_id=user.id)
        )
    ).delete(synchronize_session=False)
    
    db.session.commit()
    
    return redirect(url_for('main.index'))

# ==================== PWA Routes ====================

@bp.route('/manifest.json')
def manifest():
    """Serve PWA manifest."""
    return jsonify({
        'name': '21-Day Habit Tracker',
        'short_name': 'Habits',
        'description': 'Track 6 habits for 21 days',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#4CAF50',
        'icons': [
            {
                'src': '/static/icons/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png'
            },
            {
                'src': '/static/icons/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png'
            }
        ]
    })

@bp.route('/sw.js')
def service_worker():
    """Serve service worker."""
    return send_file('static/service-worker.js', mimetype='application/javascript')

