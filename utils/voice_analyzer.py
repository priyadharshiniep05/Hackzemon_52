import numpy as np
import librosa
import soundfile as sf
import os
from datetime import datetime

class VoiceAnalyzer:
    def __init__(self):
        # Initialize parameters
        self.sample_rate = 16000  # Hz
        self.frame_length = 0.025  # 25ms
        self.hop_length = 0.010    # 10ms
        self.n_fft = 512
        
        # Stress and fatigue thresholds (can be adjusted)
        self.stress_thresholds = {
            'pitch_range': (100, 300),  # Hz
            'jitter_threshold': 0.04,   # 4%
            'shimmer_threshold': 0.15,  # 15%
            'hfd_threshold': 2.5        # Higher order spectral feature
        }
        
        self.fatigue_thresholds = {
            'speech_rate': (3, 5),      # Syllables per second
            'pause_ratio': 0.2,         # 20% of speech is pauses
            'h1_h2': 12.0,              # Glottal source feature
            'cpcs': 0.6                 # Cepstral peak prominence (smoothed)
        }
    
    def load_audio(self, audio_path):
        """Load audio file using librosa"""
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            return y, sr
        except Exception as e:
            print(f"Error loading audio: {e}")
            return None, None
    
    def extract_features(self, y):
        """Extract audio features for stress and fatigue analysis"""
        features = {}
        
        # Basic features
        features['rms'] = np.sqrt(np.mean(y**2))
        features['zcr'] = np.mean(librosa.feature.zero_crossing_rate(y, frame_length=2048, hop_length=512))
        
        # Spectral features
        S = np.abs(librosa.stft(y, n_fft=2048))**2
        spectral_centroid = librosa.feature.spectral_centroid(S=S).mean()
        spectral_bandwidth = librosa.feature.spectral_bandwidth(S=S).mean()
        
        # Pitch and jitter (pitch perturbations)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), 
                                        fmax=librosa.note_to_hz('C7'),
                                        sr=self.sample_rate)
        f0 = f0[voiced_flag]
        
        if len(f0) > 1:
            jitter = np.mean(np.abs(np.diff(f0))) / np.mean(f0)
            pitch_range = np.max(f0) - np.min(f0)
        else:
            jitter = 0
            pitch_range = 0
        
        # Shimmer (amplitude perturbations)
        rms_energy = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        if len(rms_energy) > 1:
            shimmer = np.mean(np.abs(np.diff(rms_energy))) / np.mean(rms_energy)
        else:
            shimmer = 0
        
        # Speech rate estimation (syllables per second)
        # This is a simplified version - in practice, use a proper speech recognizer
        speech_rate = len(librosa.onset.onset_detect(y=y, sr=self.sample_rate)) / (len(y) / self.sample_rate)
        
        # Pause ratio (silence ratio)
        y_harmonic = librosa.effects.harmonic(y)
        energy = np.abs(librosa.stft(y_harmonic, n_fft=2048, hop_length=512))**2
        energy_db = librosa.power_to_db(energy, ref=np.max)
        silence_ratio = np.mean(energy_db < -40)  # Threshold for silence
        
        # Update features
        features.update({
            'spectral_centroid': spectral_centroid,
            'spectral_bandwidth': spectral_bandwidth,
            'jitter': jitter,
            'shimmer': shimmer,
            'pitch_range': pitch_range,
            'speech_rate': speech_rate,
            'silence_ratio': silence_ratio,
            'f0_mean': np.mean(f0) if len(f0) > 0 else 0
        })
        
        return features
    
    def calculate_stress_score(self, features):
        """Calculate stress score based on voice features"""
        stress_score = 0
        
        # Pitch-related stress indicators
        if features['pitch_range'] > 0:
            pitch_stress = min(1.0, features['pitch_range'] / 200)  # Normalize to 0-1
            stress_score += pitch_stress * 30  # Up to 30 points
        
        # Jitter and shimmer (voice quality)
        jitter_stress = min(1.0, features['jitter'] / self.stress_thresholds['jitter_threshold'])
        shimmer_stress = min(1.0, features['shimmer'] / self.stress_thresholds['shimmer_threshold'])
        
        stress_score += jitter_stress * 25  # Up to 25 points
        stress_score += shimmer_stress * 25  # Up to 25 points
        
        # Spectral features
        spectral_stress = min(1.0, features['spectral_centroid'] / 2000)  # Normalize
        stress_score += spectral_stress * 20  # Up to 20 points
        
        return min(100, stress_score)
    
    def calculate_fatigue_score(self, features):
        """Calculate fatigue score based on voice features"""
        fatigue_score = 0
        
        # Speech rate (slower speech may indicate fatigue)
        min_rate, max_rate = self.fatigue_thresholds['speech_rate']
        if features['speech_rate'] < min_rate:
            fatigue_score += (1 - features['speech_rate'] / min_rate) * 30  # Up to 30 points
        
        # Pause ratio (more pauses may indicate fatigue)
        pause_ratio = min(1.0, features['silence_ratio'] / self.fatigue_thresholds['pause_ratio'])
        fatigue_score += pause_ratio * 40  # Up to 40 points
        
        # Pitch range (reduced range may indicate fatigue)
        if features['pitch_range'] > 0:
            pitch_fatigue = 1 - min(1.0, features['pitch_range'] / 150)  # Normalize
            fatigue_score += pitch_fatigue * 30  # Up to 30 points
        
        return min(100, fatigue_score)
    
    def calculate_wellness_index(self, stress_score, fatigue_score):
        """Calculate overall wellness index (0-100)"""
        # Weighted average with stress having more impact
        wellness = 100 - (0.6 * stress_score + 0.4 * fatigue_score)
        return max(0, min(100, wellness))
    
    def analyze_audio(self, audio_path):
        """Main analysis function"""
        # Load audio
        y, sr = self.load_audio(audio_path)
        if y is None:
            return {
                'error': 'Failed to load audio',
                'stress_score': 0,
                'fatigue_score': 0,
                'wellness_index': 0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Extract features
        features = self.extract_features(y)
        
        # Calculate scores
        stress_score = self.calculate_stress_score(features)
        fatigue_score = self.calculate_fatigue_score(features)
        wellness_index = self.calculate_wellness_index(stress_score, fatigue_score)
        
        # Prepare results
        results = {
            'stress_score': float(stress_score),
            'fatigue_score': float(fatigue_score),
            'wellness_index': float(wellness_index),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'features': {
                'pitch_range': float(features.get('pitch_range', 0)),
                'jitter': float(features.get('jitter', 0)),
                'shimmer': float(features.get('shimmer', 0)),
                'speech_rate': float(features.get('speech_rate', 0)),
                'silence_ratio': float(features.get('silence_ratio', 0))
            }
        }
        
        return results
