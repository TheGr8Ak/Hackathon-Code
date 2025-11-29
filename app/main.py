"""
Main FastAPI application for Hospital AI Agent System
"""
import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime

from app.core.monitoring import MonitoringService
from app.core.kill_switch import KillSwitch
from app.core.approval_manager import ApprovalManager
from app.core.database import init_db, get_db
from app.agents.supervisor import SupervisorAgent
from app.agents.watchtower import WatchtowerAgent
from app.agents.quartermaster import QuartermasterAgent
from app.agents.press_secretary import PressSecretaryAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hospital AI Agent System",
    description="Level 3 Semi-Autonomous Healthcare AI System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
monitoring = MonitoringService()
kill_switch = KillSwitch(monitoring=monitoring)
approval_manager = ApprovalManager()

# Initialize agents
supervisor = SupervisorAgent()
watchtower = WatchtowerAgent()
quartermaster = QuartermasterAgent()
press_secretary = PressSecretaryAgent()


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Running in mock mode.")
        logger.warning("Some features may be limited. Install PostgreSQL for full functionality.")
    logger.info("Application startup complete")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "kill_switch_active": kill_switch.is_kill_switch_active()
    }


@app.get("/readiness")
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket monitoring endpoint
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    await monitoring.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back (or process commands)
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        await monitoring.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await monitoring.disconnect(websocket)


# Kill switch endpoints
@app.post("/api/kill-switch")
async def toggle_kill_switch(action: Dict):
    """Activate or deactivate kill switch"""
    action_type = action.get("action", "status")
    reason = action.get("reason", "")
    user = action.get("user", "system")
    
    if action_type == "activate":
        result = kill_switch.activate_kill_switch(reason, user)
        return result
    elif action_type == "deactivate":
        notes = action.get("notes", "")
        result = kill_switch.reactivate_system(user, notes)
        return result
    else:
        status = kill_switch.get_status()
        return status


@app.get("/api/kill-switch/status")
async def get_kill_switch_status():
    """Get kill switch status"""
    return kill_switch.get_status()


# Approval endpoints
@app.post("/api/approve/{action_id}")
async def approve_action(action_id: str, approval: Dict):
    """Approve an action"""
    approved_by = approval.get("approved_by", "unknown")
    notes = approval.get("notes")
    modified_action = approval.get("modified_action")
    
    result = approval_manager.approve_action(
        action_id=action_id,
        approved_by=approved_by,
        notes=notes,
        modified_action=modified_action
    )
    
    # Broadcast approval
    await monitoring.broadcast_action({
        "type": "APPROVAL",
        "action_id": action_id,
        "status": "APPROVED",
        "approved_by": approved_by,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return result


@app.post("/api/reject/{action_id}")
async def reject_action(action_id: str, rejection: Dict):
    """Reject an action"""
    rejected_by = rejection.get("rejected_by", "unknown")
    reason = rejection.get("reason", "No reason provided")
    
    result = approval_manager.reject_action(
        action_id=action_id,
        rejected_by=rejected_by,
        reason=reason
    )
    
    # Broadcast rejection
    await monitoring.broadcast_action({
        "type": "REJECTION",
        "action_id": action_id,
        "status": "REJECTED",
        "rejected_by": rejected_by,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return result


@app.get("/api/actions/pending")
async def get_pending_actions():
    """Get all pending actions - normalized for frontend"""
    try:
        pending = approval_manager.get_all_pending_actions()
        
        # Normalize format for frontend
        normalized = []
        for action in pending:
            action_data = action.get("action_data", {})
            action_id = action.get("action_id")
            
            # Determine agent name from action type or context
            agent_name = "Quartermaster"  # Default
            if action_data.get("type") == "PATIENT_ADVISORY":
                agent_name = "Press Secretary"
            elif action_data.get("type") == "STAFFING_CHANGE":
                agent_name = "Quartermaster"
            
            normalized.append({
                "id": action_id,
                "action_id": action_id,
                "type": action_data.get("type", "UNKNOWN"),
                "agent": agent_name,
                "item": action_data.get("item"),
                "quantity": action_data.get("quantity"),
                "unit": action_data.get("unit", "units"),
                "cost": action_data.get("cost"),
                "vendor": action_data.get("vendor") or action_data.get("vendor_id"),
                "reasoning": action_data.get("reasoning"),
                "risk_level": action_data.get("urgency") or "MEDIUM",  # Default to MEDIUM if not specified
                "timestamp": action.get("registered_at"),
                "registered_at": action.get("registered_at"),
                "status": action.get("status", "PENDING"),
                # Include full action_data for compatibility
                "action": action_data
            })
        
        logger.info(f"Returning {len(normalized)} pending actions")
        return {"pending_actions": normalized}
        
    except Exception as e:
        logger.error(f"Failed to get pending actions: {e}")
        return {"pending_actions": []}



# Agent endpoints
@app.post("/api/supervisor/run-cycle")
async def run_daily_cycle(request: Dict):
    """Run supervisor daily cycle"""
    target_date = request.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    
    try:
        result = await supervisor.run_daily_cycle(target_date)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Supervisor cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchtower/forecast")
async def forecast_patient_load(request: Dict):
    """Get patient load forecast"""
    forecast_date = request.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    
    try:
        result = await watchtower.forecast_patient_load(forecast_date)
        return {
            "status": "success",
            "forecast": result
        }
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/history")
async def get_action_history(limit: int = 50):
    """Get recent action history"""
    history = await monitoring.get_recent_history(limit=limit)
    return {
        "history": history,
        "count": len(history)
    }


# Statistics endpoint
@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        # Get action history from monitoring
        history = await monitoring.get_recent_history(limit=1000)
        
        # Get pending actions from approval manager (more reliable)
        pending = approval_manager.get_all_pending_actions()
        
        # Calculate stats with better field checking
        stats = {
            "total_actions": len(history),
            "autonomous_actions": sum(
                1 for a in history 
                if a.get("execution_type") == "AUTONOMOUS" or 
                   (a.get("status") == "EXECUTED" and a.get("execution_type") == "AUTONOMOUS")
            ),
            "approved_actions": sum(
                1 for a in history 
                if a.get("execution_type") == "APPROVED" or 
                   a.get("status") == "APPROVED" or
                   a.get("approved_by") is not None
            ),
            "pending_actions": len(pending),  # Use actual pending count from approval manager
            "rejected_actions": sum(
                1 for a in history 
                if a.get("execution_type") == "REJECTED" or 
                   a.get("status") == "REJECTED" or
                   a.get("rejected_by") is not None
            ),
            "kill_switch_active": kill_switch.is_kill_switch_active()
        }
        
        logger.info(f"Stats calculated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        # Return zeros on error
        return {
            "total_actions": 0,
            "autonomous_actions": 0,
            "approved_actions": 0,
            "pending_actions": len(approval_manager.get_all_pending_actions()),
            "rejected_actions": 0,
            "kill_switch_active": kill_switch.is_kill_switch_active()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

