from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length,Email,EqualTo, ValidationError
from blog.models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
     username = StringField('Username',
         validators=[DataRequired(), Length(min=2,max=10)])
     email = StringField('Email', validators=[DataRequired(), Email() ])
     password = PasswordField('Password', validators=[DataRequired()])
     confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
     submit = SubmitField('Sign Up')
     def validate_username(self,username):
         user = User.query.filter_by(username = username.data).first()
         if user:
             raise ValidationError('Username already taken. Please input a different username')
     def validate_email(self, email):
         user = User.query.filter_by(email = email.data).first()
         if user:
             raise ValidationError('There is an account associated with the email '+email.data)
class LoginForm(FlaskForm):
     email = StringField('Email', validators=[DataRequired(), Email() ])
     password = PasswordField('Password', validators=[DataRequired()])
     remember = BooleanField('Remember me')
     submit = SubmitField('Login')     

class UpdateAccountForm(FlaskForm):
     username = StringField('Username',
         validators=[DataRequired(), Length(min=2,max=10)])
     email = StringField('Email', validators=[DataRequired(), Email() ])
     picture = FileField('Update profile picture', validators=[FileAllowed(['jpg','png'])])
     submit = SubmitField('Update')
     def validate_username(self,username):
         if username.data!=current_user.username:
            user = User.query.filter_by(username = username.data).first()
            if user:
                raise ValidationError('Username already taken. Please input a different username')
     def validate_email(self, email):
         if email.data != current_user.email:
            user = User.query.filter_by(email = email.data).first()
            if user:
                raise ValidationError('There is an account associated with the email '+email.data)

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField("Post")


class RequestResetForm(FlaskForm):
     email = StringField('Email', validators=[DataRequired(), Email() ])
     submit = SubmitField('Request password reset link')   
     def validate_email(self, email):
         user = User.query.filter_by(email = email.data).first()
         if not user:
             raise ValidationError('There is no account associated with the email address '+email.data)

class PasswordResetForm(FlaskForm):
     password = PasswordField('Password', validators=[DataRequired()])
     confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
     submit = SubmitField('Reset password')