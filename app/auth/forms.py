from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ProfileUpdateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('New Password (leave blank to keep current)')
    submit = SubmitField('Update Profile')
