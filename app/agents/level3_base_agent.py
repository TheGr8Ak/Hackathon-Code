# app/agents/level3_base_agent.py
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.monitoring import MonitoringService
from app.core.trust_boundaries import TrustBoundaryEngine
from app.core.kill_switch import KillSwitch
from app.core.approval_manager import ApprovalManager
from google import genai

logger = logging.getLogger(__name__)

class Level3Agent(ABC):
    """Base class for Level 3 autonomous agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.monitoring = MonitoringService()
        self.trust_engine = TrustBoundaryEngine()
        self.kill_switch = KillSwitch(monitoring=self.monitoring)
        self.approval_manager = ApprovalManager()
        # LLM client - optional, only if API key is provided
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.llm_client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.llm_client = None
        else:
            logger.warning("GEMINI_API_KEY not set. LLM features will be limited.")
            self.llm_client = None
        self.action_history: List[Dict] = []
        
        logger.info(f"{agent_name} Agent initialized")
    
    async def propose_and_execute(self, action: Dict) -> Dict:
        """
        Level 3 autonomous action execution with trust boundaries and approval workflow
        
        Flow:
        1. Check kill switch
        2. Evaluate risk via trust engine
        3. If can_execute: execute autonomously
        4. Else: wait for approval (with timeout)
        5. Log to audit trail
        6. Broadcast to monitoring dashboard
        """
        
        # Check kill switch first
        if self.kill_switch.is_kill_switch_active():
            error_record = {
                'agent': self.agent_name,
                'action': action,
                'error': 'Kill switch is active - action blocked',
                'status': 'BLOCKED',
                'timestamp': datetime.utcnow().isoformat(),
                'execution_type': 'REJECTED'
            }
            await self.monitoring.broadcast_error(error_record)
            return error_record
        
        # Log proposal
        await self.monitoring.log_action_proposal(
            agent=self.agent_name,
            action=action
        )
        
        # Evaluate action against trust boundaries
        evaluation = self.trust_engine.evaluate_action(action)
        risk_level = evaluation.get("risk_level", "UNKNOWN")
        can_execute = evaluation.get("can_execute", False)
        required_approvals = evaluation.get("required_approvals", [])
        reasons = evaluation.get("reasons", [])
        
        # Generate action ID for tracking
        action_id = self.approval_manager.generate_action_id()
        action["action_id"] = action_id
        
        execution_record = {
            'agent': self.agent_name,
            'action': action,
            'action_id': action_id,
            'risk_level': risk_level,
            'required_approvals': required_approvals,
            'reasons': reasons,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # If can execute autonomously
        if can_execute:
            try:
                result = await self.execute_action(action)
                execution_record.update({
                    'result': result,
                    'status': 'EXECUTED',
                    'execution_type': 'AUTONOMOUS',
                    'approved_by': None
                })
                
                self.action_history.append(execution_record)
                await self.monitoring.broadcast_action(execution_record)
                
                # Verify outcome (async - happens later)
                asyncio.create_task(self._verify_later(execution_record))
                
                logger.info(f"{self.agent_name} executed action autonomously: {action.get('type')}")
                return execution_record
                
            except Exception as e:
                logger.error(f"{self.agent_name} action failed: {e}")
                error_record = {
                    'agent': self.agent_name,
                    'action': action,
                    'action_id': action_id,
                    'error': str(e),
                    'status': 'FAILED',
                    'execution_type': 'AUTONOMOUS',
                    'timestamp': datetime.utcnow().isoformat()
                }
                await self.monitoring.broadcast_error(error_record)
                return error_record
        
        # Requires approval
        else:
            execution_record.update({
                'status': 'AWAITING_APPROVAL',
                'execution_type': 'PENDING'
            })
            
            # Register as pending
            self.approval_manager.register_pending_action(action_id, action)
            await self.monitoring.broadcast_action(execution_record)
            
            logger.info(f"{self.agent_name} action requires approval: {action.get('type')} (Risk: {risk_level})")
            
            # Wait for approval
            approval_decision = await self.approval_manager.wait_for_approval(action_id)
            
            if approval_decision["status"] == "APPROVED":
                # Execute with approved action (may be modified)
                approved_action = approval_decision.get("modified_action") or action
                
                try:
                    result = await self.execute_action(approved_action)
                    execution_record.update({
                        'result': result,
                        'status': 'EXECUTED',
                        'execution_type': 'APPROVED',
                        'approved_by': approval_decision.get("approved_by"),
                        'approval_notes': approval_decision.get("notes")
                    })
                    
                    self.action_history.append(execution_record)
                    await self.monitoring.broadcast_action(execution_record)
                    
                    # Verify outcome
                    asyncio.create_task(self._verify_later(execution_record))
                    
                    logger.info(f"{self.agent_name} executed approved action: {action.get('type')}")
                    return execution_record
                    
                except Exception as e:
                    logger.error(f"{self.agent_name} approved action failed: {e}")
                    error_record = {
                        'agent': self.agent_name,
                        'action': approved_action,
                        'action_id': action_id,
                        'error': str(e),
                        'status': 'FAILED',
                        'execution_type': 'APPROVED',
                        'approved_by': approval_decision.get("approved_by"),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    await self.monitoring.broadcast_error(error_record)
                    return error_record
            
            elif approval_decision["status"] == "REJECTED":
                execution_record.update({
                    'status': 'REJECTED',
                    'execution_type': 'REJECTED',
                    'rejected_by': approval_decision.get("rejected_by"),
                    'rejection_reason': approval_decision.get("rejection_reason")
                })
                await self.monitoring.broadcast_action(execution_record)
                logger.info(f"{self.agent_name} action rejected: {action.get('type')}")
                return execution_record
            
            else:  # TIMEOUT
                execution_record.update({
                    'status': 'TIMEOUT',
                    'execution_type': 'REJECTED',
                    'rejection_reason': 'Approval timeout'
                })
                await self.monitoring.broadcast_action(execution_record)
                logger.warning(f"{self.agent_name} action approval timeout: {action.get('type')}")
                return execution_record
    
    async def _verify_later(self, execution_record: Dict):
        """Verify action outcome after delay

        Accepts the full execution_record so verification handlers can access
        the recorded timestamp and any metadata.
        """
        await asyncio.sleep(300)  # Wait 5 minutes

        action = execution_record.get('action')
        result = execution_record.get('result')

        verification = await self.verify_outcome(action, result)

        await self.monitoring.log_verification(
            agent=execution_record.get('agent', self.agent_name),
            action=action,
            verification=verification
        )
    
    @abstractmethod
    async def execute_action(self, action: Dict) -> Any:
        """Execute the proposed action - must be implemented by subclass"""
        pass
    
    @abstractmethod
    async def verify_outcome(self, action: Dict, result: Dict) -> Dict:
        """Verify if action achieved desired outcome"""
        pass
