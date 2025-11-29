# How to Start the Hospital AI System

## ⚠️ Important: Use the Correct Command

The old `green_corridor_agent.py` file exists in the root directory. Make sure you're running the **new Hospital AI System**, not the old one.

## ✅ Correct Way to Start

### Option 1: Use the Startup Script (Easiest)

**PowerShell:**
```powershell
.\START_SERVER.ps1
```

**Command Prompt:**
```cmd
START_SERVER.bat
```

### Option 2: Manual Start

**Make sure you specify the correct module path:**

```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Start the CORRECT app (Hospital AI System)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**❌ WRONG - This will start the old Green Corridor Agent:**
```powershell
uvicorn green_corridor_agent:app  # Don't use this!
uvicorn app  # Don't use this!
```

## ✅ Verify You're Running the Right System

When you visit http://localhost:8000/docs, you should see:

**✅ CORRECT:**
- Title: **"Hospital AI Agent System"**
- Endpoints like: `/api/supervisor/run-cycle`, `/api/watchtower/forecast`, `/api/kill-switch`

**❌ WRONG (Old System):**
- Title: **"Green Corridor AI Agent"**
- Endpoints like: `/telemetry/update`, `/ws/dashboard`

## 🔧 If You See the Wrong System

1. **Stop the current server** (Ctrl+C in the terminal)
2. **Kill any running processes:**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -eq "uvicorn"} | Stop-Process
   ```
3. **Start again with the correct command:**
   ```powershell
   uvicorn app.main:app --reload
   ```

## 📋 Quick Reference

| What | Command |
|------|---------|
| Start Hospital AI System | `uvicorn app.main:app --reload` |
| Start with script | `.\START_SERVER.ps1` |
| Check if running | Visit http://localhost:8000/docs |
| Stop server | Ctrl+C in terminal |

## 🎯 Expected Endpoints

When running correctly, you should see these endpoints:

- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /api/stats` - System statistics
- `POST /api/supervisor/run-cycle` - Run daily cycle
- `POST /api/watchtower/forecast` - Get forecast
- `POST /api/kill-switch` - Toggle kill switch
- `POST /api/approve/{action_id}` - Approve action
- `POST /api/reject/{action_id}` - Reject action
- `WebSocket /ws/monitor` - Real-time monitoring

