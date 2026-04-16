import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-this')
    # Defaulting to instance/ipas.db as per SRS Section 3 and 7
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'ipas.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Snooze durations (hours) — shown as dropdown options
    SNOOZE_DURATIONS = [1, 4, 24, 48]

    # Maximum snooze count per approver per request
    MAX_SNOOZE_COUNT = 3

    # Escalation thresholds in hours by priority
    ESCALATION_THRESHOLDS = {
        'critical': 4,
        'high': 24,
        'medium': 48,
        'low': 72,
    }

    # Maximum escalation count before flagging for Director intervention
    MAX_ESCALATION_COUNT = 2

    # Account lockout settings
    MAX_FAILED_LOGINS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Audit log retention in days
    AUDIT_LOG_RETENTION_DAYS = 365

    # Scheduler intervals (minutes)
    SNOOZE_CHECK_INTERVAL_MINUTES = 5
    ESCALATION_CHECK_INTERVAL_MINUTES = 15

    # Request categories (shown in the create request form dropdown)
    REQUEST_CATEGORIES = [
        'Leave Request',
        'Budget Approval',
        'Access Permission',
        'Purchase Request',
        'Policy Exception',
        'IT Support',
        'HR Matter',
        'Other',
    ]
