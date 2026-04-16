import click
from flask.cli import with_appcontext
from .extensions import db, bcrypt
from .models import User

@click.command('seed-admin')
@with_appcontext
def seed_admin_command():
    """Create the first admin user (Director role)."""
    if db.session.query(User).first() is not None:
        click.echo("Database is not empty. Seed aborted.")
        return

    employee_id = click.prompt("Employee ID")
    full_name = click.prompt("Full Name")
    department = click.prompt("Department")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    admin_user = User(
        employee_id=employee_id,
        full_name=full_name,
        department=department,
        role='director',
        password_hash=pw_hash,
        is_active=True
    )
    db.session.add(admin_user)
    db.session.commit()
    click.echo(f"Admin user {employee_id} created successfully.")
