import io
import sys
import wave
from pathlib import Path
import tempfile
import os

import numpy as np
from flask import Flask, request, render_template_string, jsonify

from voice_analyzer import VoiceAnalyzer
from wellness_calculator import WellnessCalculator
from recommendations import RecommendationEngine
from pydub import AudioSegment
import imageio_ffmpeg

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

app = Flask(__name__)

# Ensure pydub uses a working FFmpeg binary
try:
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    AudioSegment.converter = ffmpeg_path
    # Also set ffmpeg/ffprobe attributes to avoid PATH lookup
    AudioSegment.ffmpeg = ffmpeg_path
    AudioSegment.ffprobe = ffmpeg_path  # ffprobe may not be required; set to ffmpeg path as a fallback
except Exception:
    # Fallback to environment PATH discovery; upload of m4a may fail without FFmpeg
    pass

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Stress & Fatigue Analyzer</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 24px; max-width: 800px; margin: auto; }
    header { margin-bottom: 16px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 12px 0; }
    .result { background: #f7f7f7; }
    .muted { color: #666; }
    .bar { font-family: monospace; }
  </style>
</head>
<body>
  <header>
    <h1>🩺 Stress & Fatigue Analyzer (Web)</h1>
    <p class="muted">Upload a WAV file (mono or stereo, 16-bit PCM recommended). Recording length ~5s works best.</p>
  </header>

  <div class="card">
    <form method="POST" action="/analyze" enctype="multipart/form-data">
      <label>WAV file:</label>
      <input type="file" name="audio" accept="audio/wav,audio/x-wav,audio/m4a,audio/x-m4a,audio/mp4,audio/aac,audio/mpeg" required />
      <button type="submit">Analyze</button>
    </form>
  </div>

  {% if result %}
  <div class="card result">
    <h2>Results</h2>
    <p><strong>Wellness Index:</strong> {{ result.wellness.wellness_index }}/100 {{ result.wellness.indicator }}</p>
    <p><strong>Category:</strong> {{ result.wellness.category }}</p>
    <p><strong>Stress:</strong> {{ result.wellness.stress_score }}/100</p>
    <p><strong>Fatigue:</strong> {{ result.wellness.fatigue_score }}/100</p>

    <h3>Immediate Action ({{ result.reco.immediate_action.urgency }} Priority)</h3>
    <p>{{ result.reco.immediate_action.action }}</p>

    <h3>Recommendations</h3>
    <ul>
      {% for rec in result.reco.personalized_recommendations %}
      <li>{{ rec }}</li>
      {% endfor %}
    </ul>

    <h3>Breathing Exercise: {{ result.reco.breathing_exercise.name }}</h3>
    <ul>
      {% for step in result.reco.breathing_exercise.instructions %}
      <li>{{ step }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  <div class="card">
    <p class="muted">Tip: If your browser only exports WebM/OGG when recording, convert it to WAV before uploading.</p>
  </div>
</body>
</html>
"""

va = VoiceAnalyzer()
wc = WellnessCalculator()
re = RecommendationEngine()
wc.load_history()


def _read_audio_to_array(file_bytes: bytes, filename: str | None) -> tuple[np.ndarray, int]:
    # Try WAV first
    try:
        with wave.open(io.BytesIO(file_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
        if sampwidth != 2:
            raise ValueError("Only 16-bit PCM WAV is supported.")
        audio = np.frombuffer(raw, dtype=np.int16)
        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
        audio = (audio.astype(np.float32) / 32768.0).copy()
        return audio, int(framerate)
    except wave.Error:
        pass

    # Try direct ffmpeg pipe decode first (handles m4a/mp4/aac/alac if codecs available)
    ff_err = None
    try:
        import subprocess
        ffmpeg_bin = getattr(AudioSegment, 'ffmpeg', None) or imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_bin, '-hide_banner', '-loglevel', 'error', '-i', 'pipe:0', '-f', 's16le', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', 'pipe:1']
        proc = subprocess.run(cmd, input=file_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0 and proc.stdout:
            raw = proc.stdout
            samples = np.frombuffer(raw, dtype=np.int16)
            audio = (samples.astype(np.float32) / 32768.0).copy()
            return audio, 16000
        ff_err = proc.stderr.decode('utf-8', errors='ignore')
    except Exception as _e_ff:
        ff_err = repr(_e_ff)

    # Second fallback: write to a temp file to allow ffmpeg random access for some containers
    try:
        import subprocess
        ffmpeg_bin = getattr(AudioSegment, 'ffmpeg', None) or imageio_ffmpeg.get_ffmpeg_exe()
        ext = None
        if filename and '.' in filename:
            ext = filename.rsplit('.', 1)[-1].lower()
        suffix = f".{ext}" if ext else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as src:
            src.write(file_bytes)
            src.flush()
            src_path = src.name
        try:
            cmd = [ffmpeg_bin, '-hide_banner', '-loglevel', 'error', '-i', src_path, '-f', 's16le', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', 'pipe:1']
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0 and proc.stdout:
                raw = proc.stdout
                samples = np.frombuffer(raw, dtype=np.int16)
                audio = (samples.astype(np.float32) / 32768.0).copy()
                return audio, 16000
            else:
                if ff_err:
                    ff_err += "\n" + proc.stderr.decode('utf-8', errors='ignore')
                else:
                    ff_err = proc.stderr.decode('utf-8', errors='ignore')
        finally:
            try:
                os.unlink(src_path)
            except Exception:
                pass
    except Exception as _e_ff_file:
        ff_err = (ff_err or "") + f"\nfile-decode-fallback: {_e_ff_file!r}"

    # Fallback: use pydub/ffmpeg for formats like m4a, mp4, aac, mp3
    # Detect format from filename extension when possible
    fmt = None
    if filename and "." in filename:
        fmt = filename.rsplit(".", 1)[-1].lower()
    try:
        audio_seg = AudioSegment.from_file(io.BytesIO(file_bytes), format=fmt)
    except Exception as e2:
        detail = ff_err or str(e2)
        raise ValueError(f"Unsupported or unreadable audio file. File: {filename!r}. Decoder detail: {detail}") from e2

    # Convert to mono, 16kHz float32 array
    audio_seg = audio_seg.set_channels(1).set_frame_rate(16000)
    samples = np.array(audio_seg.get_array_of_samples(), dtype=np.int16)
    audio = (samples.astype(np.float32) / 32768.0).copy()
    return audio, 16000


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "audio" not in request.files:
        return jsonify({"error": "No file uploaded with field name 'audio'."}), 400
    f = request.files["audio"]
    data = f.read()
    try:
        audio, rate = _read_audio_to_array(data, f.filename)
        voice = va.analyze_from_array(audio, rate)
        wellness = wc.analyze_complete(voice["stress_score"], voice["fatigue_score"])
        reco = re.generate_report(wellness)
        return render_template_string(HTML, result={"wellness": wellness, "reco": reco})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5003, debug=False)
