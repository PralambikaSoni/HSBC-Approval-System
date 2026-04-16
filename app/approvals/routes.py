from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta

from . import approvals_bp
from .forms import ApprovalActionForm, SnoozeForm
from ..models import Request, RequestApprover, RequestVersion, Approval, SnoozeLog, AuditLog
from ..extensions import db
from ..decorators import role_required
from ..notifications.helpers import send_notification

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

@approvals_bp.route('/queue')
@login_required
@role_required('team_lead', 'manager', 'director')
def queue():
    # Show active pending requests where this user is an assigned approver
    all_my_assignments = RequestApprover.query.filter_by(approver_id=current_user.id).join(Request).filter(Request.status == 'pending').order_by(Request.submitted_at.asc()).all()
    approver_records = []
    for ra in all_my_assignments:
        if not Approval.query.filter_by(request_id=ra.request_id, approver_id=current_user.id).first():
            approver_records.append(ra)
    
    return render_template('approvals/queue.html', records=approver_records)

@approvals_bp.route('/<int:request_id>/action', methods=['POST'])
@login_required
@role_required('team_lead', 'manager', 'director')
def take_action(request_id):
    req = Request.query.get_or_404(request_id)
    ra = RequestApprover.query.filter_by(request_id=req.id, approver_id=current_user.id).first_or_404()
    
    has_acted = Approval.query.filter_by(request_id=req.id, approver_id=current_user.id).first()
    if req.status != 'pending' or has_acted:
        flash('This request is no longer pending your approval.', 'warning')
        return redirect(url_for('approvals_bp.queue'))
        
    action_type = request.form.get('action')
    comment = request.form.get('comment', '').strip()
    
    if not action_type or not comment:
        flash('Action and Comment are required.', 'danger')
        return redirect(url_for('requests_bp.request_detail', request_code=req.request_code))
        
    if action_type == 'approve':
        approval = Approval(request_id=req.id, approver_id=current_user.id, action='approved', comment=comment)
        db.session.add(approval)
        db.session.flush() # Force ID constraint to register before query check
        
        # Check if ALL approvers have approved
        all_ras = RequestApprover.query.filter_by(request_id=req.id).all()
        all_approvals = Approval.query.filter_by(request_id=req.id, action='approved').all()
        # Find distinct approvers who approved since it's possible although rare to have duplicates
        approved_approver_ids = set([a.approver_id for a in all_approvals])
        assigned_approver_ids = set([r.approver_id for r in all_ras])
        
        if assigned_approver_ids.issubset(approved_approver_ids) and len(assigned_approver_ids) > 0:
            req.status = 'approved'
            log_audit('REQUEST_APPROVED_FULLY', 'request', req.id)
        send_notification(req.requester_id, f"Your request {req.request_code} was APPROVED.", request_id=req.id)
        db.session.commit()
    
        log_audit('APPROVER_APPROVED', 'request', req.id, comment[:50])
        flash('Request approved!', 'success')
        
    elif action_type == 'reject':
        req.status = 'rejected' # Implicitly fails the whole request
        
        approval = Approval(request_id=req.id, approver_id=current_user.id, action='rejected', comment=comment)
        db.session.add(approval)
        log_audit('REQUEST_REJECTED', 'request', req.id, comment[:50])
        
        send_notification(req.requester_id, f"Your request {req.request_code} was REJECTED.", request_id=req.id)
        flash('Request rejected.', 'danger')
        
    elif action_type == 'request_details':
        approval = Approval(request_id=req.id, approver_id=current_user.id, action='modification_requested', comment=comment)
        db.session.add(approval)
        
        # Save current state as version for tracking changes
        current_version_count = RequestVersion.query.filter_by(request_id=req.id).count()
        rv = RequestVersion(
            request_id=req.id,
            version_num=current_version_count + 1,
            description=req.description,
            change_comment=comment
        )
        db.session.add(rv)
        log_audit('REQUEST_RETURNED_FOR_EDIT', 'request', req.id, comment[:50])
        
        send_notification(req.requester_id, f"{req.request_code} returned for edits.", request_id=req.id)
        flash('Request returned to sender for edits.', 'warning')
        
    db.session.commit()
    return redirect(url_for('approvals_bp.queue'))

@approvals_bp.route('/<int:request_id>/snooze', methods=['POST'])
@login_required
@role_required('team_lead', 'manager', 'director')
def snooze(request_id):
    req = Request.query.get_or_404(request_id)
    ra = RequestApprover.query.filter_by(request_id=req.id, approver_id=current_user.id).first_or_404()
    
    has_acted = Approval.query.filter_by(request_id=req.id, approver_id=current_user.id).first()
    if req.status != 'pending' or has_acted:
        flash('Cannot snooze a request that is not pending.', 'warning')
        return redirect(url_for('requests_bp.request_detail', request_code=req.request_code))
        
    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Snooze reason is required.', 'danger')
        return redirect(url_for('requests_bp.request_detail', request_code=req.request_code))
        
    # Apply snooze 
    hours = current_app.config.get('DEFAULT_SNOOZE_HOURS', 24)
    until_dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    
    previous_snoozes = SnoozeLog.query.filter_by(request_id=req.id, approver_id=current_user.id).count()
    snooze_log = SnoozeLog(
        request_id=req.id,
        approver_id=current_user.id,
        wake_at=until_dt,
        duration_hours=hours,
        snooze_count=previous_snoozes + 1
    )
    db.session.add(snooze_log)
    
    log_audit('REQUEST_SNOOZED', 'request', req.id, reason[:50])
    db.session.commit()
    
    flash(f'Request snoozed for {hours} hours.', 'info')
    return redirect(url_for('approvals_bp.queue'))
