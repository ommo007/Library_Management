from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from db import User, Section

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('2', 'Student')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

# Book form
class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=256)])
    author = StringField('Author', validators=[DataRequired(), Length(max=128)])
    isbn = StringField('ISBN', validators=[Length(max=20)])
    genre = StringField('Genre', validators=[Length(max=64)])
    section_id = SelectField('Section', coerce=int, validators=[DataRequired()])
    available = BooleanField('Available')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        # Get all sections from the database
        sections = Section.get_all()
        self.section_id.choices = [(s.id, s.name) for s in sections]

# Section form
class SectionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

    def __init__(self, original_name=None, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        if name.data != self.original_name:
            section = Section.get_by_name(name.data)
            if section:
                raise ValidationError('Section name already exists. Please choose a different one.')

# Search form
class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    section = SelectField('Filter by Section', coerce=int, choices=[(0, 'All Sections')])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        # Get all sections from the database
        sections = Section.get_all()
        self.section.choices = [(0, 'All Sections')] + [(s.id, s.name) for s in sections]

# Librarian Creation Form (for admin use)
class LibrarianCreationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', validators=[DataRequired()])
    submit = SubmitField('Create Account')