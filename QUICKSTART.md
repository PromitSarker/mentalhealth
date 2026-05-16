"""Quick Start Guide - AI Therapy Platform"""

# AI THERAPY PLATFORM - QUICK START GUIDE

## 5-Minute Setup

### Prerequisites

- Python 3.11+ or Docker
- Google Generative AI API key (free at makersuite.google.com)

### Option 1: Local Python Development

```bash
# 1. Clone repository
cd katemage

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to ENCRYPTION_KEY in .env

# 6. Run application
python -m uvicorn app.main:app --reload

# 7. Visit API
# - API Docs: http://localhost:8000/docs
# - Redoc: http://localhost:8000/redoc
```

### Option 2: Docker Deployment

```bash
# 1. Clone repository
cd katemage

# 2. Setup environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 3. Generate encryption key
docker run -it python:3.11 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add to .env as ENCRYPTION_KEY

# 4. Build and run
docker-compose up --build

# 5. Check health
curl http://localhost:8000/health

# 6. Access API
# - API Docs: http://localhost:8000/docs
```

## First Request Example

### Start a Chat Session

```bash
curl -X POST http://localhost:8000/ai/chat/session-start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-123-anonymized"}'
```

**Response**:

```json
{
  "session_id": "encrypted_session_id_here",
  "initialized_at": "2024-01-15T10:30:00",
  "message": "Session started. Please share what's on your mind."
}
```

### Send a Chat Message

```bash
curl -X POST http://localhost:8000/ai/chat/interact \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "encrypted_session_id_here",
    "user_message": "I've been feeling anxious lately",
    "user_id": "user-123-anonymized"
  }'
```

**Response**:

```json
{
  "session_id": "encrypted_session_id_here",
  "ai_response": "[AI therapy response here]",
  "risk_level": "low",
  "timestamp": "2024-01-15T10:31:00",
  "flagged_for_review": false
}
```

## API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

#### Chat

- `POST /ai/chat/session-start` - Initialize session
- `POST /ai/chat/interact` - Send message, get response
- `POST /ai/chat/session-end` - End session

#### Audio

- `POST /ai/audio/stt` - Speech to text
- `POST /ai/audio/tts` - Text to speech
- `GET /ai/audio/voices` - List voices

#### Reports & GDPR

- `POST /ai/report/generate` - Generate GAD-7/PHQ-9 report
- `POST /ai/gdpr/delete` - Delete user data (GDPR Article 17)
- `POST /ai/gdpr/export` - Export user data (GDPR Article 15)

#### Health

- `GET /` - API info
- `GET /health` - Health check

## Development Workflow

### Running Tests

```bash
# Using pytest (add to requirements.txt first)
pytest tests/

# Manual testing with curl
curl http://localhost:8000/health
```

### Viewing Logs

```bash
# Docker logs
docker-compose logs -f therapy-platform

# Local development
# Check console output or check logs/ directory
```

### Debugging

**Enable Debug Mode**:

```bash
# In .env
DEBUG=true

# Restart application
# Now you'll get full error traces in API responses
```

**Check Configuration**:

```bash
python -c "from app.dependencies import get_settings; print(get_settings())"
```

## Troubleshooting

### "GEMINI_API_KEY not set"

```bash
# Check environment variable
echo $GEMINI_API_KEY

# If empty, update .env file
# Then restart application
```

### "Invalid audio data"

- Audio file size exceeds 10MB limit
- Audio format not supported (use MP3, WAV, or FLAC)
- Solution: Compress audio or use supported format

### "Database locked"

- SQLite issue with concurrent writes (development only)
- Solution: Switch to PostgreSQL for production
- Edit DATABASE_URL in .env

### Port 8000 already in use

```bash
# Find process using port
lsof -i :8000

# Kill process or use different port
SERVER_PORT=8001 python -m uvicorn app.main:app
```

## Production Checklist

Before deploying to production:

- [ ] Set `DEBUG=false`
- [ ] Update `ALLOWED_ORIGINS` with real domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong encryption key (32+ bytes)
- [ ] Configure AWS Secrets Manager
- [ ] Enable GDPR audit logging
- [ ] Setup TLS/SSL certificates
- [ ] Configure backup strategy
- [ ] Setup monitoring and alerts
- [ ] Create incident response plan
- [ ] Run security testing (OWASP ZAP)
- [ ] Get GDPR compliance review
- [ ] Enable rate limiting
- [ ] Setup error tracking (Sentry)
- [ ] Create runbook for operations team

## Example: Complete User Journey

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
USER_ID="user-example-123"

# 1. Start session
SESSION=$(curl -s -X POST $BASE_URL/ai/chat/session-start \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\"}" | jq -r '.session_id')

echo "Session: $SESSION"

# 2. First message
curl -s -X POST $BASE_URL/ai/chat/interact \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\":\"$SESSION\",
    \"user_message\":\"I'm struggling with anxiety\",
    \"user_id\":\"$USER_ID\"
  }" | jq '.ai_response'

# 3. Second message
curl -s -X POST $BASE_URL/ai/chat/interact \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\":\"$SESSION\",
    \"user_message\":\"Can you suggest some coping strategies?\",
    \"user_id\":\"$USER_ID\"
  }" | jq '.ai_response'

# 4. Generate report
curl -s -X POST $BASE_URL/ai/report/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\":\"$SESSION\",
    \"user_id\":\"$USER_ID\",
    \"survey_responses\":{
      \"gad7_1\":2,\"gad7_2\":2,\"gad7_3\":1,\"gad7_4\":3,\"gad7_5\":2,\"gad7_6\":1,\"gad7_7\":2,
      \"phq9_1\":2,\"phq9_2\":1,\"phq9_3\":2,\"phq9_4\":0,\"phq9_5\":1,\"phq9_6\":1,\"phq9_7\":2,\"phq9_8\":1,\"phq9_9\":0
    }
  }" | jq '.recommended_next_steps'

# 5. End session
curl -s -X POST $BASE_URL/ai/chat/session-end \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\"}" | jq '.message'
```

## Getting Help

- **API Issues**: Check `/docs` for endpoint documentation
- **Security Questions**: See SECURITY_COMPLIANCE.md
- **Integration Help**: See INTEGRATION.md for Python client examples
- **GDPR Questions**: See README.md for compliance info

## Next Steps

1. **Setup Frontend**: Create React/Vue interface using INTEGRATION.md examples
2. **Database Migration**: Switch from SQLite to PostgreSQL
3. **Analytics**: Add user engagement tracking (privacy-compliant)
4. **Admin Dashboard**: Create clinician review interface
5. **Mobile App**: Build iOS/Android app with offline support
6. **Integration**: Connect with NHS systems or EHR platforms

---

**Happy coding! The platform is ready for development.** 🚀
