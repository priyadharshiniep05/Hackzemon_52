import time
from dataclasses import dataclass

import numpy as np
import pyaudio


@dataclass
class VoiceAnalysisResult:
    stress_score: int
    fatigue_score: int


class VoiceAnalyzer:
    """
    Records microphone audio and extracts simple features to estimate
    stress and fatigue heuristically using PyAudio + NumPy.
    """

    def __init__(self, rate: int = 16000, seconds: int = 5, chunk: int = 1024):
        self.rate = rate
        self.seconds = seconds
        self.chunk = chunk

    def _record(self) -> np.ndarray:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )
        frames = []
        try:
            total_chunks = int(self.rate / self.chunk * self.seconds)
            for _ in range(total_chunks):
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.int16))
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        audio = np.concatenate(frames) if frames else np.zeros(self.rate * self.seconds, dtype=np.int16)
        audio = audio.astype(np.float32) / 32768.0
        return audio

    def _frame_signal(self, x: np.ndarray, frame_len: int, hop: int) -> np.ndarray:
        if len(x) < frame_len:
            pad = np.zeros(frame_len - len(x), dtype=x.dtype)
            x = np.concatenate([x, pad])
        num = 1 + (len(x) - frame_len) // hop
        frames = np.lib.stride_tricks.as_strided(
            x,
            shape=(num, frame_len),
            strides=(x.strides[0] * hop, x.strides[0]),
            writeable=False,
        )
        return frames.copy()

    def _zcr(self, frames: np.ndarray) -> np.ndarray:
        signs = np.sign(frames)
        signs[signs == 0] = 1
        return (np.abs(np.diff(signs, axis=1)) > 0).mean(axis=1)

    def _rms(self, frames: np.ndarray) -> np.ndarray:
        return np.sqrt((frames**2).mean(axis=1) + 1e-12)

    def _estimate_pitch(self, frame: np.ndarray, rate: int, fmin: float = 50.0, fmax: float = 400.0) -> float:
        x = frame - frame.mean()
        if np.allclose(x, 0.0):
            return 0.0
        corr = np.correlate(x, x, mode='full')
        corr = corr[len(corr)//2:]
        max_lag = int(rate / fmin)
        min_lag = int(rate / fmax)
        if max_lag <= min_lag or max_lag >= len(corr):
            return 0.0
        segment = corr[min_lag:max_lag]
        lag = np.argmax(segment) + min_lag
        if lag <= 0:
            return 0.0
        freq = rate / lag
        return float(freq) if np.isfinite(freq) else 0.0

    def _extract_features(self, audio: np.ndarray) -> dict:
        frame_len = int(0.032 * self.rate)
        hop = int(0.010 * self.rate)
        frames = self._frame_signal(audio, frame_len, hop)

        window = np.hanning(frame_len).astype(np.float32)
        wframes = frames * window

        rms = self._rms(wframes)
        zcr = self._zcr(wframes)

        thr = 0.5 * np.median(rms)
        pause_ratio = float((rms < thr).mean())

        step = max(1, int(0.05 * self.rate // hop))
        pitches = []
        for i in range(0, wframes.shape[0], step):
            pitches.append(self._estimate_pitch(wframes[i], self.rate))
        pitches = np.array(pitches, dtype=np.float32)
        pitch_mean = float(np.mean(pitches[pitches > 0])) if np.any(pitches > 0) else 0.0
        pitch_std = float(np.std(pitches[pitches > 0])) if np.any(pitches > 0) else 0.0

        return {
            'rms_mean': float(rms.mean()),
            'rms_std': float(rms.std()),
            'zcr_mean': float(zcr.mean()),
            'pause_ratio': pause_ratio,
            'pitch_mean': pitch_mean,
            'pitch_std': pitch_std,
        }

    def _scale_0_100(self, x: float, lo: float, hi: float, invert: bool = False) -> float:
        if hi == lo:
            return 0.0
        t = (x - lo) / (hi - lo)
        t = max(0.0, min(1.0, t))
        return float(100.0 * (1.0 - t) if invert else 100.0 * t)

    def analyze(self) -> dict:
        audio = self._record()
        feats = self._extract_features(audio)

        s1 = self._scale_0_100(feats['zcr_mean'], 0.02, 0.25)
        s2 = self._scale_0_100(feats['pitch_std'], 0.0, 30.0)
        s3 = self._scale_0_100(feats['rms_std'], 0.0, 0.05)
        stress = 0.5 * s1 + 0.3 * s2 + 0.2 * s3

        f1 = self._scale_0_100(feats['rms_mean'], 0.02, 0.15, invert=True)
        f2 = self._scale_0_100(feats['pitch_mean'], 90.0, 220.0, invert=True)
        f3 = self._scale_0_100(feats['pause_ratio'], 0.05, 0.6)
        fatigue = 0.5 * f1 + 0.2 * f2 + 0.3 * f3

        return {
            'stress_score': int(round(max(0.0, min(100.0, stress)))),
            'fatigue_score': int(round(max(0.0, min(100.0, fatigue))))
        }

    def analyze_from_array(self, audio: np.ndarray, rate: int) -> dict:
        old_rate = self.rate
        try:
            self.rate = int(rate)
            feats = self._extract_features(audio.astype(np.float32))

            s1 = self._scale_0_100(feats['zcr_mean'], 0.02, 0.25)
            s2 = self._scale_0_100(feats['pitch_std'], 0.0, 30.0)
            s3 = self._scale_0_100(feats['rms_std'], 0.0, 0.05)
            stress = 0.5 * s1 + 0.3 * s2 + 0.2 * s3

            f1 = self._scale_0_100(feats['rms_mean'], 0.02, 0.15, invert=True)
            f2 = self._scale_0_100(feats['pitch_mean'], 90.0, 220.0, invert=True)
            f3 = self._scale_0_100(feats['pause_ratio'], 0.05, 0.6)
            fatigue = 0.5 * f1 + 0.2 * f2 + 0.3 * f3

            return {
                'stress_score': int(round(max(0.0, min(100.0, stress)))),
                'fatigue_score': int(round(max(0.0, min(100.0, fatigue))))
            }
        finally:
            self.rate = old_rate

