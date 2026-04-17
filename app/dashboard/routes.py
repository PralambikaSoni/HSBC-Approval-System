from flask import render_template
from flask_login import login_required, current_user
from ..models import Request, RequestApprover, User
from . import dashboard_bp
from sqlalchemy import func

@dashboard_bp.route('/')
@login_required
def index():
    context = {}
    
    # Base: Employee Stats
    my_reqs = Request.query.filter_by(requester_id=current_user.id).all()
    context['my_total'] = len(my_reqs)
    context['my_pending'] = len([r for r in my_reqs if r.status == 'pending'])
    context['my_recent'] = Request.query.filter_by(requester_id=current_user.id).order_by(Request.submitted_at.desc()).limit(5).all()
    
    # Approver Stats
    if current_user.role in ['team_lead', 'manager', 'director']:
        from ..models import Approval
        all_my_assignments = RequestApprover.query.filter_by(approver_id=current_user.id).join(Request).filter(Request.status == 'pending').all()
        pending_assignments = []
        for ra in all_my_assignments:
            if not Approval.query.filter_by(request_id=ra.request_id, approver_id=current_user.id).first():
                pending_assignments.append(ra)
                
        context['action_required_count'] = len(pending_assignments)
        context['recent_queue'] = pending_assignments[:5]
        
        # Approval history (requests acted upon recently)
        recent_approvals = Approval.query.filter_by(approver_id=current_user.id).order_by(Approval.acted_at.desc()).limit(5).all()
        context['recent_approvals'] = recent_approvals
        
    # Director System Stats
    if current_user.role == 'director':
        context['sys_total'] = Request.query.count()
        context['sys_pending'] = Request.query.filter_by(status='pending').count()
        context['sys_users'] = User.query.count()
        context['sys_escalated'] = Request.query.filter_by(status='escalated').count()
        
    return render_template('dashboard/index.html', **context)
