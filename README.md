# AI Wellness Monitor

A real-time wellness monitoring system that uses computer vision to analyze facial expressions and provide wellness index scores for stress and fatigue levels.

## Features

- Real-time face detection and analysis
- Wellness Index (WI) calculation (0-100)
- Stress and fatigue level monitoring
- Blink rate detection
- Personalized wellness recommendations
- Responsive web interface
- Real-time alerts and notifications

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Webcam
- Google Chrome or Firefox (for best experience)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wellness-monitor.git
   cd wellness-monitor
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your web browser**
   Navigate to `http://localhost:5000`

3. **Grant camera permissions**
   Allow the browser to access your webcam when prompted

## How It Works

1. The system uses MediaPipe Face Mesh to detect facial landmarks
2. It analyzes eye movement, blink rate, and other facial features
3. Based on the analysis, it calculates:
   - Wellness Index (0-100)
   - Stress level
   - Fatigue level
   - Blink rate
4. The system provides real-time feedback and recommendations

## Wellness Index Guide

| WI Range      | Risk Level         | Recommendation |
|--------------|-------------------|----------------|
| 0 - 40      | CRITICAL/HIGH RISK | 🚨 Immediate Rest Alert |
| 41 - 65     | MEDIUM RISK       | 💧 Hydration & Mindful Break |
| 66 - 85     | LOW/MODERATE RISK | 🧘 Micro-Break/Stretch |
| 86 - 100    | LOW RISK          | ✅ All Good |

## Project Structure

```
wellness-monitor/
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── static/              
│   ├── css/             # Custom styles (if any)
│   └── js/              # Frontend JavaScript (if any)
└── templates/
    └── index.html       # Main HTML template
```

## Troubleshooting

1. **Webcam not working**
   - Ensure no other application is using the webcam
   - Check browser permissions for camera access
   - Try a different browser (Chrome/Firefox recommended)

2. **Dependency installation issues**
   - Make sure you have the latest version of pip: `pip install --upgrade pip`
   - Try installing dependencies one by one if needed

3. **Performance issues**
   - Close other applications using the webcam
   - Reduce browser tab usage while the application is running
   - Ensure good lighting conditions for better face detection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask, OpenCV, and MediaPipe
- Inspired by digital wellness applications
- Icons by Font Awesome
