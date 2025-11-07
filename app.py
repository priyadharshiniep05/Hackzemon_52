from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
from utils.face_analyzer import FaceAnalyzer
from utils.voice_analyzer import VoiceAnalyzer
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/wellness_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    wellness_data = db.relationship('WellnessData', backref='user', lazy=True)

class WellnessData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stress_level = db.Column(db.Float)
    fatigue_level = db.Column(db.Float)
    wellness_index = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize analyzers
face_analyzer = FaceAnalyzer()
voice_analyzer = VoiceAnalyzer()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('menu'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
            
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/live_analysis')
@login_required
def live_analysis():
    return render_template('live_analysis.html')

@app.route('/voice_analysis')
@login_required
def voice_analysis():
    return render_template('voice_analysis.html')

@app.route('/analyze_face', methods=['POST'])
@login_required
def analyze_face():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    
    # Analyze face
    results = face_analyzer.analyze(img)
    
    # Save to database
    wellness_data = WellnessData(
        user_id=current_user.id,
        stress_level=results.get('stress_score', 0),
        fatigue_level=results.get('fatigue_score', 0),
        wellness_index=results.get('wellness_index', 0)
    )
    db.session.add(wellness_data)
    db.session.commit()
    
    return jsonify(results)

@app.route('/analyze_voice', methods=['POST'])
@login_required
def analyze_voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio provided'}), 400
    
    audio_file = request.files['audio']
    
    # Save temporarily
    temp_path = 'temp_audio.wav'
    audio_file.save(temp_path)
    
    try:
        # Analyze voice
        results = voice_analyzer.analyze_audio(temp_path)
        
        # Save to database
        wellness_data = WellnessData(
            user_id=current_user.id,
            stress_level=results.get('stress_score', 0),
            fatigue_level=results.get('fatigue_score', 0),
            wellness_index=results.get('wellness_index', 0)
        )
        db.session.add(wellness_data)
        db.session.commit()
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/get_wellness_data')
@login_required
def get_wellness_data():
    data = WellnessData.query.filter_by(user_id=current_user.id).order_by(WellnessData.timestamp.desc()).limit(5).all()
    result = [{
        'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M'),
        'wellness_index': d.wellness_index,
        'stress_level': d.stress_level,
        'fatigue_level': d.fatigue_level
    } for d in data]
    return jsonify(result)

@app.route('/profile')
@login_required
def profile():
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'join_date': '2023-01-01'  # Add actual join date field to User model
    }
    return render_template('profile.html', user=user_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
