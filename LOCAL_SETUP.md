# Local Setup Guide (Without Docker)

Since Docker is not installed, here's how to run the system locally.

## Option 1: Install Docker Desktop (Recommended)

1. Download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Then use: `docker compose up -d` (note: newer Docker uses `docker compose` not `docker-compose`)

## Option 2: Run Locally Without Docker

### Step 1: Install PostgreSQL and Redis

**PostgreSQL:**
- Download from: https://www.postgresql.org/download/windows/
- Or use a cloud service like Supabase/Neon (free tier available)

**Redis:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use Redis Cloud (free tier): https://redis.com/try-free/

### Step 2: Setup Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database (update with your PostgreSQL connection)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/hospital_ai_db
REDIS_URL=redis://localhost:6379/0

# API Keys (get from respective services)
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# SMS (Optional - system works without it)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Hospital Config
HOSPITAL_NAME=City Hospital
HOSPITAL_LOCATION_LAT=12.9716
HOSPITAL_LOCATION_LON=77.5946
```

### Step 4: Initialize Database

```powershell
# Create database in PostgreSQL first
# Then run:
python scripts/init_database.py
```

### Step 5: Start Backend

```powershell
# Make sure venv is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Start Frontend (in a new terminal)

```powershell
cd frontend
npm install
npm run dev
```

### Step 7: Access System

- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 3: Minimal Setup (No Database/Redis)

For quick testing without external dependencies:

1. The system will work in "mock mode" for:
   - Redis (in-memory fallback)
   - Database (will fail on startup but can be skipped)
   - SMS (mock mode)

2. Modify `app/main.py` to skip database init:

```python
@app.on_event("startup")
async def startup_event():
    logger.info("Skipping database init (mock mode)")
    # init_db()  # Comment this out
```

3. Run backend:
```powershell
uvicorn app.main:app --reload
```

## Quick Test Without Full Setup

Run the quick test script to verify components:

```powershell
python scripts/quick_test.py
```

This tests:
- Trust boundaries engine
- Kill switch
- Approval manager
- Agent initialization

## Troubleshooting

### PostgreSQL Connection Error
- Make sure PostgreSQL is running
- Check connection string in `.env`
- Verify database exists: `CREATE DATABASE hospital_ai_db;`

### Redis Connection Error
- System will use in-memory fallback if Redis unavailable
- This is fine for testing, but WebSocket history won't persist

### Port Already in Use
- Change port in `uvicorn` command: `--port 8001`
- Update frontend `.env`: `VITE_API_URL=http://localhost:8001`

### Module Not Found
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

