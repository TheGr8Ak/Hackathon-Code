"""
Kill Switch - Emergency stop mechanism for autonomous agents
"""
import json
import asyncio
import logging
import redis
import os
from typing import Optional, Dict
from datetime import datetime
from app.core.monitoring import MonitoringService

logger = logging.getLogger(__name__)


class KillSwitch:
    """Emergency stop mechanism for the AI system"""
    
    def __init__(self, monitoring: Optional[MonitoringService] = None):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_key = os.getenv("KILL_SWITCH_REDIS_KEY", "system:kill_switch")
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Kill switch connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Kill switch will work in-memory only.")
            self.redis_client = None
            self._in_memory_state = False
        
        self.monitoring = monitoring
    
    def is_system_active(self) -> bool:
        """Check if system is active (not killed)"""
        if self.redis_client:
            try:
                status = self.redis_client.get(self.redis_key)
                return status != "KILLED"  # If not set or not "KILLED", system is active
            except Exception as e:
                logger.error(f"Failed to check kill switch in Redis: {e}")
                return not getattr(self, '_in_memory_state', False)
        
        return not getattr(self, '_in_memory_state', False)
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active"""
        return not self.is_system_active()
    
    def activate_kill_switch(self, reason: str, activated_by: str) -> Dict:
        """Activate the kill switch"""
        try:
            kill_data = {
                "status": "KILLED",
                "reason": reason,
                "activated_by": activated_by,
                "activated_at": datetime.utcnow().isoformat()
            }
            
            if self.redis_client:
                self.redis_client.set(
                    self.redis_key,
                    "KILLED",
                    ex=86400  # Expire after 24 hours (safety)
                )
                self.redis_client.set(
                    f"{self.redis_key}:metadata",
                    json.dumps(kill_data),
                    ex=86400
                )
            else:
                self._in_memory_state = True
            
            # Broadcast alert
            if self.monitoring:
                asyncio.create_task(self.monitoring.broadcast_action({
                    "type": "KILL_SWITCH_ACTIVATED",
                    "data": kill_data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            logger.critical(f"KILL SWITCH ACTIVATED by {activated_by}: {reason}")
            
            return {
                "status": "success",
                "message": "Kill switch activated",
                "data": kill_data
            }
        except Exception as e:
            logger.error(f"Failed to activate kill switch: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def reactivate_system(self, reactivated_by: str, notes: Optional[str] = None) -> Dict:
        """Reactivate the system"""
        try:
            reactivation_data = {
                "status": "ACTIVE",
                "reactivated_by": reactivated_by,
                "reactivated_at": datetime.utcnow().isoformat(),
                "notes": notes
            }
            
            if self.redis_client:
                self.redis_client.delete(self.redis_key)
                self.redis_client.delete(f"{self.redis_key}:metadata")
                self.redis_client.set(
                    f"{self.redis_key}:reactivation",
                    json.dumps(reactivation_data),
                    ex=86400
                )
            else:
                self._in_memory_state = False
            
            # Broadcast alert
            if self.monitoring:
                asyncio.create_task(self.monitoring.broadcast_action({
                    "type": "KILL_SWITCH_DEACTIVATED",
                    "data": reactivation_data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            logger.info(f"System reactivated by {reactivated_by}: {notes}")
            
            return {
                "status": "success",
                "message": "System reactivated",
                "data": reactivation_data
            }
        except Exception as e:
            logger.error(f"Failed to reactivate system: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_status(self) -> Dict:
        """Get current kill switch status"""
        is_active = self.is_system_active()
        
        metadata = {}
        if self.redis_client:
            try:
                metadata_str = self.redis_client.get(f"{self.redis_key}:metadata")
                if metadata_str:
                    metadata = json.loads(metadata_str)
            except:
                pass
        
        return {
            "system_active": is_active,
            "kill_switch_active": not is_active,
            "metadata": metadata
        }

