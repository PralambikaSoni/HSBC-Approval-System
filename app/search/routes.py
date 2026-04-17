from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import User

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/approvers', methods=['GET'])
@login_required
def search_approvers():
    name = request.args.get('name', '').strip()
    department = request.args.get('department', '').strip()
    role = request.args.get('role', '').strip()
    emp_id = request.args.get('emp_id', '').strip()
    
    # At least one parameter must be non-empty
    if not any([name, department, role, emp_id]):
        return jsonify([])
        
    # NEVER include the current user, NEVER include deactivated users
    query = User.query.filter(User.is_active == True, User.id != current_user.id)
    
    if name:
        query = query.filter(User.full_name.ilike(f"%{name}%"))
    if department:
        query = query.filter(User.department.ilike(department))
    if role:
        query = query.filter(User.role == role)
    if emp_id:
        query = query.filter(User.employee_id == emp_id)
        
    results = query.limit(20).all()
    
    return jsonify([{
        'id': u.id,
        'employee_id': u.employee_id,
        'full_name': u.full_name,
        'department': u.department,
        'role': u.role
    } for u in results])
