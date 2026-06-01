from app import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    amenities = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(256), nullable=True, default='default_room.jpg')
    availability = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservations = db.relationship('Reservation', backref='room', lazy=True)

    def get_amenities_list(self):
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []

    def is_available_for_dates(self, check_in, check_out, exclude_reservation_id=None):
        from app.models.reservation import Reservation
        query = Reservation.query.filter(
            Reservation.room_id == self.id,
            Reservation.status.in_(['confirmed', 'pending']),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in
        )
        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)
        return query.count() == 0

    def __repr__(self):
        return f'<Room {self.room_number} - {self.room_name}>'
