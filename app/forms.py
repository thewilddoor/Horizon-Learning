# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('teacher', 'Teacher'), ('student', 'Student')], validators=[DataRequired()])
    school_name = StringField('School Name')  # Only for teachers
    class_code = StringField('Class Code')    # Only for students (optional or auto-generated)
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BotForm(FlaskForm):
    name = StringField('Bot Name', validators=[DataRequired(), Length(min=2, max=64)])
    bot_id = StringField('Bot ID', validators=[DataRequired(), Length(min=2, max=64)])
    api_token = StringField('API Token', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Submit')

class LearningCompanionForm(FlaskForm):
    class_name = StringField('Class Name', validators=[DataRequired(), Length(min=2, max=64)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=64)])
    instructions = TextAreaField('Custom Instructions(Optional)')
    bot = SelectField('Select Bot', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create')

class MaterialUploadForm(FlaskForm):
    companion = SelectField('Select Learning Companion', coerce=int, validators=[DataRequired()])
    file = FileField('Upload Material', validators=[DataRequired(), FileAllowed(['pdf', 'docx', 'ppt', 'pptx'], 'PDF, DOCX, PPT, PPTX only!')])
    submit = SubmitField('Upload')

class AssignMaterialForm(FlaskForm):
    companion = SelectField('Select Learning Companion', coerce=int, validators=[DataRequired()])
    material = SelectField('Select Material', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')

class LinkCompanionForm(FlaskForm):
    class_code = StringField('Class Code', validators=[DataRequired(), Length(min=6, max=10)])
    submit = SubmitField('Link')

class ChatForm(FlaskForm):
    message = StringField('Your Message', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Send')

class EditLearningCompanionForm(FlaskForm):
    class_name = StringField('Class Name', validators=[DataRequired(), Length(min=2, max=64)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=64)])
    instructions = TextAreaField('Custom Instructions(Optional)')
    bot = SelectField('Select Bot', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update')

class ClearMessagesForm(FlaskForm):
    companion_id = HiddenField('Companion ID', validators=[Optional()])
    submit = SubmitField('Clear Messages')
