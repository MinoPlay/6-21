"""
Migration script to fix achievement unlock dates.
This recalculates the correct unlock dates for all existing achievements.
"""
from app import create_app, db
from app.models import User, Achievement
from app.utils import get_achievement_unlock_date, ACHIEVEMENT_DEFINITIONS
from datetime import datetime

def fix_achievement_dates():
    """Recalculate and update unlock dates for all achievements."""
    app = create_app()
    
    with app.app_context():
        print("Starting achievement date fix...")
        
        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users")
        
        for user in users:
            print(f"\nProcessing user: {user.username} (ID: {user.id})")
            
            # Get all achievements for this user
            achievements = Achievement.query.filter_by(user_id=user.id).all()
            print(f"  Found {len(achievements)} achievements")
            
            for achievement in achievements:
                old_date = achievement.unlocked_at
                
                # Recalculate the correct unlock date
                new_date = get_achievement_unlock_date(user.id, achievement.achievement_key)
                
                # Get achievement name for display
                definition = ACHIEVEMENT_DEFINITIONS.get(achievement.achievement_key, {})
                name = definition.get('name', achievement.achievement_key)
                
                if old_date.date() != new_date.date():
                    print(f"  ✓ {name}:")
                    print(f"    Old: {old_date.strftime('%Y-%m-%d')}")
                    print(f"    New: {new_date.strftime('%Y-%m-%d')}")
                    achievement.unlocked_at = new_date
                else:
                    print(f"  - {name}: {old_date.strftime('%Y-%m-%d')} (no change)")
        
        # Commit all changes
        db.session.commit()
        print("\n✓ All achievement dates have been updated!")
        print("Changes saved to database.")

if __name__ == '__main__':
    fix_achievement_dates()
