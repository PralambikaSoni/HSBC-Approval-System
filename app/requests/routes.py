from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone

from .forms import RequestForm, ResubmitForm
from .helpers import generate_request_code
from ..approvals.forms import ApprovalActionForm, SnoozeForm
from ..models import Request, RequestApprover, RequestVersion, AuditLog
from ..extensions import db
from ..notifications.helpers import send_notification
from . import requests_bp

def log_audit(action, target_type, target_id, comment=None):
    log = AuditLog(
        action_type=action,
        actor_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        comment=comment,
        ip_address=request.remote_addr
    )
    db.session.add(log)

@requests_bp.route('/')
@login_required
def list_requests():
    # Only show requests created by the current user
    reqs = Request.query.filter_by(requester_id=current_user.id).order_by(Request.submitted_at.desc()).all()
    return render_template('requests/list.html', requests=reqs)

@requests_bp.route('/<request_code>')
@login_required
def request_detail(request_code):
    req = Request.query.filter_by(request_code=request_code).first_or_404()
    
    # Check if user is legally allowed to see this request
    # Allowed if: user is requester, or user is an assigned approver, or user is director
    is_requester = req.requester_id == current_user.id
    is_approver = any(a.approver_id == current_user.id for a in req.approvers)
    is_director = current_user.role == 'director'
    
    if not (is_requester or is_approver or is_director):
        from flask import abort
        abort(403)
        
    versions = RequestVersion.query.filter_by(request_id=req.id).order_by(RequestVersion.version_num.asc()).all()
    
    # Passing forms if active approver
    from ..models import Approval
    # Find active assignment
    my_assignment = next((a for a in req.approvers if a.approver_id == current_user.id), None)
    has_acted = Approval.query.filter_by(request_id=req.id, approver_id=current_user.id).first() if my_assignment else None
    active_ra = my_assignment if my_assignment and not has_acted else None
    
    action_form = ApprovalActionForm() if active_ra else None
    snooze_form = SnoozeForm() if active_ra else None
    
    return render_template('requests/detail.html', req=req, versions=versions, active_ra=active_ra, action_form=action_form, snooze_form=snooze_form)

@requests_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_request():
    form = RequestForm()
    
    # Add dynamic categories from config
    form.category.choices = [(c, c) for c in current_app.config['REQUEST_CATEGORIES']]
    
    if request.method == 'POST':
        approver_ids = request.form.getlist('approver_ids')
        
        if not approver_ids:
            flash('You must select at least one approver.', 'danger')
            return render_template('requests/create.html', form=form)
            
        if form.validate_on_submit():
            # Generate code
            req_code = generate_request_code()
            
            # Create request
            new_req = Request(
                request_code=req_code,
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                priority=form.priority.data,
                status='pending', # Directly mapping to pending as per section 5
                requester_id=current_user.id
            )
            db.session.add(new_req)
            db.session.flush() # Get id
            
            # Create RequestApprover rows
            for aid in set(approver_ids):
                note = request.form.get(f'note_{aid}', None)
                ra = RequestApprover(request_id=new_req.id, approver_id=int(aid), note_to_approver=note)
                db.session.add(ra)
                # Send Notification
                send_notification(int(aid), f"New pending request: {req_code}", request_id=new_req.id)
                
            log_audit('REQUEST_CREATED', 'request', new_req.id)
            db.session.commit()
            
            flash(f'Request {req_code} created successfully.', 'success')
            return redirect(url_for('requests_bp.list_requests'))
            
    return render_template('requests/create.html', form=form)
