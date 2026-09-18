# Connection Module

Localhost-only configuration for the Heatwave EWS backend.

## Development Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ with PostGIS
- Redis 7+

### Environment Configuration
1. Copy `.env.example` to `.env`
2. Update the following values:
   - `DATABASE_URL`: `postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/heatwave`
   - `REDIS_URL`: `redis://localhost:6379/0`
   - `OPEN_METEO_API_KEY`: (free, can be left empty for basic use)
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` (sandbox demo)
   - `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_ACCESS_TOKEN` (sandbox demo)

### Run Locally
```bash
# 1. Start PostgreSQL
brew services start postgresql@16
# OR start PostgreSQL 17
brew services start postgresql@17

# 2. Start Redis
brew services start redis

# 3. Install dependencies
cd backend && source venv/bin/activate && pip install -r requirements.txt

# 4. Run database migrations
cd backend && source venv/bin/activate && alembic upgrade head

# 5. Start the backend
cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Start the frontend
cd frontend && npm install && npm run dev
```

### API Base URL
All frontend calls proxy to `http://localhost:8000/api` (configured in vite.config.ts)