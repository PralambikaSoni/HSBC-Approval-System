from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from . import notifications_bp
from ..models import Notification
from ..extensions import db

@notifications_bp.route('/unread', methods=['GET'])
@login_required
def get_unread():
    notifs = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'link': n.link,
        'created_at': n.created_at.isoformat()
    } for n in notifs])

@notifications_bp.route('/mark-read', methods=['POST'])
@login_required
def mark_read():
    data = request.get_json() or {}
    notif_id = data.get('notification_id')
    
    if notif_id:
        n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
        if n:
            n.is_read = True
            db.session.commit()
    else:
        # Mark all as read
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
            
    return jsonify({'success': True})
