from app import db
from datetime import datetime

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    arrival_time = db.Column(db.String(20), nullable=True)
    guests = db.Column(db.Integer, nullable=False, default=1)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def nights(self):
        delta = self.check_out - self.check_in
        return delta.days

    def total_price(self):
        return self.nights() * self.room.price

    def booking_reference(self):
        return f'LUX-{self.id:05d}'

    def __repr__(self):
        return f'<Reservation {self.booking_reference()}>'
