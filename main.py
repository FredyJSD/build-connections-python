import os
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for
import json

from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_wtf import CSRFProtect
from sqlalchemy import Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
csrf = CSRFProtect(app)
Bootstrap5(app)

# Creating Databases
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    reset_token: Mapped[str] = mapped_column(String(100), nullable=True)
    reset_token_expiry: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # relationships
    questions = relationship("Questions", back_populates="creator", cascade="all, delete-orphan")
    progress = relationship("UserQuestionProgress", back_populates="user", cascade="all, delete-orphan")


class Questions(db.Model):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # relationships
    creator = relationship("Users", back_populates="questions")
    progress = relationship("UserQuestionProgress", back_populates="question", cascade="all, delete-orphan")


class UserQuestionProgress(db.Model):
    __tablename__ = "question_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    answered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    # relationships
    user = relationship("Users", back_populates="progress")
    question = relationship("Questions", back_populates="progress")


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# Function to load JSON data
def load_json(question_file):
    try:
        file_path = os.path.join(DATA_DIR, f"{question_file}.json")  # Correct path resolution
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as err:
        print(f"Error reading or parsing the JSON file: {err}")
        raise

def hash_password(password):
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
    return hashed_password


def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    # if form.validate_on_submit():
    #     email = form.email.data
    #     result = db.session.execute(db.select(Users).where(Users.email == email))
    #     user = result.scalar()
    #     if user:
    #         flash("You've already signed up with that email, log in instead!")
    #         return redirect(url_for('login'))
    #
    #     new_user = Users(
    #         name=form.name.data,
    #         email=form.email.data,
    #         password=hash_password(form.password.data)
    #     )
    #
    #     db.session.add(new_user)
    #     db.session.commit()
    #     login_user(new_user)
    #     return redirect(url_for("menu"))
    return render_template("register.html", form=form)

@app.route("/login")
def login():
    return render_template("index.html")


@app.route('/icebreaker')
def icebreaker():
    questions = load_json('questions')
    ice_level = next((level for level in questions["levels"] if level["name"] == "ice breaker"), None)
    ice_questions = ice_level["questions"] if ice_level else []
    return render_template('ice.html', question=ice_questions)


@app.route('/confess')
def confess():
    questions = load_json('questions')
    confess_level = next((level for level in questions["levels"] if level["name"] == "confess"), None)
    confess_questions = confess_level["questions"] if confess_level else []
    return render_template('confess.html', question=confess_questions)


@app.route('/deep')
def deep():
    questions = load_json('questions')
    deep_level = next((level for level in questions["levels"] if level["name"] == "deep"), None)
    deep_questions = deep_level["questions"] if deep_level else []
    return render_template('deep.html', question=deep_questions)


if __name__ == '__main__':
    app.run(debug=True, port=3000)
