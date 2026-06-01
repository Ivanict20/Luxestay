from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app(config=None):
    app = Flask(__name__)
    
    if config is None:
        from config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.customer import customer_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    from app.models.user import User
    from app.models.room import Room
    from app import bcrypt

    # Create admin if not exists
    if not User.query.filter_by(email='admin@luxestay.com').first():
        admin = User(
            fullname='LuxeStay Admin',
            email='admin@luxestay.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)

    # Seed sample rooms
    if Room.query.count() == 0:
        rooms = [
            Room(
                room_number='101',
                room_name='Standard Single',
                room_type='Standard',
                price=2500.00,
                description='A cozy and comfortable standard single room with all essential amenities. Perfect for solo travelers seeking quality and comfort.',
                amenities='Free WiFi, Air Conditioning, Flat-screen TV, Private Bathroom, Daily Housekeeping, Room Service',
                image='standard_single.jpg',
                availability=True
            ),
            Room(
                room_number='201',
                room_name='Deluxe Double',
                room_type='Deluxe',
                price=4500.00,
                description='Spacious deluxe double room with premium furnishings and stunning city views. Ideal for couples or business travelers.',
                amenities='Free WiFi, Air Conditioning, Smart TV, King Bed, Mini Bar, Private Bathroom, Bathtub, Balcony, Room Service, Daily Housekeeping',
                image='deluxe_double.jpg',
                availability=True
            ),
            Room(
                room_number='301',
                room_name='Executive Suite',
                room_type='Suite',
                price=8500.00,
                description='An elegant executive suite offering a separate living area, premium amenities, and breathtaking panoramic views of the city.',
                amenities='Free WiFi, Air Conditioning, Smart TV, King Bed, Living Room, Mini Bar, Jacuzzi, Balcony, Butler Service, Room Service, Daily Housekeeping, Complimentary Breakfast',
                image='executive_suite.jpg',
                availability=True
            ),
            Room(
                room_number='401',
                room_name='Presidential Suite',
                room_type='Presidential',
                price=18000.00,
                description='The pinnacle of luxury — our Presidential Suite features lavish interiors, a private dining area, personal butler, and exclusive access to premium services.',
                amenities='Free WiFi, Air Conditioning, Multiple Smart TVs, Master Bedroom, Private Dining Room, Full Kitchen, Private Pool, Jacuzzi, Butler Service, Limousine Service, VIP Lounge Access, Complimentary Breakfast & Dinner',
                image='presidential_suite.jpg',
                availability=True
            ),
            Room(
                room_number='102',
                room_name='Standard Twin',
                room_type='Standard',
                price=3000.00,
                description='Comfortable standard twin room with two single beds, perfect for friends or colleagues traveling together.',
                amenities='Free WiFi, Air Conditioning, Flat-screen TV, Twin Beds, Private Bathroom, Daily Housekeeping',
                image='standard_single.jpg',
                availability=True
            ),
            Room(
                room_number='202',
                room_name='Deluxe Family Room',
                room_type='Deluxe',
                price=6000.00,
                description='Spacious family room designed for families, with ample space and child-friendly amenities.',
                amenities='Free WiFi, Air Conditioning, Smart TV, King Bed + Sofa Bed, Mini Bar, Family Bathroom, Baby Cot Available, Room Service, Daily Housekeeping',
                image='deluxe_double.jpg',
                availability=True
            ),
        ]
        for room in rooms:
            db.session.add(room)

    db.session.commit()
