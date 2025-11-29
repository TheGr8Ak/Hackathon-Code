"""
Approval Manager - Handles approval workflow for agent actions
"""
import json
import asyncio
import logging
import redis
import os
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from uuid import uuid4


logger = logging.getLogger(__name__)


class ApprovalManager:
    """Manages approval workflow for agent actions"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.approval_timeout = int(os.getenv("APPROVAL_TIMEOUT", "300"))  # 5 minutes default
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Approval manager connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Approvals will work in-memory only.")
            self.redis_client = None
            self._in_memory_approvals: Dict[str, Dict] = {}
            self._in_memory_pending: Dict[str, Dict] = {}
    
    def generate_action_id(self) -> str:
        """Generate unique action ID"""
        return f"action_{uuid4().hex[:12]}"
    
    async def wait_for_approval(
        self,
        action_id: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wait for approval decision
        
        Returns:
            {
                "status": "APPROVED" | "REJECTED" | "TIMEOUT",
                "approved_by": str | None,
                "rejection_reason": str | None,
                "modified_action": Dict | None
            }
        """
        timeout = timeout or self.approval_timeout
        start_time = datetime.utcnow()
        
        while True:
            # Check if approved/rejected
            decision = self.get_approval_decision(action_id)
            
            if decision["status"] in ["APPROVED", "REJECTED"]:
                return decision
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout:
                logger.warning(f"Approval timeout for action {action_id}")
                return {
                    "status": "TIMEOUT",
                    "approved_by": None,
                    "rejection_reason": "Approval timeout - no response within time limit",
                    "modified_action": None
                }
            
            # Wait before checking again
            await asyncio.sleep(2)
    
    def get_approval_decision(self, action_id: str) -> Dict[str, Any]:
        """Get current approval decision for an action"""
        if self.redis_client:
            try:
                decision_str = self.redis_client.get(f"approval:{action_id}")
                if decision_str:
                    return json.loads(decision_str)
            except Exception as e:
                logger.error(f"Failed to get approval from Redis: {e}")
        
        # Check in-memory
        if self.redis_client is None and action_id in self._in_memory_approvals:
            return self._in_memory_approvals[action_id]
        
        return {
            "status": "PENDING",
            "approved_by": None,
            "rejection_reason": None,
            "modified_action": None
        }
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """
        Get all pending actions awaiting approval
        
        Returns:
            List of pending action dictionaries
        """
        pending_actions = []
        
        if self.redis_client:
            try:
                # Get all pending: keys
                keys = self.redis_client.keys("pending:*")
                
                for key in keys:
                    pending_str = self.redis_client.get(key)
                    if pending_str:
                        pending_data = json.loads(pending_str)
                        # Only include if still pending
                        if pending_data.get("status") == "PENDING":
                            pending_actions.append(pending_data)
                
            except Exception as e:
                logger.error(f"Failed to get pending actions from Redis: {e}")
        else:
            # Use in-memory storage
            if hasattr(self, '_in_memory_pending'):
                for action_id, pending_data in self._in_memory_pending.items():
                    if pending_data.get("status") == "PENDING":
                        pending_actions.append(pending_data)
        
        return pending_actions
    
    def approve_action(
        self,
        action_id: str,
        approved_by: str,
        notes: Optional[str] = None,
        modified_action: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Approve an action"""
        decision = {
            "status": "APPROVED",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat(),
            "notes": notes,
            "modified_action": modified_action
        }
        
        if self.redis_client:
            try:
                # Store approval decision
                self.redis_client.set(
                    f"approval:{action_id}",
                    json.dumps(decision),
                    ex=self.approval_timeout * 2  # Keep for 2x timeout duration
                )
                
                # Remove from pending
                self.redis_client.delete(f"pending:{action_id}")
                
            except Exception as e:
                logger.error(f"Failed to store approval in Redis: {e}")
        else:
            self._in_memory_approvals[action_id] = decision
            if hasattr(self, '_in_memory_pending') and action_id in self._in_memory_pending:
                del self._in_memory_pending[action_id]
        
        logger.info(f"Action {action_id} approved by {approved_by}")
        return decision
    
    def reject_action(
        self,
        action_id: str,
        rejected_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """Reject an action"""
        decision = {
            "status": "REJECTED",
            "rejected_by": rejected_by,
            "rejected_at": datetime.utcnow().isoformat(),
            "rejection_reason": reason
        }
        
        if self.redis_client:
            try:
                # Store rejection decision
                self.redis_client.set(
                    f"approval:{action_id}",
                    json.dumps(decision),
                    ex=self.approval_timeout * 2
                )
                
                # Remove from pending
                self.redis_client.delete(f"pending:{action_id}")
                
            except Exception as e:
                logger.error(f"Failed to store rejection in Redis: {e}")
        else:
            self._in_memory_approvals[action_id] = decision
            if hasattr(self, '_in_memory_pending') and action_id in self._in_memory_pending:
                del self._in_memory_pending[action_id]
        
        logger.info(f"Action {action_id} rejected by {rejected_by}: {reason}")
        return decision
    
    def register_pending_action(self, action_id: str, action_data: Dict) -> None:
        """Register an action as pending approval"""
        pending_data = {
            "action_id": action_id,
            "action_data": action_data,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "PENDING"
        }
        
        if self.redis_client:
            try:
                # Store with JSON serialization to avoid tuple errors
                self.redis_client.set(
                    f"pending:{action_id}",
                    json.dumps(pending_data, default=str),  # Convert all to strings
                    ex=self.approval_timeout * 2
                )
                logger.info(f"Registered pending action: {action_id}")
            except Exception as e:
                logger.error(f"Failed to register pending action in Redis: {e}")
        else:
            if not hasattr(self, '_in_memory_pending'):
                self._in_memory_pending = {}
            self._in_memory_pending[action_id] = pending_data
    
    def get_all_pending_actions(self) -> List[Dict]:
        """Get all pending actions"""
        pending_list = []
        
        if self.redis_client:
            try:
                # Get all pending action keys
                keys = self.redis_client.keys("pending:*")
                for key in keys:
                    try:
                        data_str = self.redis_client.get(key)
                        if data_str:
                            pending_data = json.loads(data_str)
                            # Check if still pending (not approved/rejected)
                            decision = self.get_approval_decision(pending_data.get("action_id"))
                            if decision["status"] == "PENDING":
                                pending_list.append(pending_data)
                    except Exception as e:
                        logger.error(f"Failed to parse pending action {key}: {e}")
            except Exception as e:
                logger.error(f"Failed to get pending actions from Redis: {e}")
        else:
            # In-memory fallback
            if hasattr(self, '_in_memory_pending'):
                for action_id, pending_data in self._in_memory_pending.items():
                    # Check if still pending
                    decision = self.get_approval_decision(action_id)
                    if decision["status"] == "PENDING":
                        pending_list.append(pending_data)
        
        return pending_list
