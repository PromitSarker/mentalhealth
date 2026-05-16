"""Security & Compliance Architecture Documentation."""

"""

# AI THERAPY PLATFORM - SECURITY & GDPR COMPLIANCE ARCHITECTURE

## Overview

This document outlines the security controls and GDPR compliance mechanisms
implemented in the AI Therapy Platform. The platform is designed for UK GDPR
compliance (UK GDPR 2018) and healthcare data protection standards.

## 1. GDPR COMPLIANCE FRAMEWORK

### 1.1 Lawful Basis for Processing

- User Consent: Explicit, granular consent collected at registration
- Performance of Contract: Terms of service agreement
- Legitimate Interest: Platform operation and user safety

### 1.2 Right to be Forgotten (Article 17)

**Implementation**: `/ai/gdpr/delete` endpoint

Process:

1. User initiates deletion request (web/app interface)
2. API receives GDPRDeleteRequest with user_id and optional reason
3. gdpr_service.request_data_deletion() queues async deletion job
4. System deletes:
   - User profile and metadata
   - All session records
   - Encrypted conversation history
   - Assessment scores and reports
   - Audio recordings and transcriptions
   - Authentication tokens and sessions
5. Audit log entry created before deletion
6. Deletion confirmation sent to user
7. Deletion completes within 30 days (UK GDPR requirement)

**Data Retention After Deletion**: None (complete removal)

### 1.3 Right of Access (Article 15)

**Implementation**: `/ai/gdpr/export` endpoint

Provides users with complete data export including:

- User profile information
- All conversation history
- Assessment results
- Audio recordings metadata
- Processing activity logs
- Format: JSON (machine-readable)

### 1.4 Data Portability (Article 20)

Data export format supports transition to other platforms:

- Open JSON format
- No proprietary formats
- Includes all derivatives and processed data

### 1.5 Privacy by Design

**Principles Implemented**:

a) **Data Minimization**

- Collect only necessary data (message, timestamp, risk level)
- No tracking of user behavior beyond therapy sessions
- No third-party analytics integration

b) **Purpose Limitation**

- Data used only for:
  - Therapy dialogue provision
  - Clinical assessment scoring
  - Safety monitoring (risk detection)
  - Compliance and audit trails

c) **Storage Limitation**

- Configurable retention period (default: 365 days)
- Auto-deletion via retention_policy job
- Backup deletion: 90-day retention

d) **Integrity & Confidentiality**

- AES-256 encryption at rest
- TLS 1.2+ in transit
- Encrypted database fields
- Access logs and monitoring

## 2. SECURITY ARCHITECTURE

### 2.1 Encryption

#### At Rest (Storage)

- **Algorithm**: AES-256 (Fernet)
- **Key Management**: Environment variable stored in secrets manager
- **Fields Encrypted**:
  - Conversation history
  - User messages
  - Audio data (metadata)
  - Assessment results
  - Personal identifiable information

**Implementation** (`utils/encryption.py`):

```python
from cryptography.fernet import Fernet

# Key is 256-bit, base64-encoded
key = urlsafe_b64encode(sha256(key_material).digest())
cipher = Fernet(key)
encrypted = cipher.encrypt(data.encode())
```

#### In Transit (Network)

- **Protocol**: TLS 1.2 minimum (TLS 1.3 recommended)
- **Configuration**: Nginx reverse proxy or AWS ALB with SSL termination
- **Certificate**: Let's Encrypt or AWS Certificate Manager
- **Enforcement**: HSTS header, redirect HTTP→HTTPS

**Security Headers** (middleware/security.py):

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### 2.2 Authentication & Authorization

**Current Implementation**:

- Session-based with encrypted session IDs
- User consent validation middleware

**Production Recommendations**:

- JWT tokens with RS256 signing
- OAuth 2.0 for third-party integrations
- RBAC (Role-Based Access Control) for admin functions
- Multi-Factor Authentication (MFA) for sensitive operations

### 2.3 Input Validation

**Multi-Layer Validation**:

1. **Schema Validation** (Pydantic models)
   - Type checking
   - Range validation (e.g., GAD-7 scores 0-3)
   - Length constraints

2. **Injection Prevention** (InputValidationMiddleware)
   - SQL injection detection
   - XSS pattern detection
   - Command injection prevention

3. **Sanitization** (utils/validators.py)
   - Remove null bytes
   - Strip control characters
   - Truncate oversized inputs
   - Normalize unicode

### 2.4 Rate Limiting

**Implementation**: RateLimitMiddleware

- Default: 60 requests/minute per client
- Production: Configure per endpoint
- Redis recommended for distributed deployments

**Example for sensitive endpoints**:

```
/ai/chat/interact: 20 requests/minute
/ai/gdpr/delete: 1 request/minute
/ai/report/generate: 10 requests/minute
```

### 2.5 Access Control

**CORS Configuration**:

- Whitelist approved origins (localhost:3000, therapy-platform.co.uk)
- Restrict methods: GET, POST (no OPTIONS in production)
- No credentials exposure

**API Key Management** (Future):

- API keys stored in secrets manager
- Rotation every 90 days
- Rate limiting per API key
- Audit all API key usage

## 3. HIGH-RISK DETECTION & AI SAFETY

### 3.1 Risk Detection Engine (utils/risk_detection.py)

**Detection Mechanism**:

```
User Input → Risk Analysis → Risk Level → Action Trigger
                  ↓
        CRITICAL: Flag, Safety Message
              ↓
        HIGH:    Safety Message + Log
              ↓
        MEDIUM:  Log Entry
              ↓
        LOW:     No Action
```

**Risk Levels**:

| Level    | Keywords       | Action                           |
| -------- | -------------- | -------------------------------- |
| CRITICAL | suicide, hang  | Immediate alert + safety message |
| HIGH     | hopeless, die  | Flag + safety message + log      |
| MEDIUM   | sad, depressed | Log only                         |
| LOW      | normal         | No action                        |

**Keywords Database** (utils/risk_detection.py):

Critical Keywords:

- "suicide", "kill myself", "end my life"
- "hang myself", "overdose", "cut myself"
- "hurt myself", "self harm", "noose"

High Risk Keywords:

- "hopeless", "worthless", "better off dead"
- "want to die", "give up", "trapped"

### 3.2 Safety Messaging

**Auto-Generated Crisis Support**:

```
CRITICAL: "I've detected concerning content.
Samaritans: 116 123 (24/7, free). Your safety is our priority."

HIGH: "I'm concerned. Please contact a mental health professional.
Samaritans: 116 123"

MEDIUM: "I notice you're struggling. Professional support can help."
```

### 3.3 Response Validation

All Gemini API responses validated for:

- No medical prescriptions ("I can prescribe...")
- No diagnoses ("You have...")
- No dangerous advice
- Adherence to therapy guidelines

## 4. AUDIT & COMPLIANCE LOGGING

### 4.1 Audit Trail (middleware/logging.py)

**Events Logged**:

- Chat interactions (session_id, timestamp, risk_level)
- Clinical reports generated (user_id, scores, audit_timestamp)
- GDPR deletion requests (user_id, reason, timestamp)
- Data exports (user_id, export_timestamp)
- Risk detection events (session_id, risk_level, keywords)

**Log Format**:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "CHAT_INTERACT",
  "session_id": "encrypted_id",
  "risk_level": "MEDIUM",
  "user_id": "anonymized_id"
}
```

**Retention**: 7 years (UK healthcare records retention requirement)
**Storage**: Encrypted logs on S3 or Splunk

### 4.2 Incident Response

**High-Risk Detection Protocol**:

1. Real-time alert to clinical team (email/Slack webhook)
2. Flag recorded in audit log
3. User receives safety message
4. Manual review queued for clinician
5. Follow-up contact attempted (if contact details available)

## 5. DEPLOYMENT SECURITY

### 5.1 Container Security

**Docker Best Practices**:

- Non-root user (UID 1000)
- Read-only filesystem where possible
- No secrets in image (use secrets manager)
- Health checks enabled
- Resource limits enforced

### 5.2 Network Security

**Recommended Architecture**:

```
Internet → CloudFront (DDoS protection)
        ↓
      ALB (SSL termination, WAF)
        ↓
    Private Subnet
        ↓
   Therapy Platform
   (ECS/Kubernetes)
        ↓
    Private RDS
   (PostgreSQL)
```

### 5.3 Database Security

**SQLite** (Development):

- File encrypted with AES-256
- Located outside web root
- Daily backups

**PostgreSQL** (Production):

- Encryption at rest (AWS RDS encryption)
- SSL connection required
- Network in private subnet
- RDS Proxy for connection pooling
- Automated backups with 30-day retention

### 5.4 Secrets Management

**AWS Secrets Manager**:

```
/therapy-platform/prod/gemini-api-key
/therapy-platform/prod/encryption-key
/therapy-platform/prod/db-password
/therapy-platform/prod/jwt-signing-key
```

**Rotation Policy**:

- API keys: 90 days
- Database passwords: 90 days
- Encryption keys: Annual (with key rotation)
- Access reviewed quarterly

## 6. COMPLIANCE CHECKLIST

### UK GDPR Requirements

- [x] Privacy Policy (separate, external document)
- [x] Privacy Notice (displayed on registration)
- [x] Lawful basis for processing
- [x] Data Processing Agreement (for services)
- [x] Right to access (Article 15)
- [x] Right to erasure (Article 17)
- [x] Right to portability (Article 20)
- [x] Data retention policy
- [x] Privacy by design implementation
- [x] Audit logging (Article 32)

### UK Healthcare Data Standards

- [x] Confidentiality (encryption)
- [x] Integrity (audit logs)
- [x] Availability (backup/recovery)
- [x] Role-based access control
- [x] Secure disposal procedures

### Security Standards

- [x] OWASP Top 10 protections
- [x] Input validation
- [x] Injection prevention
- [x] CSRF protection (if web forms)
- [x] TLS encryption
- [x] Security headers

## 7. INCIDENT RESPONSE PLAN

### Data Breach Notification (72-hour requirement)

**Steps**:

1. Isolate affected systems
2. Assess scope and severity
3. Notify ICO (if high risk)
4. Notify affected users
5. Provide mitigating measures
6. Document incident response

## 8. MONITORING & LOGGING

### Key Metrics

- API response time (target: < 500ms)
- Error rate (alert: > 1%)
- Risk detection events (daily report)
- Audit log entries (daily export)
- Failed authentication attempts (alert: > 5 in 5 minutes)

### Tools

- CloudWatch (AWS logs)
- DataDog (APM)
- Splunk (log aggregation)
- Grafana (dashboards)

## 9. SECURITY TESTING

### Recommended Tests

- OWASP ZAP penetration testing (quarterly)
- SQL injection testing
- XSS payload testing
- Authentication bypass testing
- Rate limiting validation
- Encryption key rotation testing

### Dependencies Audit

```bash
pip audit  # Python vulnerability scanner
safety check  # Check for known security issues
```

## 10. REGULATORY CONTACTS

**UK ICO** (Information Commissioner's Office)

- Website: ico.org.uk
- GDPR Complaints: contact via website

**NHS England** (if integrated with NHS)

- Data Security & Protection Toolkit (DSPT)
- Annual completion required

**Crisis Support**

- Samaritans: 116 123 (24/7)
- Crisis Text Line: Text HELLO to 50808

---

## Document Version

**Version**: 1.0
**Last Updated**: 2024
**Next Review**: Quarterly

---

"""
