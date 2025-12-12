"""
Migration script to add 'notified' column to Achievement table.
This sets existing achievements to notified=True to avoid re-showing old notifications.
"""

from app import create_app, db
from app.models import Achievement
from sqlalchemy import text

def migrate():
    app = create_app()
    
    with app.app_context():
        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('achievement')]
        
        if 'notified' in columns:
            print("Column 'notified' already exists.")
            return
        
        print("Adding 'notified' column to Achievement table...")
        
        # Add the column with default value False
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE achievement ADD COLUMN notified BOOLEAN DEFAULT 0'))
            conn.commit()
        
        print("Column added successfully.")
        
        # Set all existing achievements to notified=True to avoid re-showing
        print("Marking all existing achievements as notified...")
        Achievement.query.update({'notified': True})
        db.session.commit()
        
        count = Achievement.query.count()
        print(f"Updated {count} achievement(s) to notified=True")
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
