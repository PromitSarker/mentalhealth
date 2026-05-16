"""Simplified README - AI Therapy Platform"""

# 🏥 AI THERAPY PLATFORM - Minimal Backend

A lightweight FastAPI backend for AI therapy with risk detection, clinical scoring, and audio processing.

## ✨ Features

**Core Capabilities:**

- ✅ Chat with Gemini AI (therapy-focused)
- ✅ Real-time risk detection (self-harm/suicidal ideation)
- ✅ Speech-to-text (STT) conversion
- ✅ Text-to-speech (TTS) synthesis
- ✅ GAD-7 anxiety scoring (0-21)
- ✅ PHQ-9 depression scoring (0-27)
- ✅ Clinical recommendations

**What's Handled by Frontend/Backend:**

- Data storage & persistence
- User authentication
- Data encryption
- Session management
- Frontend UI

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Generative AI API key (free at makersuite.google.com)

### Setup (5 minutes)

```bash
# 1. Clone & enter directory
cd katemage

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env - add your GEMINI_API_KEY

# 5. Run server
python -m uvicorn app.main:app --reload

# 6. Visit documentation
# http://localhost:8000/docs
```

### Docker Setup

```bash
cp .env.example .env
# Edit .env - add your GEMINI_API_KEY
docker-compose up --build
# http://localhost:8000/docs
```

---

## 📡 API Endpoints (5 Total)

### Chat

```
POST /ai/chat/interact
Request: { "user_message": "I'm feeling anxious" }
Response: { "ai_response": "...", "risk_level": "low", "flagged_for_review": false }
```

### Audio

```
POST /ai/audio/stt
Request: { "audio_data": "base64_encoded_audio" }
Response: { "transcription": "...", "confidence": 0.95 }

POST /ai/audio/tts
Request: { "text": "Hello there", "voice": "en-GB-Neural2-A" }
Response: { "audio_data": "base64_encoded_audio" }

GET /ai/audio/voices
Response: Available voices for synthesis
```

### Clinical Reports

```
POST /ai/report/generate
Request: { "survey_responses": { "gad7_1": 2, "gad7_2": 1, ..., "phq9_1": 2, ... } }
Response: { "gad7_score": 12, "phq9_score": 8, "clinical_summary": "...", "recommended_next_steps": [...] }
```

### Health

```
GET /
GET /health
```

---

## 📁 Project Structure

```
katemage/
├── app/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Request/response schemas
│   └── routers/
│       ├── chat.py          # /ai/chat/interact
│       ├── audio.py         # /ai/audio/*
│       └── reports.py       # /ai/report/generate
│
├── services/
│   ├── gemini_service.py    # AI dialogue
│   ├── audio_service.py     # STT/TTS (mock)
│   └── scoring_service.py   # GAD-7/PHQ-9
│
├── utils/
│   ├── risk_detection.py    # Safety monitoring
│   └── encryption.py        # Key generation (removed from flow)
│
├── middleware/              # Removed (frontend handles)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔄 Basic Usage

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Chat interaction
response = requests.post(
    f"{BASE_URL}/ai/chat/interact",
    json={"user_message": "I feel anxious"}
)
print(response.json())
# Output: {
#   "ai_response": "...",
#   "risk_level": "low",
#   "flagged_for_review": false,
#   "timestamp": "2024-01-15T10:30:00"
# }

# Generate clinical report
response = requests.post(
    f"{BASE_URL}/ai/report/generate",
    json={
        "survey_responses": {
            "gad7_1": 2, "gad7_2": 2, "gad7_3": 1, "gad7_4": 3,
            "gad7_5": 2, "gad7_6": 1, "gad7_7": 2,
            "phq9_1": 2, "phq9_2": 1, "phq9_3": 2, "phq9_4": 0,
            "phq9_5": 1, "phq9_6": 1, "phq9_7": 2, "phq9_8": 1,
            "phq9_9": 0
        }
    }
)
print(response.json())
```

---

## 🎯 Risk Detection

The backend automatically scans for concerning content:

| Risk Level | Examples                  | Action                          |
| ---------- | ------------------------- | ------------------------------- |
| CRITICAL   | "suicide", "kill myself"  | Flag + send crisis support info |
| HIGH       | "hopeless", "want to die" | Flag + log                      |
| MEDIUM     | "sad", "depressed"        | Log                             |
| LOW        | Normal conversation       | No action                       |

**Crisis Support Message (Automatic):**

```
"Samaritans: 116 123 (24/7, free). Your safety is our priority."
```

---

## 📊 Clinical Scoring

### GAD-7 (Anxiety)

- 7 questions × 0-3 scale each
- Total: 0-21
- Severity: Minimal, Mild, Moderate, Severe

### PHQ-9 (Depression)

- 9 questions × 0-3 scale each
- Total: 0-27
- Severity: Minimal, Mild, Moderate, Moderately Severe, Severe

---

## 🔧 Configuration

See `.env.example`:

```
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-1.5-pro
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

---

## 📚 API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚠️ Important Notes

1. **Audio Processing**: STT/TTS endpoints return mock data. Integrate with Google Cloud Speech API in production.
2. **Risk Detection**: Keyword-based scanning. Consider adding ML model for production.
3. **Storage**: Backend doesn't store data. Frontend/backend handles all persistence.
4. **Authentication**: Not included. Implement in your backend.
5. **Validation**: Frontend/backend responsible for data validation beyond basic schemas.

---

## 🚢 Deployment

### Docker

```bash
docker-compose up --build
```

### Production

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📞 Troubleshooting

**"GEMINI_API_KEY not set"**

```bash
# Check .env file
cat .env

# Update GEMINI_API_KEY value
# Restart server
```

**"Port 8000 already in use"**

```bash
SERVER_PORT=8001 python -m uvicorn app.main:app --reload
```

---

## 📄 Files

- `requirements.txt` - Python dependencies (5 packages)
- `Dockerfile` - Container image
- `docker-compose.yml` - Multi-container setup
- `app/` - Application code (4 files)
- `services/` - Business logic (3 files)
- `utils/` - Utilities (2 files)

---

## 🎓 Next Steps

1. ✅ Run locally and test endpoints
2. ✅ Connect from frontend
3. ✅ Integrate Google Cloud APIs (STT/TTS production)
4. ✅ Add authentication in your backend
5. ✅ Deploy with Docker

---

**Version**: 1.0.0 | **Status**: Ready to Use 🚀
