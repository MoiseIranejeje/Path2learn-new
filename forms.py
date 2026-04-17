from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
# Import from the new models.py file
from models import User # Assuming User model is still relevant for AddAdminForm

class CsvUploadForm(FlaskForm):
    csv_file = FileField('Upload CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'Only CSV files are allowed!')
    ])
    submit = SubmitField('Upload Schools')

class AddAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Admin')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class SuggestSchoolForm(FlaskForm):
    # Core Info
    name = StringField('Name of the school .', validators=[DataRequired()])
    province = SelectField('Province', validators=[DataRequired()], choices=[]) # Populated in the route
    district = SelectField('District', validators=[DataRequired()], choices=[])
    sector = SelectField('Sector', validators=[DataRequired()], choices=[])
    
    # Policies and Programs
    gender_policy = SelectField('Gender Inclusivity Policy', validators=[DataRequired()], choices=['Mixed', 'Boys Only', 'Girls Only'])
    ownership = SelectField('Ownership policy', validators=[DataRequired()], choices=['Public', 'Private', 'Government -Aided (Religious)'])
    education_program = SelectField('Education program', validators=[DataRequired()], choices=[
        'Rwandan General Education (REB Curriculum)', 'Cambridge International Education (CIE)', 'Technical and Vocational Education and Training (TVET)'
    ])
    boarding_policy = SelectField('Boarding / Day Policy', validators=[DataRequired()], choices=['Day School', 'Boarding School', 'Day and Boarding'])
    
    # Description and Photos
    description = TextAreaField('1.Descibe the school its life style and others in not more than 100 words.', validators=[DataRequired()])
    photos = TextAreaField('Add atleast one school photo (For visual reference) (Please Right click on the image and then copy image address)', validators=[DataRequired()])
    extracurriculars = TextAreaField('Extracurricular Activities (e.g., Football, Debate Club, Music, Robotics)')

    # Optional Contact Info
    phone = StringField('Phone number')
    website = StringField('School Website (If any )')
    
    # Optional Other Info
    religious_affiliation = StringField('Religious denominations (Optional)')

    # Suggester Info
    suggester_name = StringField('Your Name (Optional)')
    suggester_email = StringField('Your Email (Optional, for updates)', validators=[Optional(), Email()])

    submit = SubmitField('Submit Suggestion')

# ★★★ START: NEW REVIEW FORM ★★★
class ReviewForm(FlaskForm):
    rating = SelectField('Rating (1-5 Stars)', choices=[
        ('5', '★★★★★ - Excellent'),
        ('4', '★★★★☆ - Very Good'),
        ('3', '★★★☆☆ - Average'),
        ('2', '★★☆☆☆ - Below Average'),
        ('1', '★☆☆☆☆ - Poor')
    ], validators=[DataRequired()])
    comment = TextAreaField('Your Review', validators=[DataRequired()])
    reviewer_name = StringField('Your Name', validators=[DataRequired()], default='Anonymous')
    submit = SubmitField('Submit Review')
# ★★★ END: NEW REVIEW FORM ★★★
# ★★★ START: NEW CONTACT FORM ★★★
class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')
# ★★★ END: NEW CONTACT FORM ★★★
# ★★★ NEW: CHANGE PASSWORD FORM ★★★
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# ★★★ START: NEW AUTH FORMS ★★★
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('I am a...', choices=[('student', 'Student'), ('parent', 'Parent')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use.')

class LinkFamilyForm(FlaskForm):
    # Field to enter the email of the person to link
    target_email = StringField('Family Member Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Link Account')

class CompareSchoolsForm(FlaskForm):
    school1 = SelectField('Select First School', coerce=int, validators=[DataRequired()])
    school2 = SelectField('Select Second School', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Compare Schools')
# ★★★ END: NEW AUTH FORMS ★★★