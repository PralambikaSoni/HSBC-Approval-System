from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import uuid

from . import admin_bp
from .forms import UserCreateForm, UserEditForm
from ..models import User, AuditLog, Request
from ..extensions import db, bcrypt
from ..decorators import role_required

def log_audit(action, target_type, target_id, old_state=None, new_state=None, comment=None):
    log = AuditLog(
        action_type=action,
        actor_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        old_state=old_state,
        new_state=new_state,
        comment=comment,
        ip_address=request.remote_addr
    )
    db.session.add(log)

@admin_bp.before_request
@login_required
@role_required('director')
def restrict_admin():
    pass

@admin_bp.route('/all-requests')
def all_requests():
    reqs = Request.query.order_by(Request.submitted_at.desc()).all()
    return render_template('admin/all_requests.html', requests=reqs)

@admin_bp.route('/users')
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            employee_id=form.employee_id.data,
            full_name=form.full_name.data,
            department=form.department.data,
            role=form.role.data,
            password_hash=hashed_pw,
            force_pw_reset=form.force_pw_reset.data,
            created_by=current_user.id
        )
        db.session.add(user)
        db.session.flush() # To get user.id
        
        log_audit('USER_CREATED', 'user', user.id, new_state=f"{user.employee_id} - {user.role}")
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin_bp.list_users'))
    return render_template('admin/user_form.html', form=form, title="Create User")

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        old_role = user.role
        
        user.full_name = form.full_name.data
        user.department = form.department.data
        user.role = form.role.data
        
        if old_role != user.role:
            log_audit('USER_ROLE_CHANGED', 'user', user.id, old_state=old_role, new_state=user.role)
            
        log_audit('USER_EDITED', 'user', user.id)
        db.session.commit()
        
        flash(f'User {user.employee_id} updated successfully!', 'success')
        return redirect(url_for('admin_bp.list_users'))
        
    return render_template('admin/user_form.html', form=form, title="Edit User", user=user)

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
def toggle_active(user_id):
    if user_id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for('admin_bp.list_users'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    action = 'USER_DEACTIVATED' if not user.is_active else 'USER_REACTIVATED'
    log_audit(action, 'user', user.id, new_state=str(user.is_active))
    db.session.commit()
    
    status_str = "deactivated" if not user.is_active else "reactivated"
    flash(f'User {user.employee_id} has been {status_str}.', 'info')
    return redirect(url_for('admin_bp.list_users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    # Generate a temporary random password
    temp_pw = str(uuid.uuid4())[:8]
    user.password_hash = bcrypt.generate_password_hash(temp_pw).decode('utf-8')
    user.force_pw_reset = True
    
    log_audit('PASSWORD_RESET', 'user', user.id)
    db.session.commit()
    
    flash(f'Password reset for {user.employee_id}. Temporary password is: {temp_pw}', 'warning')
    return redirect(url_for('admin_bp.list_users'))

@admin_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.failed_logins = 0
    user.locked_until = None
    
    log_audit('ACCOUNT_UNLOCKED', 'user', user.id)
    db.session.commit()
    
    flash(f'{user.employee_id} has been manually unlocked.', 'success')
    return redirect(url_for('admin_bp.list_users'))

@admin_bp.route('/audit-logs')
def audit_logs():
    # Adding basic filtering as per SRS section 8.9
    query = AuditLog.query
    
    target_type = request.args.get('target_type')
    action = request.args.get('action')
    actor_id = request.args.get('actor_id')
    
    if target_type:
        query = query.filter_by(target_type=target_type)
    if action:
        query = query.filter_by(action_type=action)
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
        
    logs = query.order_by(AuditLog.logged_at.desc()).limit(200).all()
    # Eager load the actor data manually since we didn't specify relationship in models for AuditLog actor_id
    actors = {u.id: u for u in User.query.filter(User.id.in_([log.actor_id for log in logs])).all()}
    
    return render_template('admin/audit_logs.html', logs=logs, actors=actors)
