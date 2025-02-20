import os
from datetime import datetime

from flask import Flask, render_template
import json

from sqlalchemy import Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


# Creating Databases
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Users(db.Model):
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


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


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
