# 🏥 CodeCoven - HealthTech

<img width="1336" height="740" alt="Screenshot 2025-11-29 093448" src="https://github.com/user-attachments/assets/85490351-c74c-4c55-befd-f9f5b078490c" />

![WhatsApp Image 2025-11-29 at 10 54 34](https://github.com/user-attachments/assets/35e19acf-259d-4f01-9af1-7f1c2dd0fdc6)

<img width="1919" height="870" alt="Screenshot 2025-11-29 063341" src="https://github.com/user-attachments/assets/2446affe-8616-407b-8bb0-14fc5aa6d804" />

A Level 3 Semi-Autonomous Healthcare AI System with 3 working agents (Watchtower, Quartermaster, Press Secretary) orchestrated by a Supervisor using LangGraph. The system forecasts patient load using NeuralProphet, manages resources autonomously within trust boundaries, and sends patient advisories using RAG.

## 🎯 Features

- **Watchtower Agent**: Forecasts patient load using NeuralProphet with external regressors (AQI, festivals, epidemic signals)
- **Quartermaster Agent**: Manages inventory and staffing autonomously within trust boundaries
- **Press Secretary Agent**: Sends patient advisories using RAG (Retrieval-Augmented Generation)
- **Supervisor Agent**: Orchestrates all agents using LangGraph workflow
- **Trust Boundaries Engine**: Evaluates risk and determines autonomous execution vs. approval required
- **Real-time Dashboard**: WebSocket-based monitoring with action feed and approval UI
- **Kill Switch**: Emergency stop mechanism for all autonomous actions
- **Approval System**: Human-in-the-loop for high-risk actions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Supervisor Agent                      │
│                  (LangGraph Workflow)                   │
└──────────────┬──────────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼──────┐
│Watch- │  │Quart-│  │  Press   │
│tower  │  │master│  │Secretary │
└───────┘  └──────┘  └──────────┘
    │          │          │
    └──────────┼──────────┘
               │
    ┌──────────▼──────────┐
    │  Trust Boundaries   │
    │      Engine         │
    └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### Using Docker Compose (Recommended)

1. **Clone and setup**:
```bash
git clone <repository>
cd Hackathon
cp .env.example .env  # Edit with your API keys
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Access services**:
- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow: http://localhost:5000

### Local Development

1. **Backend setup**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Initialize database
python -c "from app.core.database import init_db; init_db()"
```

3. **Run backend**:
```bash
uvicorn app.main:app --reload
```

4. **Frontend setup**:
```bash
cd frontend
npm install
npm run dev
```

## 📋 Environment Variables

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql://hospital_ai:hospital_ai_pass@localhost:5432/hospital_ai_db
REDIS_URL=redis://localhost:6379/0

# API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# SMS (Optional - uses mock if not provided)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# Hospital Config
HOSPITAL_NAME=City Hospital
HOSPITAL_LOCATION_LAT=12.9716
HOSPITAL_LOCATION_LON=77.5946
```

## 🎮 Usage

### Running Daily Cycle

```bash
# Via API
curl -X POST http://localhost:8000/api/supervisor/run-cycle \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-01-15"}'

# Or via Python
python -c "from app.agents.supervisor import SupervisorAgent; import asyncio; asyncio.run(SupervisorAgent().run_daily_cycle('2025-01-15'))"
```

### Monitoring Dashboard

1. Open http://localhost:3000
2. View real-time action feed
3. Approve/reject pending actions
4. Monitor system statistics
5. Use Emergency Stop if needed

### API Endpoints

- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /api/stats` - System statistics
- `GET /api/monitoring/history` - Action history
- `POST /api/kill-switch` - Toggle kill switch
- `POST /api/approve/{action_id}` - Approve action
- `POST /api/reject/{action_id}` - Reject action
- `POST /api/supervisor/run-cycle` - Run daily cycle
- `POST /api/watchtower/forecast` - Get forecast
- `WebSocket /ws/monitor` - Real-time monitoring

## 🔒 Trust Boundaries

The system evaluates actions against trust boundaries:

- **LOW Risk**: Executes autonomously
- **MEDIUM Risk**: Requires single approval
- **HIGH Risk**: Requires multiple approvals
- **CRITICAL Risk**: Requires CMO approval

### Action Types

1. **PURCHASE_ORDER**: Cost thresholds (₹50k low, ₹2L medium, ₹5L high)
2. **STAFFING_CHANGE**: Overtime hours (20h low, 40h medium)
3. **PATIENT_ADVISORY**: Recipient count (2000 low, 5000 medium)
4. **INVENTORY_TRANSFER**: Value thresholds (₹30k low, ₹1L medium)

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

## 📁 Project Structure

```
Hackathon/
├── app/
│   ├── agents/
│   │   ├── level3_base_agent.py    # Base agent class
│   │   ├── watchtower.py           # Forecasting agent
│   │   ├── quartermaster.py        # Resource management
│   │   ├── press_secretary.py      # Patient communication
│   │   └── supervisor.py           # Orchestrator
│   ├── core/
│   │   ├── database.py              # SQLAlchemy models
│   │   ├── trust_boundaries.py     # Risk evaluation
│   │   ├── monitoring.py            # WebSocket monitoring
│   │   ├── kill_switch.py           # Emergency stop
│   │   └── approval_manager.py      # Approval workflow
│   ├── services/
│   │   ├── sms_service.py           # SMS via Twilio
│   │   └── email_service.py         # Email (mock)
│   ├── database/
│   │   └── patient_db.py            # Patient database
│   └── main.py                      # FastAPI app
├── frontend/
│   └── src/
│       └── components/
│           └── Level3Dashboard.jsx  # React dashboard
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🎯 Success Criteria (16-Hour Checkpoint)

✅ **Working**: 3 agents forecast, purchase supplies, and send advisories  
✅ **Dashboard**: Real-time action feed with WebSocket  
✅ **Trust Boundaries**: Low-risk actions execute autonomously, high-risk require approval  
✅ **Database**: Actions logged in PostgreSQL audit trail  
✅ **Demo-able**: Can show end-to-end workflow in 5-minute demo

## 🔮 Future Enhancements

- [ ] Complete NeuralProphet model training with historical data
- [ ] Real supplier API integration
- [ ] Enhanced RAG with more medical guidelines
- [ ] Multi-language support for patient advisories
- [ ] Advanced analytics and reporting
- [ ] Integration with hospital management systems
- [ ] Mobile app for approvals

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 📧 Contact

For questions or support, please open an issue on GitHub.



