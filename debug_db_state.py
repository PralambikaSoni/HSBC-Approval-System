from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    print("Search 'pws1':", User.query.filter(User.department == 'pws1').all())
    print("Search 'PWS1':", User.query.filter(User.department == 'PWS1').all())
    print("ilike 'pws1':", User.query.filter(User.department.ilike('pws1')).all())
