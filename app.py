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
=======
from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import random
import time
import os

app = Flask(__name__)

# Initialize OpenCV's face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Initialize variables for wellness tracking
blink_counter = 0
last_blink_time = time.time()
blink_rate = 0
fatigue_score = 0
stress_score = 0
last_alert_time = time.time()
frame_count = 0

# Constants
EYE_CLOSED_FRAMES = 0
EYE_CLOSED_THRESHOLD = 3  # Number of frames to consider an eye as closed

def generate_frames():
    global blink_counter, last_blink_time, blink_rate, fatigue_score, stress_score, last_alert_time, frame_count, EYE_CLOSED_FRAMES
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
        
    print("Webcam opened successfully")
    
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Could not read frame from webcam")
            break
        
        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)
        frame_count += 1
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Region of interest for eyes
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            # Detect eyes
            eyes = eye_cascade.detectMultiScale(roi_gray)
            
            # Simple blink detection
            if len(eyes) == 0:  # No eyes detected (blinking)
                EYE_CLOSED_FRAMES += 1
                if EYE_CLOSED_FRAMES == EYE_CLOSED_THRESHOLD:  # Just closed
                    blink_counter += 1
                    current_time = time.time()
                    if last_blink_time > 0:
                        blink_rate = 1.0 / (current_time - last_blink_time)
                    last_blink_time = current_time
            else:
                EYE_CLOSED_FRAMES = 0
                
                # Draw rectangles around eyes
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
            
            # Update wellness scores with recovery mechanism
            current_time = time.time()
            if current_time - last_alert_time > 10:  # Update scores every 10 seconds
                # If eyes are open and no stress detected, recover
                if EYE_CLOSED_FRAMES < EYE_CLOSED_THRESHOLD:  # Eyes are open
                    # Recover from stress and fatigue
                    stress_score = max(0, stress_score - random.uniform(1, 5))
                    fatigue_score = max(0, fatigue_score - random.uniform(0.5, 3))
                else:
                    # Increase stress and fatigue if eyes are closed (blinking/straining)
                    stress_score = min(100, stress_score + random.uniform(1, 3))
                    fatigue_score = min(100, fatigue_score + random.uniform(0.5, 2))
                
                # Add some small random variation
                stress_score = max(0, min(100, stress_score + random.uniform(-2, 2)))
                fatigue_score = max(0, min(100, fatigue_score + random.uniform(-1, 1.5)))
                
                last_alert_time = current_time
        
        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    try:
        return Response(generate_frames(),
                      mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"Error in video_feed: {str(e)}")
        return str(e), 500

@app.route('/get_wellness_data')
def get_wellness_data():
    global stress_score, fatigue_score
    
    # Calculate wellness index (0-100) - higher is better
    # Weighted average where stress has slightly more impact than fatigue
    wellness_index = max(0, min(100, 100 - (stress_score * 0.45 + fatigue_score * 0.35)))
    
    # Determine risk level and recommendation
    if wellness_index <= 40:
        risk_level = "CRITICAL/HIGH RISK"
        recommendation = "🚨 Immediate Rest Alert: Stop working now. Perform a 4-7-8 Breathing Exercise (4s inhale, 7s hold, 8s exhale) for 5 rounds, or take a 10-minute walk."
    elif wellness_index <= 65:
        risk_level = "MEDIUM RISK"
        recommendation = "💧 Hydration & Mindful Break: Risk is elevated. Take a break, drink a glass of water, and look away from your screen for two minutes."
    elif wellness_index <= 85:
        risk_level = "LOW/MODERATE RISK"
        recommendation = "🧘 Micro-Break/Stretch: Risk is low. To maintain focus, stand up and stretch for 60 seconds."
    else:
        risk_level = "LOW RISK"
        recommendation = "✅ All Good: Great! Maintain your current focus. Remember to drink water."
    
    return jsonify({
        'wellness_index': int(wellness_index),
        'stress_score': int(stress_score),
        'fatigue_score': int(fatigue_score),
        'blink_rate': round(blink_rate, 2),
        'risk_level': risk_level,
        'recommendation': recommendation
    })

if __name__ == '__main__':
    app.run(debug=True, port=5051, host='0.0.0.0')
