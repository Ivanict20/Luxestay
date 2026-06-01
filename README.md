# LuxeStay Hotel Reservation System

A full-featured, production-ready hotel reservation system built with Flask, SQLite, and a refined luxury hotel aesthetic.

---

## Features

### Admin System
- Secure admin login with session management
- Full room management (add, edit, delete, image upload)
- Real-time reservation dashboard with stats
- View, confirm, cancel, edit, and delete reservations
- Filter reservations by status (pending/confirmed/cancelled)
- Search reservations by guest name, email, or phone
- Notification bell showing pending bookings (auto-refreshes)
- Prevent double-booking with date conflict validation

### Customer System
- Customer registration and login
- Browse and filter available rooms (by type, price range)
- Detailed room pages with images and amenities
- Booking form with real-time availability check and price calculator
- View and manage personal reservations only (secure access control)
- Edit or cancel reservations
- Printable booking receipt with booking reference

### Technical
- Flask + SQLite (upgradeable to MySQL)
- Password hashing with bcrypt
- CSRF protection on all forms
- Role-based access control (admin / customer)
- Image upload with secure filenames
- Responsive on desktop and mobile

---

## Quick Start

### 1. Install Python dependencies

```bash
cd luxestay
pip install -r requirements.txt
```

### 2. Run the application

```bash
python run.py
```

Visit: http://localhost:5000

### 3. Default Admin Login

- **Email:** admin@luxestay.com  
- **Password:** admin123

---

## Folder Structure

```
luxestay/
├── run.py                    # Entry point
├── config.py                 # Configuration
├── requirements.txt
├── README.md
├── instance/
│   └── luxestay.db           # SQLite database (auto-created)
└── app/
    ├── __init__.py           # App factory + seed data
    ├── models/
    │   ├── user.py
    │   ├── room.py
    │   └── reservation.py
    ├── routes/
    │   ├── auth.py
    │   ├── admin.py
    │   ├── customer.py
    │   └── main.py
    ├── static/
    │   ├── css/style.css
    │   ├── js/main.js
    │   └── uploads/rooms/    # Room images stored here
    └── templates/
        ├── base.html
        ├── auth/
        │   ├── login.html
        │   └── register.html
        ├── admin/
        │   ├── base_admin.html
        │   ├── dashboard.html
        │   ├── rooms.html
        │   ├── room_form.html
        │   ├── reservations.html
        │   ├── reservation_detail.html
        │   └── edit_reservation.html
        └── customer/
            ├── base_customer.html
            ├── dashboard.html
            ├── rooms.html
            ├── room_detail.html
            ├── book_room.html
            ├── confirmation.html
            ├── my_reservations.html
            ├── reservation_detail.html
            └── edit_reservation.html
```

---

## Database Tables

| Table | Key Fields |
|-------|-----------|
| users | id, fullname, email, password (hashed), role |
| rooms | id, room_number, room_name, room_type, price, image, availability |
| reservations | id, user_id, room_id, check_in, check_out, status, guests |

---

## Environment Variables (Optional)

Set these for email notifications:

```
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## Upgrading to MySQL

In `config.py`, change:
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/luxestay'
```

Then: `pip install pymysql`

---

## Security

- All passwords hashed with bcrypt
- CSRF tokens on every form
- SQL injection protected via SQLAlchemy ORM
- Session-based authentication
- Role-based access: admin routes protected, customer data isolated
- Customers can only view/edit their own reservations
