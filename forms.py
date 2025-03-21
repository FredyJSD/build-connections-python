from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, URL, Email, Length, Optional
from flask_ckeditor import CKEditorField


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Create Account!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login!")


class NewSession(FlaskForm):
    session_name = StringField("Name", validators=[DataRequired()])
    invite = StringField("Invite User", validators=[Optional(), Email()])
    submit = SubmitField("Add Session!")


class NewQuestion(FlaskForm):
    question = TextAreaField("New Question", render_kw={"rows": 3, "cols": 40}, validators=[DataRequired()])
    submit = SubmitField("Add Question!")


class RequestReset(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset Password!")
