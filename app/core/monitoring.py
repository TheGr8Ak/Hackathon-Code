"""
Monitoring service for broadcasting agent actions to dashboard
"""
import json
import logging
import redis
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket


logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring and broadcasting agent actions"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for monitoring")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Monitoring will work in-memory only.")
            self.redis_client = None
        
        self.active_connections: List[WebSocket] = []
        self.action_history: List[Dict] = []  # In-memory fallback
        self.max_history = 1000
    
    async def connect(self, websocket: WebSocket):
        """Add a WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
        
        # Send recent history
        history = await self.get_recent_history(limit=50)
        if history:
            await websocket.send_json({
                "type": "history",
                "actions": history
            })
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_action(self, action_data: Dict):
        """Broadcast action to all connected clients"""
        # Add timestamp if not present
        if "timestamp" not in action_data:
            action_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Ensure agent name is present
        if "agent" not in action_data:
            action_data["agent"] = "Unknown Agent"
        
        # Ensure action type is accessible at top level
        if "action" in action_data and isinstance(action_data["action"], dict):
            if "type" in action_data["action"] and "type" not in action_data:
                action_data["type"] = action_data["action"]["type"]
        
        # Store in Redis as JSON string (simpler and more reliable)
        if self.redis_client:
            try:
                action_json = json.dumps(action_data, default=str)
                self.redis_client.lpush("action_history", action_json)
                self.redis_client.ltrim("action_history", 0, self.max_history - 1)
                logger.debug(f"Stored action in Redis history")
            except Exception as e:
                logger.error(f"Failed to store in Redis: {e}")
        
        # Store in memory
        self.action_history.append(action_data.copy())
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)
        
        # Broadcast to WebSocket clients
        message = {
            "type": "action",
            "data": action_data
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)
        
        action_type = action_data.get("type") or action_data.get("action", {}).get("type", "UNKNOWN")
        logger.info(f"Broadcasted action: {action_data.get('agent')} - {action_type}")
    
    async def log_action_proposal(self, agent: str, action: Dict):
        """Log an action proposal"""
        proposal_data = {
            "agent": agent,
            "action": action,
            "type": action.get("type", "UNKNOWN"),
            "status": "PROPOSED",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_action(proposal_data)
    
    async def broadcast_error(self, error_data: Dict):
        """Broadcast an error"""
        error_data["type"] = "error"
        await self.broadcast_action(error_data)
    
    async def log_verification(self, agent: str, action: Dict, verification: Dict):
        """Log verification result"""
        verification_data = {
            "agent": agent,
            "action": action,
            "type": action.get("type", "UNKNOWN"),
            "verification": verification,
            "status": "VERIFIED",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_action(verification_data)
    
    async def get_recent_history(self, limit: int = 50) -> List[Dict]:
        """Get recent action history"""
        if self.redis_client:
            try:
                # Get from Redis list
                action_strings = self.redis_client.lrange("action_history", 0, limit - 1)
                history = []
                
                for action_str in action_strings:
                    try:
                        action = json.loads(action_str)
                        history.append(action)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse action: {e}")
                        continue
                
                logger.info(f"Retrieved {len(history)} actions from Redis")
                return history
                
            except Exception as e:
                logger.error(f"Failed to get from Redis: {e}")
        
        # Fallback to in-memory
        logger.info(f"Using in-memory history: {len(self.action_history)} actions")
        return self.action_history[-limit:] if len(self.action_history) > limit else self.action_history.copy()
