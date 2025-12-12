from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    entries = db.relationship('HabitEntry', backref='habit', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Habit {self.name} (User {self.user_id})>'

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('habit_id', 'date', name='_habit_date_uc'),)
    
    def __repr__(self):
        return f'<HabitEntry habit_id={self.habit_id} date={self.date} completed={self.completed}>'

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_key = db.Column(db.String(50), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)
    notified = db.Column(db.Boolean, default=False)  # Whether the user has been notified (toast shown)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_key', name='_user_achievement_uc'),)
    
    def __repr__(self):
        return f'<Achievement {self.achievement_key} (User {self.user_id})>'
