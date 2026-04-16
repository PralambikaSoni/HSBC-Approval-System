from datetime import datetime, timezone
from ..models import Request
from ..extensions import db

def generate_request_code():
    """Generates code in format HSBC-YYYY-NNNN"""
    year = str(datetime.now(timezone.utc).year)
    
    # Get the latest request
    last_req = Request.query.order_by(Request.id.desc()).first()
    
    if not last_req:
        return f"HSBC-{year}-0001"
        
    parts = last_req.request_code.split('-')
    if len(parts) == 3 and parts[1] == year:
        seq = int(parts[2]) + 1
        return f"HSBC-{year}-{seq:04d}"
    else:
        # Reset counter for new year
        return f"HSBC-{year}-0001"
