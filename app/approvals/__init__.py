from flask import Blueprint

approvals_bp = Blueprint('approvals_bp', __name__)

from . import routes
