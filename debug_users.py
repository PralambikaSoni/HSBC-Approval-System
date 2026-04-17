from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print("--- USERS ---")
    for u in users:
        print(f"ID: {u.id} | Name: {u.full_name} | Role: {u.role} | Dept: {u.department}")
