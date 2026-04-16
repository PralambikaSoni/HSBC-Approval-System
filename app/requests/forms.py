from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class RequestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    category = SelectField('Category', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Request')
    
class ResubmitForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Resubmit')
