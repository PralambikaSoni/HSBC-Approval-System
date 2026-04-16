from . import auth_bp

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone

from . import auth_bp
from .forms import LoginForm
from ..models import User
from ..extensions import db, bcrypt

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/') 

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(employee_id=form.employee_id.data).first()
        
        if user:
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return render_template('auth/login.html', form=form)

            if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                flash('Account locked due to too many failed attempts. Try again in 15 minutes.', 'danger')
                return render_template('auth/login.html', form=form)

            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                user.failed_logins = 0
                user.locked_until = None
                db.session.commit()
                login_user(user)
                flash('Login successful!', 'success')
                return redirect('/')
            else:
                user.failed_logins += 1
                if user.failed_logins >= 5:
                    from datetime import timedelta
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                db.session.commit()
                flash('Invalid employee ID or password', 'danger')
        else:
            flash('Invalid employee ID or password', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from .forms import ProfileUpdateForm
    form = ProfileUpdateForm()
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.department = form.department.data
        
        if form.password.data:
            current_user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('dashboard_bp.index'))
        
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.department.data = current_user.department
        
    return render_template('auth/profile.html', form=form)
