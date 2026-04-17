from app import create_app
from app.extensions import db
from app.models import Request, RequestApprover, User

app = create_app()
with app.app_context():
    reqs = Request.query.order_by(Request.id.desc()).limit(3).all()
    print("--- LATEST REQUESTS ---")
    for r in reqs:
        print(f"Req ID: {r.id} Code: {r.request_code} Status: {r.status} Requester: {r.requester.full_name}")
        for ra in r.approvers:
            print(f"  - Assigned Approver: {ra.approver.full_name} (Role: {ra.approver.role}) ID: {ra.approver_id}")
        
        # Check approvals
        from app.models import Approval
        apps = Approval.query.filter_by(request_id=r.id).all()
        for a in apps:
            print(f"  - Action taken by {a.approver_id}: {a.action}")
