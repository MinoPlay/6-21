from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from datetime import datetime, timedelta
from app import db
from app.models import Habit, HabitEntry
from app.utils import get_habit_stats, get_overall_stats, get_date_range_for_challenge, get_week_day_stats
import json
import io

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Daily habit tracking view."""
    habits = Habit.query.order_by(Habit.order).all()
    
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
def setup():
    """Initial habit setup form."""
    if request.method == 'POST':
        # Delete existing habits if any
        Habit.query.delete()
        HabitEntry.query.delete()
        
        # Create 6 new habits
        for i in range(1, 7):
            habit_name = request.form.get(f'habit_{i}')
            if habit_name and habit_name.strip():
                habit = Habit(name=habit_name.strip(), order=i)
                db.session.add(habit)
        
        db.session.commit()
        return redirect(url_for('main.index'))
    
    # Check if habits already exist
    existing_habits = Habit.query.order_by(Habit.order).all()
    
    return render_template('setup.html', existing_habits=existing_habits)

@bp.route('/api/toggle', methods=['POST'])
def toggle_entry():
    """Toggle habit completion for a specific date."""
    data = request.get_json()
    habit_id = data.get('habit_id')
    date_str = data.get('date')
    
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
    
    return jsonify({
        'success': True,
        'completed': entry.completed,
        'habit_id': habit_id,
        'date': date_str
    })

@bp.route('/stats')
def stats():
    """Statistics dashboard."""
    habits = Habit.query.order_by(Habit.order).all()
    
    if not habits:
        return redirect(url_for('main.setup'))
    
    overall_stats = get_overall_stats(habits)
    week_day_stats = get_week_day_stats(habits)
    
    return render_template('stats.html', 
                         overall_stats=overall_stats,
                         week_day_stats=week_day_stats)

@bp.route('/calendar')
def calendar():
    """21-day calendar overview."""
    habits = Habit.query.order_by(Habit.order).all()
    
    if not habits:
        return redirect(url_for('main.setup'))
    
    # Get the start date (first entry or 21 days ago)
    first_entry = HabitEntry.query.order_by(HabitEntry.date).first()
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
def export_data():
    """Export all habit data as JSON."""
    habits = Habit.query.order_by(Habit.order).all()
    
    export_data = {
        'export_date': datetime.now().isoformat(),
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
    
    filename = f'habit_tracker_export_{datetime.now().strftime("%Y%m%d")}.json'
    
    return send_file(
        json_bytes,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/import', methods=['POST'])
def import_data():
    """Import habit data from JSON file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.json'):
        return jsonify({'error': 'File must be a JSON file'}), 400
    
    try:
        # Parse JSON data
        data = json.load(file)
        
        # Validate structure
        if 'habits' not in data:
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Clear existing data
        HabitEntry.query.delete()
        Habit.query.delete()
        db.session.commit()
        
        # Import habits and entries
        habit_id_map = {}  # Map old IDs to new IDs
        
        for habit_data in data['habits']:
            # Create new habit
            habit = Habit(
                name=habit_data['name'],
                order=habit_data['order']
            )
            db.session.add(habit)
            db.session.flush()  # Get the new ID
            
            habit_id_map[habit_data['id']] = habit.id
            
            # Import entries for this habit
            if 'entries' in habit_data:
                for entry_data in habit_data['entries']:
                    entry_date = datetime.strptime(entry_data['date'], '%Y-%m-%d').date()
                    entry = HabitEntry(
                        habit_id=habit.id,
                        date=entry_date,
                        completed=entry_data['completed']
                    )
                    db.session.add(entry)
        
        db.session.commit()
        
        return redirect(url_for('main.index'))
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON file'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/reset', methods=['POST'])
def reset_challenge():
    """Reset and start a new 21-day challenge."""
    # Delete all entries but keep habits
    HabitEntry.query.delete()
    db.session.commit()
    
    return redirect(url_for('main.index'))

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
