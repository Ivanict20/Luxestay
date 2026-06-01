from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.room import Room
from app.models.reservation import Reservation
from datetime import datetime
import os
import time
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_image(file, room_number):
    """Save uploaded image with a unique timestamped filename. Returns filename or None."""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"room_{secure_filename(str(room_number))}_{int(time.time())}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)
    return unique_name

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total = Reservation.query.count()
    confirmed = Reservation.query.filter_by(status='confirmed').count()
    pending = Reservation.query.filter_by(status='pending').count()
    cancelled = Reservation.query.filter_by(status='cancelled').count()
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(availability=True).count()
    recent_reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
        total=total, confirmed=confirmed, pending=pending,
        cancelled=cancelled, total_rooms=total_rooms,
        available_rooms=available_rooms,
        recent_reservations=recent_reservations)

# ---- ROOMS ----

@admin_bp.route('/rooms')
@login_required
@admin_required
def rooms():
    rooms = Room.query.order_by(Room.room_number).all()
    return render_template('admin/rooms.html', rooms=rooms)

@admin_bp.route('/rooms/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_room():
    if request.method == 'POST':
        room_number = request.form.get('room_number', '').strip()
        room_name   = request.form.get('room_name', '').strip()
        room_type   = request.form.get('room_type', '').strip()
        price       = request.form.get('price', 0)
        description = request.form.get('description', '').strip()
        amenities   = request.form.get('amenities', '').strip()
        availability = request.form.get('availability') == 'on'

        if not all([room_number, room_name, room_type, price]):
            flash('Please fill all required fields.', 'danger')
            return render_template('admin/room_form.html', room=None)

        if Room.query.filter_by(room_number=room_number).first():
            flash('Room number already exists.', 'danger')
            return render_template('admin/room_form.html', room=None)

        # Save uploaded image (timestamped unique filename)
        image_filename = 'default_room.jpg'
        if 'image' in request.files:
            saved = save_uploaded_image(request.files['image'], room_number)
            if saved:
                image_filename = saved

        room = Room(
            room_number=room_number, room_name=room_name, room_type=room_type,
            price=float(price), description=description, amenities=amenities,
            image=image_filename, availability=availability
        )
        db.session.add(room)
        db.session.commit()
        flash(f'Room {room_name} added successfully!', 'success')
        return redirect(url_for('admin.rooms'))

    return render_template('admin/room_form.html', room=None)

@admin_bp.route('/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)

    if request.method == 'POST':
        room.room_name   = request.form.get('room_name', '').strip()
        room.room_type   = request.form.get('room_type', '').strip()
        room.price       = float(request.form.get('price', room.price))
        room.description = request.form.get('description', '').strip()
        room.amenities   = request.form.get('amenities', '').strip()
        room.availability = request.form.get('availability') == 'on'

        # Replace image only when a new file is actually submitted
        if 'image' in request.files:
            saved = save_uploaded_image(request.files['image'], room.room_number)
            if saved:
                # Optionally delete the old file to save disk space
                if room.image and room.image not in ('default_room.jpg',):
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], room.image)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                room.image = saved   # ← update DB column to new filename

        db.session.commit()
        flash(f'Room {room.room_name} updated successfully!', 'success')
        return redirect(url_for('admin.rooms'))

    return render_template('admin/room_form.html', room=room)

@admin_bp.route('/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    active = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.status.in_(['confirmed', 'pending'])
    ).count()
    if active > 0:
        flash('Cannot delete room with active reservations.', 'danger')
        return redirect(url_for('admin.rooms'))
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully.', 'success')
    return redirect(url_for('admin.rooms'))

# ---- RESERVATIONS ----

@admin_bp.route('/reservations')
@login_required
@admin_required
def reservations():
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    
    query = Reservation.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.filter(
            db.or_(
                Reservation.fullname.ilike(f'%{search}%'),
                Reservation.email.ilike(f'%{search}%'),
                Reservation.phone.ilike(f'%{search}%')
            )
        )
    reservations = query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin/reservations.html',
        reservations=reservations, status_filter=status_filter, search=search)

@admin_bp.route('/reservations/<int:res_id>')
@login_required
@admin_required
def reservation_detail(res_id):
    res = Reservation.query.get_or_404(res_id)
    return render_template('admin/reservation_detail.html', res=res)

@admin_bp.route('/reservations/<int:res_id>/confirm', methods=['POST'])
@login_required
@admin_required
def confirm_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    res.status = 'confirmed'
    db.session.commit()
    flash(f'Reservation {res.booking_reference()} confirmed!', 'success')
    return redirect(request.referrer or url_for('admin.reservations'))

@admin_bp.route('/reservations/<int:res_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    res.status = 'cancelled'
    db.session.commit()
    flash(f'Reservation {res.booking_reference()} cancelled.', 'warning')
    return redirect(request.referrer or url_for('admin.reservations'))

@admin_bp.route('/reservations/<int:res_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    db.session.delete(res)
    db.session.commit()
    flash('Reservation deleted.', 'success')
    return redirect(url_for('admin.reservations'))

@admin_bp.route('/reservations/<int:res_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    rooms = Room.query.all()
    if request.method == 'POST':
        res.fullname = request.form.get('fullname', res.fullname)
        res.email = request.form.get('email', res.email)
        res.phone = request.form.get('phone', res.phone)
        res.guests = int(request.form.get('guests', res.guests))
        res.arrival_time = request.form.get('arrival_time', res.arrival_time)
        res.special_requests = request.form.get('special_requests', res.special_requests)
        res.status = request.form.get('status', res.status)

        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        if check_in_str and check_out_str:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            if check_out <= check_in:
                flash('Check-out must be after check-in.', 'danger')
                return render_template('admin/edit_reservation.html', res=res, rooms=rooms)
            if not res.room.is_available_for_dates(check_in, check_out, exclude_reservation_id=res.id):
                flash('Room not available for selected dates.', 'danger')
                return render_template('admin/edit_reservation.html', res=res, rooms=rooms)
            res.check_in = check_in
            res.check_out = check_out

        db.session.commit()
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('admin.reservation_detail', res_id=res.id))

    return render_template('admin/edit_reservation.html', res=res, rooms=rooms)

@admin_bp.route('/api/notifications')
@login_required
@admin_required
def notifications():
    pending = Reservation.query.filter_by(status='pending').order_by(Reservation.created_at.desc()).limit(5).all()
    data = [{
        'id': r.id,
        'ref': r.booking_reference(),
        'name': r.fullname,
        'room': r.room.room_name,
        'created_at': r.created_at.strftime('%b %d, %H:%M')
    } for r in pending]
    return jsonify({'count': len(data), 'notifications': data})
