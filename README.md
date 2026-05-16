# AI Therapy Platform - UK GDPR Compliant Backend

Production-ready FastAPI backend for an AI-powered therapy platform with UK GDPR compliance, Gemini API integration, and clinical assessment features.

## Features

### 🔒 Security & Compliance

- **GDPR Compliance**: Right-to-be-forgotten (Article 17), data export (Article 15)
- **AES-256 Encryption**: Data at rest encryption for sensitive information
- **TLS/HTTPS**: Enforced transport security with security headers
- **UK Data Residency**: Configured for UK-based deployment
- **Audit Logging**: Complete audit trail for insurance transparency
- **Input Validation**: Protection against injection attacks

### 🤖 AI Capabilities

- **Gemini API Integration**: Therapy-focused dialogue with safety guardrails
- **High-Risk Detection**: Scans for self-harm and suicidal ideation
- **Response Validation**: Ensures AI responses meet clinical guidelines
- **Safety Messaging**: Automatic crisis support information

### 🎙️ Audio Features

- **Speech-to-Text (STT)**: Voice input with UK English support (en-GB)
- **Text-to-Speech (TTS)**: Natural-sounding voice synthesis
- **Multiple Languages**: Extensible language support

### 📊 Clinical Assessments

- **GAD-7 Scoring**: Generalized Anxiety Disorder assessment (0-21)
- **PHQ-9 Scoring**: Depression severity assessment (0-27)
- **Clinical Summary**: Auto-generated professional reports
- **Recommendations**: Evidence-based next steps for patients

## Project Structure

```
katemage/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   └── routers/
│       ├── chat.py          # Chat endpoints
│       ├── audio.py         # Audio (STT/TTS) endpoints
│       └── reports.py       # Clinical report endpoints
├── services/
│   ├── gemini_service.py    # Gemini API wrapper
│   ├── audio_service.py     # Audio processing (STT/TTS)
│   ├── scoring_service.py   # GAD-7/PHQ-9 scoring
│   └── gdpr_service.py      # GDPR compliance service
├── middleware/
│   ├── security.py          # Security headers, rate limiting
│   ├── logging.py           # Request/response logging
│   └── gdpr.py              # GDPR middleware
├── utils/
│   ├── encryption.py        # AES-256 encryption
│   ├── risk_detection.py    # High-risk content detection
│   └── validators.py        # Input validation helpers
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-container orchestration
├── requirements.txt         # Python dependencies
└── .env.example            # Environment configuration template
```

## API Endpoints

### Chat Interaction

- **POST** `/ai/chat/interact` - Therapy dialogue with risk detection
- **POST** `/ai/chat/session-start` - Initialize secure session
- **POST** `/ai/chat/session-end` - Terminate session

### Audio Processing

- **POST** `/ai/audio/stt` - Speech-to-text transcription
- **POST** `/ai/audio/tts` - Text-to-speech synthesis
- **GET** `/ai/audio/voices` - List available TTS voices

### Clinical Reports

- **POST** `/ai/report/generate` - Generate GAD-7/PHQ-9 report with audit trail
- **POST** `/ai/gdpr/delete` - Right-to-be-forgotten request
- **POST** `/ai/gdpr/export` - Data export (GDPR Article 15)

### Health & Status

- **GET** `/` - API information
- **GET** `/health` - Health check endpoint

## Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Generative AI API key (Gemini)

### Environment Configuration

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Configure environment variables:

```bash
# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# Security
ENCRYPTION_KEY=your_32_byte_hex_key  # Generate with: python -c "from utils.encryption import EncryptionManager; print(EncryptionManager.generate_key())"

# GDPR
DATA_RETENTION_DAYS=365
ENABLE_GDPR_AUDIT_LOG=true
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API at `http://localhost:8000` and docs at `http://localhost:8000/docs`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Check container health
docker-compose ps
```

The application will be available at `http://localhost:8000`

## Security Considerations

### Data at Rest

- Sensitive data encrypted with AES-256 (Fernet)
- Encryption keys managed via environment variables
- No sensitive data logged

### Data in Transit

- TLS/HTTPS enforced
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, CSP

### Access Control

- CORS configured for approved origins only
- Rate limiting on sensitive endpoints
- Input validation and injection protection

### GDPR Compliance

- Right-to-be-forgotten: Complete user data deletion
- Data export: Machine-readable format export
- Data retention: Automatic deletion after 365 days (configurable)
- Audit logging: All sensitive operations tracked

## High-Risk Detection

The platform detects and flags concerning content:

### Critical Keywords

- Suicidal ideation: "suicide", "kill myself", "hang myself", etc.
- Self-harm: "cut myself", "self harm", "hurt myself"

### Risk Levels

- **CRITICAL**: Immediate safety concern, flag for review
- **HIGH**: Multiple risk indicators
- **MEDIUM**: Some concerning language
- **LOW**: Routine conversation

### Automatic Responses

Users receive appropriate crisis support information:

- Samaritans: 116 123 (24/7, free)
- Professional mental health resources

## Clinical Scoring

### GAD-7 (Generalized Anxiety Disorder)

- 7 items × 0-3 scale = 0-21 total
- Severity: Minimal (0-4), Mild (5-9), Moderate (10-14), Severe (15-21)

### PHQ-9 (Patient Health Questionnaire)

- 9 items × 0-3 scale = 0-27 total
- Severity: Minimal (0-4), Mild (5-9), Moderate (10-14), Moderately Severe (15-19), Severe (20-27)

## Logging & Monitoring

### Log Levels

- **INFO**: Standard operations and API calls
- **WARNING**: Audit events, GDPR operations, high-risk content
- **ERROR**: Application errors and exceptions

### Audit Trail

- All clinical reports generation
- GDPR deletion requests
- Data exports
- High-risk content flagging

## Testing

```bash
# Run with pytest (recommended)
pytest tests/

# Manual endpoint testing
curl -X POST http://localhost:8000/ai/chat/interact \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-session","user_message":"I am feeling anxious","user_id":"user-123"}'
```

## Production Deployment

### Recommendations

1. Use PostgreSQL instead of SQLite for production
2. Deploy with Gunicorn and Nginx reverse proxy
3. Use AWS Secrets Manager or similar for encryption keys
4. Enable CloudWatch or similar logging
5. Set up automated backups
6. Use AWS RDS or managed PostgreSQL
7. Enable VPC and security groups
8. Implement API Gateway for rate limiting
9. Use CloudFront for DDoS protection
10. Enable GDPR compliance audit logs to S3

### Example Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name therapy.example.co.uk;

    ssl_certificate /etc/letsencrypt/live/therapy.example.co.uk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/therapy.example.co.uk/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Licensing

MIT License - See LICENSE file for details

## Support & Compliance

For GDPR compliance questions or clinical guidance:

- Contact: compliance@therapy-platform.co.uk
- Mental health crisis: Samaritans 116 123 (UK)
- UK ICO (GDPR): https://ico.org.uk/

## Changelog

### v1.0.0 (Initial Release)

- Gemini API integration
- GAD-7/PHQ-9 clinical scoring
- GDPR compliance framework
- High-risk detection
- Audio (STT/TTS) endpoints
- Docker containerization
- UK production-ready configuration
