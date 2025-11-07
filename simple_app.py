from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wellness.db'
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

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    return render_template('login.html')

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
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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

@app.route('/profile')
@login_required
def profile():
    wellness_data = WellnessData.query.filter_by(user_id=current_user.id).order_by(WellnessData.timestamp.desc()).all()
    return render_template('profile.html', wellness_data=wellness_data)

@app.route('/wellness_assistant')
@login_required
def wellness_assistant():
    return render_template('wellness_assistant.html')

@app.route('/games')
@login_required
def games():
    return render_template('games.html')

@app.route('/wellness_graph')
@login_required
def wellness_graph():
    # Sample data for the graph
    wellness_data = WellnessData.query.filter_by(user_id=current_user.id)\
        .order_by(WellnessData.timestamp).all()
    
    # Prepare data for the chart
    dates = [data.timestamp.strftime('%Y-%m-%d') for data in wellness_data]
    stress_levels = [data.stress_level for data in wellness_data] if wellness_data else []
    fatigue_levels = [data.fatigue_level for data in wellness_data] if wellness_data else []
    
    return render_template('wellness_graph.html',
                         dates=dates,
                         stress_levels=stress_levels,
                         fatigue_levels=fatigue_levels)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
