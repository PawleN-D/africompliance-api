# SA Compliance API

POPIA-compliant business verification API for South African companies.

## Features

- ✅ CIPC company verification
- ✅ Director information lookup
- ✅ Risk scoring and sanctions screening
- ✅ POPIA-compliant data handling
- ✅ 90-day caching for cost optimization

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite (MVP) → PostgreSQL (Production)
- **Hosting:** Vercel
- **Cache:** In-memory (MVP) → Redis (Production)

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/sa-compliance-api.git
cd sa-compliance-api

# Create virtual environment
python -m venv ven
source ven/bin/activate  # On Linux/Mac
# or
ven\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Running Locally
```bash
# Start the API server
uvicorn api.main:app --reload --port 8000

# API will be available at:
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/redoc (ReDoc)
```

## API Usage

### Verify a Company
```bash
curl -X POST http://localhost:8000/v1/verify/business/za \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "2019/123456/07",
    "verify_directors": true
  }'
```

### Response
```json
{
  "status": "verified",
  "confidence_score": 95,
  "business": {
    "legal_name": "Example Logistics (Pty) Ltd",
    "registration_number": "2019/123456/07",
    "status": "In Business",
    "vat_registered": true
  },
  "directors": [...],
  "risk_flags": {...},
  "verified_at": "2026-01-17T14:23:11Z"
}
```

## Deployment

Deployed on Vercel: [Your Vercel URL]

## Roadmap

- [ ] SARS VAT verification
- [ ] PostgreSQL migration
- [ ] Sanctions list integration
- [ ] Webhook support for async verification
- [ ] Multi-country support (Kenya, Nigeria)

## License

MIT

## Contact

For pilot access or inquiries: [sirpawle@gmail.com]