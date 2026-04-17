from datetime import datetime, timezone
from flask import current_app
from ..extensions import db, scheduler
from ..models import Request, RequestApprover, User, SnoozeLog, AuditLog
from ..notifications.helpers import send_notification
from sqlalchemy import or_

def get_escalation_target(current_role, department):
    """Finds the next highest role in the same department, or a director."""
    hierarchy = {'employee': 0, 'team_lead': 1, 'manager': 2, 'director': 3}
    curr_level = hierarchy.get(current_role, 0)
    
    if curr_level >= 3:
        return None # Cannot escalate director
        
    next_role = None
    if curr_level == 0:
        next_role = 'team_lead'
    elif curr_level == 1:
        next_role = 'manager'
    elif curr_level == 2:
        next_role = 'director'
        
    # Try finding someone in same dept with next role
    targets = User.query.filter_by(department=department, role=next_role, is_active=True).all()
    if targets:
        return targets[0] # Pick the first available
        
    # If no one found in dept with next role, escalate straight to any director
    directors = User.query.filter_by(role='director', is_active=True).all()
    if directors:
        return directors[0]
        
    return None

def check_escalations():
    """Scheduled job to check for overdue pending requests."""
    # We must use app context because apscheduler runs in background thread
    with scheduler.app.app_context():
        now = datetime.now(timezone.utc)
        
        # Get all completely pending requests
        from ..models import Approval
        all_active = RequestApprover.query.join(Request).filter(Request.status == 'pending').all()
        
        pending_approver_records = []
        for ra in all_active:
             if not Approval.query.filter_by(request_id=ra.request_id, approver_id=ra.approver_id).first():
                 pending_approver_records.append(ra)
        
        for ra in pending_approver_records:
            req = ra.request
            approver = ra.approver
            
            # 1. Check if director (never escalates)
            if approver.role == 'director':
                continue
                
            # 2. Check if snoozed
            # Note: A real app would check if snoozed_until > now, then calculate the new deadline.
            # For simplicity per SRS, if there's an active snooze that hasn't expired, we skip checking it entirely.
            snooze = SnoozeLog.query.filter_by(request_id=req.id, approver_id=approver.id).order_by(SnoozeLog.id.desc()).first()
            if snooze and snooze.wake_at:
                snoozed_until_utc = snooze.wake_at.replace(tzinfo=timezone.utc) if snooze.wake_at.tzinfo is None else snooze.wake_at
                if snoozed_until_utc > now:
                    continue # Currently actively snoozed
            
            # 3. Check elapsed time
            created_at_utc = ra.assigned_at.replace(tzinfo=timezone.utc) if ra.assigned_at and ra.assigned_at.tzinfo is None else (ra.assigned_at or now)
            hours_elapsed = (now - created_at_utc).total_seconds() / 3600
            
            escalation_hours = current_app.config.get('ESCALATION_THRESHOLDS', {}).get(req.priority, 24)
            
            if hours_elapsed > escalation_hours:
                # Target missed! ESCALATE!
                target = get_escalation_target(approver.role, approver.department)
                if not target:
                    continue # No one to escalate to
                    
                # Mark old assignment as escalated
                approval = Approval(request_id=req.id, approver_id=approver.id, action='escalated', comment='AUTO-ESCALATED')
                db.session.add(approval)
                
                # Create new assignment if they aren't already an approver
                existing_ra = RequestApprover.query.filter_by(request_id=req.id, approver_id=target.id).first()
                if not existing_ra:
                    new_ra = RequestApprover(
                        request_id=req.id, 
                        approver_id=target.id,
                        note_to_approver=f"AUTO-ESCALATED: Original approver {approver.full_name} failed to respond in {escalation_hours}h."
                    )
                    db.session.add(new_ra)
                
                # Audit log
                audit = AuditLog(
                    action_type='ESCALATION',
                    actor_id=1, # System process ID / ideally we have a system user, but 1 usually works
                    target_type='request',
                    target_id=req.id,
                    comment=f"Escalated from {approver.employee_id} to {target.employee_id}"
                )
                db.session.add(audit)
                
                # Notifications
                send_notification(approver.id, f"You failed to approve {req.request_code} in time. It was escalated.", request_id=req.id)
                send_notification(target.id, f"ESCALATION: You have a new urgent request {req.request_code}.", request_id=req.id)
                
                db.session.commit()
