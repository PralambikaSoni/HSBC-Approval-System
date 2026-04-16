from ..models import Notification
from ..extensions import db

def send_notification(user_id, message, request_id=None):
    """Creates a new in-app notification for a user."""
    n = Notification(
        user_id=user_id,
        message=message,
        request_id=request_id
    )
    db.session.add(n)
    # Note: caller is responsible for db.session.commit() unless required immediately.
    # We will safely let the caller commit it to avoid partial transaction commits.
