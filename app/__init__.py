import os
import atexit
import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, bcrypt, csrf, scheduler as bg_scheduler

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    from .extensions import migrate
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    with app.app_context():
        # Setup scheduler if not already running
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            if not bg_scheduler.running:
                from .scheduler.tasks import check_escalations
                bg_scheduler.app = app
                bg_scheduler.add_job(id='check_escalations_job', func=check_escalations, trigger='interval', seconds=60)
                bg_scheduler.start()

        from .models import User
        @login_manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

    # Register Blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from .dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/')

    from .admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .search import search_bp
    app.register_blueprint(search_bp, url_prefix='/search')

    from .requests import requests_bp
    app.register_blueprint(requests_bp, url_prefix='/requests')

    from .approvals import approvals_bp
    app.register_blueprint(approvals_bp, url_prefix='/approvals')

    from .notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Register CLI commands
    from .cli import seed_admin_command
    app.cli.add_command(seed_admin_command)

    return app
