from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, relationship
from flask_login import UserMixin
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    employee_id = sa.Column(sa.String(50), unique=True, nullable=False)
    full_name = sa.Column(sa.String(150), nullable=False)
    department = sa.Column(sa.String(100), nullable=False)
    role = sa.Column(
        sa.String(50), 
        sa.CheckConstraint("role IN ('employee','team_lead','manager','director')", name='ck_user_role'), 
        nullable=False
    )
    password_hash = sa.Column(sa.String(255), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)
    force_pw_reset = sa.Column(sa.Boolean, default=False)
    failed_logins = sa.Column(sa.Integer, default=0)
    locked_until = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    created_by = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True)

    # Note: UserMixin provides is_authenticated, is_active, is_anonymous, get_id()
    # We rename the column to shadow is_active but logic still works

class Request(db.Model):
    __tablename__ = 'requests'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    request_code = sa.Column(sa.String(50), unique=True, nullable=False)
    title = sa.Column(sa.String(120), nullable=False)
    description = sa.Column(sa.String(2000), nullable=False)
    category = sa.Column(sa.String(100), nullable=False)
    priority = sa.Column(
        sa.String(20), 
        sa.CheckConstraint("priority IN ('low','medium','high','critical')", name='ck_req_priority'), 
        nullable=False
    )
    status = sa.Column(
        sa.String(50),
        sa.CheckConstraint(
            "status IN ('created','pending','in_review','snoozed','modification_requested','escalated','approved','rejected','closed')",
            name='ck_req_status'
        ),
        nullable=False,
        default='created'
    )
    requester_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    escalation_count = sa.Column(sa.Integer, default=0)
    submitted_at = sa.Column(sa.DateTime, default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    closed_at = sa.Column(sa.DateTime, nullable=True)

    requester = relationship('User', foreign_keys=[requester_id])
    approvers = relationship('RequestApprover', back_populates='request')

class RequestApprover(db.Model):
    __tablename__ = 'request_approvers'
    __table_args__ = (
        sa.UniqueConstraint('request_id', 'approver_id', name='uq_request_approver'),
    )

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    request_id = sa.Column(sa.Integer, sa.ForeignKey('requests.id'), nullable=False)
    approver_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    note_to_approver = sa.Column(sa.Text, nullable=True)
    assigned_at = sa.Column(sa.DateTime, default=sa.func.now())

    request = relationship('Request', back_populates='approvers')
    approver = relationship('User', foreign_keys=[approver_id])

class RequestVersion(db.Model):
    __tablename__ = 'request_versions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    request_id = sa.Column(sa.Integer, sa.ForeignKey('requests.id'), nullable=False)
    version_num = sa.Column(sa.Integer, nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    changed_by = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    change_comment = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())

class Approval(db.Model):
    __tablename__ = 'approvals'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    request_id = sa.Column(sa.Integer, sa.ForeignKey('requests.id'), nullable=False)
    approver_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    action = sa.Column(
        sa.String(50),
        sa.CheckConstraint("action IN ('approved','rejected','modification_requested','escalated','voided')", name='ck_approv_action'),
        nullable=False
    )
    comment = sa.Column(sa.Text, nullable=True)
    acted_at = sa.Column(sa.DateTime, default=sa.func.now())

    request = relationship('Request', foreign_keys=[request_id])

class SnoozeLog(db.Model):
    __tablename__ = 'snooze_log'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    request_id = sa.Column(sa.Integer, sa.ForeignKey('requests.id'), nullable=False)
    approver_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    snooze_count = sa.Column(sa.Integer, nullable=False)
    duration_hours = sa.Column(sa.Integer, nullable=False)
    snoozed_at = sa.Column(sa.DateTime, default=sa.func.now())
    wake_at = sa.Column(sa.DateTime, nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    message = sa.Column(sa.Text, nullable=False)
    request_id = sa.Column(sa.Integer, sa.ForeignKey('requests.id'), nullable=True)
    is_read = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())

    request = relationship('Request', foreign_keys=[request_id])

    @property
    def link(self):
        from flask import url_for
        if self.request_id and self.request:
            try:
                return url_for('requests_bp.request_detail', request_code=self.request.request_code)
            except RuntimeError:
                # Fallback if accessed outside request context (e.g., from Scheduler)
                return f"/requests/{self.request.request_code}"
        return "#"

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    action_type = sa.Column(sa.String(100), nullable=False)
    actor_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    target_type = sa.Column(sa.String(50), nullable=False)  # 'request' or 'user'
    target_id = sa.Column(sa.Integer, nullable=False)
    old_state = sa.Column(sa.Text, nullable=True)
    new_state = sa.Column(sa.Text, nullable=True)
    comment = sa.Column(sa.Text, nullable=True)
    ip_address = sa.Column(sa.String(50), nullable=True)
    logged_at = sa.Column(sa.DateTime, default=sa.func.now())
