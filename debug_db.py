import sys
import traceback
with open("real_error.txt", "w") as f:
    try:
        from app import create_app
        from app.extensions import db
        app = create_app()
        app.app_context().push()
        db.create_all()
    except Exception as e:
        traceback.print_exc(file=f)
