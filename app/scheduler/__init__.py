from flask import Blueprint

scheduler_bp = Blueprint('scheduler_bp', __name__)

from . import tasks
