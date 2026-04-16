from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from ..models import User

class UserCreateForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=50)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    role = SelectField('Role', choices=[
        ('employee', 'Employee'),
        ('team_lead', 'Team Lead'),
        ('manager', 'Manager'),
        ('director', 'Director')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    force_pw_reset = BooleanField('Force password reset on first login')
    submit = SubmitField('Create User')

    def validate_employee_id(self, employee_id):
        user = User.query.filter_by(employee_id=employee_id.data).first()
        if user:
            raise ValidationError('That Employee ID is already taken.')

class UserEditForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    role = SelectField('Role', choices=[
        ('employee', 'Employee'),
        ('team_lead', 'Team Lead'),
        ('manager', 'Manager'),
        ('director', 'Director')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Changes')
