import cv2
import numpy as np
from datetime import datetime

class FaceAnalyzer:
    def __init__(self):
        # Initialize face detection model (using Haar Cascade for simplicity)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Initialize variables for frame analysis
        self.prev_frame_time = 0
        self.face_roi = None
        self.eye_strain_frames = 0
        self.blink_count = 0
        self.last_blink_time = datetime.now()
        
    def detect_face(self, frame):
        """Detect face in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            self.face_roi = (x, y, w, h)
            return True, (x, y, w, h)
        return False, None
    
    def detect_eyes(self, frame, face_roi):
        """Detect eyes in the face region"""
        x, y, w, h = face_roi
        face_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(face_gray)
        return eyes
    
    def analyze_eye_strain(self, eyes, frame_count):
        """Analyze eye strain based on eye detection"""
        if len(eyes) < 2:  # If eyes not detected
            self.eye_strain_frames += 1
        else:
            self.eye_strain_frames = max(0, self.eye_strain_frames - 0.5)
            
        # Calculate eye strain score (0-100)
        eye_strain = min(100, (self.eye_strain_frames / frame_count) * 100) if frame_count > 0 else 0
        return eye_strain
    
    def detect_blinks(self, eyes, frame):
        """Detect blinks based on eye aspect ratio"""
        if len(eyes) >= 2:
            # Simple blink detection based on eye aspect ratio
            eye1 = eyes[0]
            eye2 = eyes[1]
            
            # Calculate eye aspect ratio (simplified)
            def eye_aspect_ratio(eye):
                # eye: (x, y, w, h)
                return eye[3] / (eye[2] + 1e-6)  # height/width
                
            ear1 = eye_aspect_ratio(eye1)
            ear2 = eye_aspect_ratio(eye2)
            
            # If both eyes are closed (simplified)
            if ear1 < 0.2 and ear2 < 0.2:
                current_time = datetime.now()
                time_diff = (current_time - self.last_blink_time).total_seconds()
                
                if time_diff > 0.3:  # Prevent multiple detections for the same blink
                    self.blink_count += 1
                    self.last_blink_time = current_time
                    
        return self.blink_count
    
    def analyze_facial_expressions(self, frame, face_roi):
        """Analyze facial expressions for stress indicators"""
        # This is a simplified version - in a real app, use a proper model
        x, y, w, h = face_roi
        face_roi = frame[y:y+h, x:x+w]
        
        # Convert to grayscale and calculate image moments
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        moments = cv2.moments(cv2.Canny(gray, 100, 200))
        
        # Calculate stress score based on image moments (simplified)
        stress_score = min(100, (moments['mu20'] + moments['mu02']) / 1000)
        return stress_score
    
    def calculate_wellness_index(self, stress_score, fatigue_score):
        """Calculate overall wellness index (0-100)"""
        # Weighted average with stress having more impact
        wellness = 100 - (0.6 * stress_score + 0.4 * fatigue_score)
        return max(0, min(100, wellness))
    
    def analyze(self, frame):
        """Main analysis function"""
        # Initialize default results
        results = {
            'face_detected': False,
            'stress_score': 0,
            'fatigue_score': 0,
            'wellness_index': 100,
            'blink_count': 0,
            'eye_strain': 0
        }
        
        # Detect face
        face_detected, face_roi = self.detect_face(frame)
        results['face_detected'] = face_detected
        
        if face_detected:
            # Detect eyes
            eyes = self.detect_eyes(frame, face_roi)
            
            # Analyze eye strain and blinks
            results['eye_strain'] = self.analyze_eye_strain(eyes, 30)  # 30 frames buffer
            results['blink_count'] = self.detect_blinks(eyes, frame)
            
            # Calculate fatigue score based on eye metrics
            results['fatigue_score'] = min(100, results['eye_strain'] * 0.7 + 
                                         (30 - min(30, results['blink_count'])) * 0.3)
            
            # Analyze facial expressions for stress
            results['stress_score'] = self.analyze_facial_expressions(frame, face_roi)
            
            # Calculate overall wellness index
            results['wellness_index'] = self.calculate_wellness_index(
                results['stress_score'], results['fatigue_score'])
            
            # Add timestamp
            results['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        return results
