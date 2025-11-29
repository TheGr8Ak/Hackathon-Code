# Quick Start Guide

## Fastest Way to Get Started (No Docker Required)

### 1. Install Python Dependencies

```powershell
# Activate virtual environment (if not already)
.\venv\Scripts\Activate.ps1

# Install all packages
pip install -r requirements.txt
```

### 2. Run Quick Test (Verify Installation)

```powershell
python scripts/quick_test.py
```

This will test all core components without needing database/Redis.

### 3. Start Backend (Mock Mode)

```powershell
# Start FastAPI server
uvicorn app.main:app --reload
```

The system will work in mock mode:
- ✅ Trust boundaries: Works
- ✅ Agents: Work
- ✅ Monitoring: In-memory (no Redis needed)
- ⚠️ Database: Will show error but can be ignored for testing
- ✅ WebSocket: Works

### 4. Test API Endpoints

Open browser: http://localhost:8000/docs

Try these endpoints:
- `GET /health` - Health check
- `GET /api/stats` - System statistics
- `POST /api/watchtower/forecast` - Get forecast
  ```json
  {"date": "2025-01-15"}
  ```

### 5. Run Daily Cycle (Python Script)

Create a test script `test_run.py`:

```python
import asyncio
from app.agents.supervisor import SupervisorAgent
from datetime import datetime

async def main():
    supervisor = SupervisorAgent()
    date = datetime.now().strftime("%Y-%m-%d")
    result = await supervisor.run_daily_cycle(date)
    print("\n=== Daily Cycle Complete ===")
    print(f"Forecast: {result['forecast'].get('predicted_load')} patients")
    print(f"Actions: {len(result.get('resource_actions', []))}")
    print(f"Advisories: {len(result.get('advisories_sent', []))}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```powershell
python test_run.py
```

## What Works Without Full Setup

✅ **All Agents**: Watchtower, Quartermaster, Press Secretary, Supervisor  
✅ **Trust Boundaries**: Risk evaluation and approval workflow  
✅ **Kill Switch**: Emergency stop mechanism  
✅ **Approval System**: Approve/reject actions  
✅ **Forecasting**: Watchtower with fallback predictions  
✅ **Resource Management**: Quartermaster supply/staffing analysis  
✅ **Patient Advisories**: Press Secretary with RAG  

⚠️ **Limited Without Database/Redis**:
- Action history won't persist
- WebSocket history resets on restart
- No audit trail in database

## Next Steps

1. **For Full Features**: Install PostgreSQL and Redis (see LOCAL_SETUP.md)
2. **For Production**: Use Docker (install Docker Desktop)
3. **For Testing**: Current setup is sufficient

## Common Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start backend
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Generate synthetic data
python scripts/generate_indian_synth_data.py

# Quick test
python scripts/quick_test.py
```

