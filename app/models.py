from datetime import datetime
from app import db

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    entries = db.relationship('HabitEntry', backref='habit', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('habit_id', 'date', name='_habit_date_uc'),)
    
    def __repr__(self):
        return f'<HabitEntry habit_id={self.habit_id} date={self.date} completed={self.completed}>'
