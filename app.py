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
