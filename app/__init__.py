from flask import Flask, url_for as flask_url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    # Add cache busting for static files
    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)
    
    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, 'static', filename)
                if os.path.isfile(file_path):
                    values['v'] = int(os.stat(file_path).st_mtime)
        return flask_url_for(endpoint, **values)
    
    from app import routes, models
    app.register_blueprint(routes.bp)
    
    with app.app_context():
        db.create_all()
        
        # Run retroactive achievement migration
        migration_flag = os.path.join(os.path.dirname(__file__), '..', '.achievements_migrated')
        if not os.path.exists(migration_flag):
            try:
                from app.models import User
                from app.utils import run_retroactive_achievements
                
                users = User.query.all()
                for user in users:
                    print(f"Running retroactive achievements for user: {user.username}")
                    newly_unlocked = run_retroactive_achievements(user.id)
                    print(f"  Unlocked {len(newly_unlocked)} achievements")
                
                # Create flag file to prevent re-running
                with open(migration_flag, 'w') as f:
                    f.write('Migration completed')
                print("Achievement migration completed successfully!")
            except Exception as e:
                print(f"Achievement migration error (safe to ignore on fresh install): {e}")
    
    return app
