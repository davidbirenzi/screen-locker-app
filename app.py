from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    progress = db.Column(db.Integer, default=0)
    quiz_grades = db.relationship('QuizGrade', backref='user', lazy=True)

class QuizGrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get the latest grade for each course
    python_grade = QuizGrade.query.filter_by(user_id=current_user.id, course='python').order_by(QuizGrade.date_taken.desc()).first()
    database_grade = QuizGrade.query.filter_by(user_id=current_user.id, course='database').order_by(QuizGrade.date_taken.desc()).first()
    web_grade = QuizGrade.query.filter_by(user_id=current_user.id, course='web').order_by(QuizGrade.date_taken.desc()).first()
    
    return render_template('dashboard.html', 
                         python_grade=python_grade,
                         database_grade=database_grade,
                         web_grade=web_grade)

@app.route('/course/<int:course_id>')
@login_required
def course(course_id):
    # Get all grades for the specific course
    course_name = 'python' if course_id == 1 else 'database' if course_id == 2 else 'web'
    grades = QuizGrade.query.filter_by(user_id=current_user.id, course=course_name).order_by(QuizGrade.date_taken.desc()).all()
    return render_template('course.html', course_id=course_id, grades=grades)

@app.route('/start_quiz/<course>')
@login_required
def start_quiz(course):
    try:
        subprocess.Popen(['python', 'quiz_app.py', course])
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Error starting quiz: ' + str(e))
        return redirect(url_for('dashboard'))

@app.route('/submit_grade', methods=['POST'])
@login_required
def submit_grade():
    data = request.get_json()
    grade = QuizGrade(
        user_id=current_user.id,
        course=data['course'],
        score=data['score'],
        total_questions=data['total_questions']
    )
    db.session.add(grade)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 