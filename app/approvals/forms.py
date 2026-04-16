from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class ApprovalActionForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('request_details', 'Return for Edits')
    ], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Submit Action')

class SnoozeForm(FlaskForm):
    reason = TextAreaField('Snooze Reason', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Snooze (24h)')
