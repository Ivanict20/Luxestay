from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.room import Room
from app.models.reservation import Reservation
from datetime import datetime, date

customer_bp = Blueprint('customer', __name__)

def customer_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    rooms = Room.query.filter_by(availability=True).all()
    my_reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.created_at.desc()).limit(3).all()
    return render_template('customer/dashboard.html', rooms=rooms, my_reservations=my_reservations)

@customer_bp.route('/rooms')
@login_required
def browse_rooms():
    room_type = request.args.get('type', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    
    query = Room.query
    if room_type:
        query = query.filter_by(room_type=room_type)
    if min_price:
        query = query.filter(Room.price >= float(min_price))
    if max_price:
        query = query.filter(Room.price <= float(max_price))
    
    rooms = query.order_by(Room.price).all()
    room_types = db.session.query(Room.room_type).distinct().all()
    room_types = [r[0] for r in room_types]
    
    return render_template('customer/rooms.html', rooms=rooms, room_types=room_types,
        selected_type=room_type, min_price=min_price, max_price=max_price)

@customer_bp.route('/rooms/<int:room_id>')
@login_required
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('customer/room_detail.html', room=room)

@customer_bp.route('/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)

    if not room.availability:
        flash('This room is not available for booking.', 'danger')
        return redirect(url_for('customer.browse_rooms'))

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        check_in_str = request.form.get('check_in', '')
        check_out_str = request.form.get('check_out', '')
        arrival_time = request.form.get('arrival_time', '')
        guests = int(request.form.get('guests', 1))
        special_requests = request.form.get('special_requests', '').strip()

        if not all([fullname, email, phone, check_in_str, check_out_str]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('customer/book_room.html', room=room)

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('customer/book_room.html', room=room)

        if check_in < date.today():
            flash('Check-in date cannot be in the past.', 'danger')
            return render_template('customer/book_room.html', room=room)

        if check_out <= check_in:
            flash('Check-out date must be after check-in date.', 'danger')
            return render_template('customer/book_room.html', room=room)

        if not room.is_available_for_dates(check_in, check_out):
            flash('Error: Room already booked for selected dates. Please choose different dates.', 'danger')
            return render_template('customer/book_room.html', room=room)

        reservation = Reservation(
            user_id=current_user.id,
            room_id=room.id,
            fullname=fullname,
            email=email,
            phone=phone,
            check_in=check_in,
            check_out=check_out,
            arrival_time=arrival_time,
            guests=guests,
            special_requests=special_requests,
            status='pending'
        )
        db.session.add(reservation)
        db.session.commit()

        flash(f'Booking submitted! Your reference is {reservation.booking_reference()}. We will confirm shortly.', 'success')
        return redirect(url_for('customer.booking_confirmation', res_id=reservation.id))

    return render_template('customer/book_room.html', room=room,
        today=date.today().isoformat(), user=current_user)

@customer_bp.route('/confirmation/<int:res_id>')
@login_required
def booking_confirmation(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.my_reservations'))
    return render_template('customer/confirmation.html', res=res)

@customer_bp.route('/my-reservations')
@login_required
def my_reservations():
    status_filter = request.args.get('status', '')
    query = Reservation.query.filter_by(user_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    reservations = query.order_by(Reservation.created_at.desc()).all()
    return render_template('customer/my_reservations.html',
        reservations=reservations, status_filter=status_filter)

@customer_bp.route('/reservation/<int:res_id>')
@login_required
def reservation_detail(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.my_reservations'))
    return render_template('customer/reservation_detail.html', res=res)

@customer_bp.route('/reservation/<int:res_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.my_reservations'))
    if res.status == 'cancelled':
        flash('Cannot edit a cancelled reservation.', 'danger')
        return redirect(url_for('customer.my_reservations'))

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()
        arrival_time = request.form.get('arrival_time', '')
        guests = int(request.form.get('guests', res.guests))
        special_requests = request.form.get('special_requests', '')

        check_in_str = request.form.get('check_in', '')
        check_out_str = request.form.get('check_out', '')

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid dates.', 'danger')
            return render_template('customer/edit_reservation.html', res=res)

        if check_out <= check_in:
            flash('Check-out must be after check-in.', 'danger')
            return render_template('customer/edit_reservation.html', res=res)

        if not res.room.is_available_for_dates(check_in, check_out, exclude_reservation_id=res.id):
            flash('Room not available for the selected dates.', 'danger')
            return render_template('customer/edit_reservation.html', res=res)

        res.fullname = fullname
        res.phone = phone
        res.arrival_time = arrival_time
        res.guests = guests
        res.special_requests = special_requests
        res.check_in = check_in
        res.check_out = check_out
        res.status = 'pending'  # reset to pending on edit
        db.session.commit()
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('customer.reservation_detail', res_id=res.id))

    return render_template('customer/edit_reservation.html', res=res)

@customer_bp.route('/reservation/<int:res_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer.my_reservations'))
    res.status = 'cancelled'
    db.session.commit()
    flash('Reservation cancelled successfully.', 'warning')
    return redirect(url_for('customer.my_reservations'))

@customer_bp.route('/api/check-availability')
@login_required
def check_availability():
    room_id = request.args.get('room_id')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    exclude_id = request.args.get('exclude_id')
    
    if not all([room_id, check_in, check_out]):
        return jsonify({'available': False, 'message': 'Missing parameters'})
    
    try:
        room = Room.query.get(int(room_id))
        ci = datetime.strptime(check_in, '%Y-%m-%d').date()
        co = datetime.strptime(check_out, '%Y-%m-%d').date()
        exc = int(exclude_id) if exclude_id else None
        available = room.is_available_for_dates(ci, co, exclude_reservation_id=exc)
        return jsonify({'available': available,
            'message': 'Available' if available else 'Room already booked for selected dates.'})
    except Exception as e:
        return jsonify({'available': False, 'message': str(e)})
