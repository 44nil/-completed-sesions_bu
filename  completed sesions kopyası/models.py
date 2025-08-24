from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()

ALLOWED_STATUSES = ('active', 'canceled', 'moved', 'attended', 'no_show')

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ... diğer alanlar ...

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    capacity = db.Column(db.Integer)
    notes = db.Column(db.Text)
    is_recurring = db.Column(db.Boolean, default=False)
    # ... diğer alanlar ...

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    user_name = db.Column(db.String(128))
    status = db.Column(Enum(*ALLOWED_STATUSES, name='reservation_status'), default='active', nullable=False)
    # ... diğer alanlar ...

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128))
    # ... diğer alanlar ...

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ... diğer alanlar ...
