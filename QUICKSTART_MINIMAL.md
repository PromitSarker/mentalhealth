"""MINIMAL QUICKSTART - AI Therapy Platform"""

# ⚡ AI Therapy Platform - Minimal Backend (5-Min Setup)

## Step 1: Install & Configure (2 min)

```bash
# Enter project directory
cd /home/Aether/Desktop/katemage

# Create & activate environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR on Windows:
# venv\Scripts\activate

# Install dependencies (only 5 packages!)
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your favorite editor
# Add: GEMINI_API_KEY=your_key_here_from_makersuite.google.com
```

## Step 2: Run Locally (1 min)

```bash
# Start server (automatically reloads on code changes)
python -m uvicorn app.main:app --reload

# Output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

Visit: **http://localhost:8000/docs** (interactive API documentation)

## Step 3: Test Endpoints (2 min)

### Test 1: Chat Interaction

```bash
curl -X POST http://localhost:8000/ai/chat/interact \
  -H "Content-Type: application/json" \
  -d '{"user_message": "I am feeling anxious"}'
```

**Response:**

```json
{
  "ai_response": "[AI therapy response]",
  "risk_level": "low",
  "flagged_for_review": false,
  "timestamp": "2024-01-15T10:30:00"
}
```

### Test 2: Clinical Scoring

```bash
curl -X POST http://localhost:8000/ai/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "survey_responses": {
      "gad7_1": 2, "gad7_2": 2, "gad7_3": 1, "gad7_4": 3,
      "gad7_5": 2, "gad7_6": 1, "gad7_7": 2,
      "phq9_1": 2, "phq9_2": 1, "phq9_3": 2, "phq9_4": 0,
      "phq9_5": 1, "phq9_6": 1, "phq9_7": 2, "phq9_8": 1,
      "phq9_9": 0
    }
  }'
```

**Response:**

```json
{
  "gad7_score": 14,
  "gad7_severity": "moderate",
  "phq9_score": 9,
  "phq9_severity": "mild",
  "clinical_summary": "...",
  "recommended_next_steps": [...]
}
```

### Test 3: Speech to Text

```bash
curl -X POST http://localhost:8000/ai/audio/stt \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_data",
    "language": "en-GB"
  }'
```

---

## 🐳 Docker Setup (Alternative, 1 min)

```bash
# Add API key to .env first
nano .env

# Run with Docker
docker-compose up --build

# Visit: http://localhost:8000/docs
```

---

## 📝 What's Included

**5 Endpoints:**

- `POST /ai/chat/interact` - Chat with Gemini AI + risk detection
- `POST /ai/audio/stt` - Speech to text conversion
- `POST /ai/audio/tts` - Text to speech synthesis
- `POST /ai/report/generate` - GAD-7/PHQ-9 clinical scoring
- `GET /ai/audio/voices` - List available voices
- `GET /health` - Server health check

**3 Core Services:**

1. **Gemini Service** - AI therapy dialogue
2. **Audio Service** - STT/TTS processing
3. **Scoring Service** - Clinical assessments

**2 Utilities:**

1. **Risk Detection** - Scan for harmful content
2. **Encryption** - Key generation utilities (not in API flow)

---

## 🚨 Risk Detection (Automatic)

Content is automatically analyzed for safety concerns:

```
Critical Risk: "suicide", "kill myself"
  → Automatically adds: "Samaritans: 116 123 (24/7, free)"

High Risk: "hopeless", "want to die"
  → Flagged for review

Medium Risk: "sad", "depressed"
  → Logged

Low Risk: Normal conversation
  → No action
```

---

## 🎯 Integration with Frontend

### Example: Frontend → Backend Flow

```javascript
// Frontend sends chat message
const response = await fetch("http://localhost:8000/ai/chat/interact", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_message: userInput,
  }),
});

const data = await response.json();
console.log(data.ai_response); // Display to user
console.log(data.risk_level); // Handle risk
console.log(data.flagged_for_review); // Alert admin if true
```

---

## 🐛 Troubleshooting

**Error: "GEMINI_API_KEY not set"**

```bash
# Check .env
cat .env

# Ensure GEMINI_API_KEY has a value
# Restart server
```

**Error: "Port 8000 already in use"**

```bash
# Use different port
python -m uvicorn app.main:app --reload --port 8001
```

**Error: Module not found**

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

---

## 📚 Learn More

- **Full Documentation**: `README_SIMPLIFIED.md`
- **API Docs (Live)**: http://localhost:8000/docs
- **ReDoc (Alternative)**: http://localhost:8000/redoc
- **Project Structure**: `INDEX.md`
- **Integration Examples**: `INTEGRATION.md`

---

## ✅ You're Set!

Your minimal AI therapy backend is ready to use:

- ✅ Chat endpoint with AI
- ✅ Risk detection
- ✅ Clinical scoring
- ✅ Audio processing
- ✅ Production-ready code

**Frontend handles:** Storage, encryption, authentication, UI

**Backend handles:** AI logic, risk analysis, scoring

---

**That's it! You're done. Start building! 🚀**
