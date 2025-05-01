import secrets, time, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
import json
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_wtf import CSRFProtect
from sqlalchemy import Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, NewSession, NewQuestion, RequestReset, ResetPasswordForm
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Creating Databases
class Base(DeclarativeBase):
    pass

db_uri = os.environ.get("DB_URI", "sqlite:///build_connections.db")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
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
    session_associations = relationship("GameSessionUsers", back_populates="user", cascade="all, delete-orphan")


class GameSession(db.Model):
    __tablename__ = "game_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # relationships
    progress = relationship("UserQuestionProgress", back_populates="session", cascade="all, delete-orphan")
    session_associations = relationship("GameSessionUsers", back_populates="session", cascade="all, delete-orphan")


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
    session_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("game_sessions.id", ondelete="CASCADE"),
                                            nullable=False)
    answered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    question_level: Mapped[str] = mapped_column(String(20), nullable=False)

    # relationships
    question = relationship("Questions", back_populates="progress")
    session = relationship("GameSession", back_populates="progress")


class GameSessionUsers(db.Model):
    __tablename__ = "game_session_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("game_sessions.id", ondelete="CASCADE"),
                                            nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # relationships
    session = relationship("GameSession", back_populates="session_associations")
    user = relationship("Users", back_populates="session_associations")



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


# For Testing
def add_all_questions(admin_id: int):
    questions = [
        # Ice Breaker Questions
        Questions(
            level="ice breaker",
            text="How do you usually spend your weekends?",
            created_by=admin_id
        ),
        Questions(
            level="deep",
            text="What’s the last movie or TV show you really enjoyed?",
            created_by=admin_id
        ),
        Questions(
            level="confess",
            text="What’s a hobby you could talk about for hours?",
            created_by=admin_id
        ),
        Questions(
            level="ice breaker",
            text="If you could visit anywhere in the world, where would you go and why?",
            created_by=admin_id
        ),
        Questions(
            level="ice breaker",
            text="Do you prefer the beach, mountains, or city for a getaway?",
            created_by=admin_id
        )
    ]
    db.session.add_all(questions)  # Add all questions to session
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)


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
    db.create_all()
    add_all_questions(1)
    return render_template('index.html', current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(Users).where(Users.email == email))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        new_user = Users(
            name=form.name.data,
            email=form.email.data,
            password=hash_password(form.password.data)
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("menu"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(Users).where(Users.email == email))
        user = result.scalar()
        if user and verify_password(user.password, password):
            login_user(user)
            return redirect(url_for("menu"))
        else:
            flash("That email or password is incorrect")
            return redirect(url_for('login'))

    return render_template("login.html", form=form)


@app.route('/reset', methods=["GET", "POST"])
def reset_password():
    form = RequestReset()
    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(Users).where(Users.email == email))
        user = result.scalar()
        if user:
            secret_key = secrets.token_urlsafe(16)
            user.reset_token = secret_key
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()
            reset_link = url_for('reset_token_route', token=secret_key, _external=True)
            msg = Message(
                f'Build Connections. Reset Password!',
                sender=os.environ.get('MAIL_USERNAME'),
                recipients=[user.email],
            )
            msg.body = f'Click the link to reset your password: {reset_link}'
            mail.send(msg)
            flash("A reset link has been sent to your email if account exists.", "info")
            return redirect(url_for('login'))
        else:
            flash("Email Does Not Exist", "danger")
            return redirect(url_for('login'))
    return render_template("request_reset.html", form=form)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_token_route(token):
    form = ResetPasswordForm()
    user = db.session.execute(db.select(Users).where(Users.reset_token == token)).scalar()
    if user and (user.reset_token_expiry > datetime.utcnow()):
        if form.validate_on_submit():
            user.password = hash_password(form.password.data)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash("Your password has been reset.", "success")
            return redirect(url_for('login'))

        return render_template("reset_password.html", form=form)
    else:
        flash("Token Invalid!", "danger")
        return redirect(url_for('login'))


@app.route('/sessions')
def sessions():
    result = db.session.execute(
        db.select(GameSession).join(GameSessionUsers).where(GameSessionUsers.user_id == current_user.id)
    )
    game_sessions = result.scalars().all()
    return render_template('sessions.html', game_sessions=game_sessions)


@login_required
@app.route('/new-session', methods=["GET", "POST"])
def create_session():
    form = NewSession()
    if form.validate_on_submit():
        session_name = form.session_name.data
        invited_user_email = form.invite.data
        invited_user = None
        if invited_user_email:
            invited_user = db.session.execute(db.select(Users).where(Users.email == invited_user_email)).scalar()
            if not invited_user:
                flash("User email does not exist", "danger")
                return render_template("create_session.html", form=form)
        new_session = GameSession(name=session_name)
        db.session.add(new_session)
        db.session.commit()
        creator_session_link = GameSessionUsers(
            session_id=new_session.id,
            user_id=current_user.id
        )
        db.session.add(creator_session_link)
        if invited_user:
            invited_session_link = GameSessionUsers(
                session_id=new_session.id,
                user_id=invited_user.id
            )
            db.session.add(invited_session_link)
        db.session.commit()

        questions_result = db.session.execute(
            db.select(Questions).where((Questions.created_by == 1) | (Questions.created_by == current_user.id))
        ).scalars().all()

        for question in questions_result:
            new_user_question_progress = UserQuestionProgress(
                session_id=new_session.id,
                answered=False,
                question_id=question.id,
                question_level=question.level
            )
            db.session.add(new_user_question_progress)

        db.session.commit()
        return redirect(url_for("sessions"))
    else:
        print("Form validation failed!")  # Debugging statement
        print("Errors:", form.errors)  # Check validation errors

    return render_template('create_session.html', form=form)


@app.route("/delete/<int:session_id>")
def delete_session(session_id):
    session_to_delete = db.get_or_404(GameSession, session_id)
    db.session.delete(session_to_delete)
    db.session.commit()
    return redirect(url_for('sessions'))


@app.route('/menu')
@app.route('/menu/<int:session_id>')
def menu(session_id=None):
    if session_id:
        return render_template('menu.html', session_id=session_id)
    return render_template('menu.html')


@app.route('/new-question', methods=["GET", "POST"])
@app.route('/new-question/<int:session_id>', methods=["GET", "POST"])
@login_required
def new_question(session_id=None):
    form = NewQuestion()
    if form.validate_on_submit():
        question_text = form.question.data
        new_user_question = Questions(
            level="user_question",
            text=question_text,
            created_by=current_user.id
        )
        db.session.add(new_user_question)
        db.session.commit()
        return redirect(url_for("user_menu", session_id=session_id))
    return render_template('new_question.html', form=form, session_id=session_id)


@app.route('/user-menu')
@app.route('/user-menu/<int:session_id>')
def user_menu(session_id=None):
    return render_template('user-question-menu.html', session_id=session_id)


@app.route('/icebreaker')
@app.route('/icebreaker/<int:session_id>')
def icebreaker(session_id=None):
    if session_id:
        result = db.session.execute(
            db.select(
                Questions.text, UserQuestionProgress.question_id, UserQuestionProgress.answered)
            .join(UserQuestionProgress)
            .filter(UserQuestionProgress.question_level == "ice breaker")
            .filter(UserQuestionProgress.session_id == session_id)
        )
        ice_questions = result.all()
        questions_list = [{
            "text": q.text,
            "question_id": q.question_id,
            "answered": q.answered
        } for q in ice_questions]
        print(f"Session ID being passed to template: {session_id}")
        return render_template('ice.html', questions=questions_list, session_id=session_id)

    result = db.session.execute(
        db.select(Questions).filter(Questions.created_by == 1, Questions.level == "ice breaker")
    )
    ice_questions = result.scalars().all()
    questions_list = [{"text": q.text} for q in ice_questions]
    print(f"No session ID being passed")
    return render_template('ice.html', questions=questions_list, session_id=session_id)


@app.route('/confess')
@app.route('/confess/<int:session_id>')
def confess(session_id=None):
    if session_id:
        result = db.session.execute(
            db.select(Questions.text, UserQuestionProgress.question_id, UserQuestionProgress.answered)
            .join(UserQuestionProgress)
            .filter(UserQuestionProgress.question_level == "confess")
            .filter(UserQuestionProgress.session_id == session_id)
        )
        confess_questions = result.all()
        questions_list = [{
            "text": q.text,
            "question_id": q.question_id,
            "answered": q.answered
        } for q in confess_questions]
        print(f"Session ID being passed to template: {session_id}")
        return render_template('confess.html', questions=questions_list, session_id=session_id)

    result = db.session.execute(
        db.select(Questions).filter(Questions.created_by == 1, Questions.level == "confess")
    )
    confess_questions = result.scalars().all()
    questions_list = [{"text": q.text} for q in confess_questions]
    return render_template('confess.html', questions=questions_list, session_id=session_id)


@app.route('/deep')
@app.route('/deep/<int:session_id>')
def deep(session_id=None):
    if session_id:
        result = db.session.execute(
            db.select(Questions.text, UserQuestionProgress.question_id, UserQuestionProgress.answered)
            .join(UserQuestionProgress)
            .filter(UserQuestionProgress.question_level == "deep")
            .filter(UserQuestionProgress.session_id == session_id)
        )
        deep_questions = result.all()
        questions_list = [{
            "text": q.text,
            "question_id": q.question_id,
            "answered": q.answered
        } for q in deep_questions]
        print(f"Session ID being passed to template: {session_id}")
        return render_template('deep.html', questions=questions_list, session_id=session_id)

    result = db.session.execute(
        db.select(Questions).filter(Questions.created_by == 1, Questions.level == "deep")
    )
    deep_questions = result.scalars().all()
    questions_list = [{"text": q.text} for q in deep_questions]
    return render_template('deep.html', questions=questions_list, session_id=session_id)


@app.route('/user-questions')
@app.route('/user-questions/<int:session_id>')
@login_required
def user_questions(session_id=None):
    result = db.session.execute(
        db.select(Questions).filter(Questions.created_by == current_user.id, Questions.level == "user_question")
    )
    deep_questions = result.scalars().all()
    questions_list = [{"text": q.text} for q in deep_questions]
    return render_template('user_questions.html', questions=questions_list, session_id=session_id)


@csrf.exempt
@app.route('/update_answered', methods=["POST"])
def update_answer():
    print("Answering Question")
    data = request.get_json()
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    answered = bool(data.get("answered"))

    result = db.session.execute(db.select(UserQuestionProgress)
                                  .filter(UserQuestionProgress.session_id == session_id)
                                  .filter(UserQuestionProgress.question_id == question_id))

    progress = result.scalar()
    if progress:
        progress.answered = answered
        db.session.commit()
        return jsonify({"status": "success", "message": "Answer updated successfully."})
    else:
        return jsonify({"status": "error", "message": "Progress record not found."}), 404

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, port=5003)
