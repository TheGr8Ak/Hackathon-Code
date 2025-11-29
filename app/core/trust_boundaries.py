"""
Trust Boundaries Engine - Evaluates risk and determines if actions can execute autonomously
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TrustBoundaryEngine:
    """
    Evaluates actions against trust boundaries to determine:
    - Can execute autonomously?
    - Risk level
    - Required approvals
    """
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.getenv(
                "TRUST_BOUNDARIES_CONFIG_PATH",
                "app/core/trust_boundaries.json"
            )
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"Trust boundaries engine initialized with config: {config_path}")
    
    def _load_config(self) -> Dict:
        """Load trust boundaries configuration"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Default trust boundaries configuration"""
        return {
            "action_types": {
                "PURCHASE_ORDER": {
                    "low_risk_threshold": {
                        "cost_max": 50000,  # ₹50k
                        "vendor_whitelist": ["vendor_a", "vendor_b", "vendor_c"],
                        "item_categories_allowed": ["medical_supplies", "consumables"]
                    },
                    "medium_risk_threshold": {
                        "cost_max": 200000,  # ₹2L
                        "vendor_whitelist": ["vendor_a", "vendor_b", "vendor_c", "vendor_d"],
                        "item_categories_allowed": ["medical_supplies", "consumables", "equipment"]
                    },
                    "high_risk_threshold": {
                        "cost_max": 500000,  # ₹5L
                    },
                    "required_approvals": {
                        "LOW": [],
                        "MEDIUM": ["procurement_manager"],
                        "HIGH": ["procurement_manager", "finance_manager"],
                        "CRITICAL": ["procurement_manager", "finance_manager", "cmo"]
                    }
                },
                "STAFFING_CHANGE": {
                    "low_risk_threshold": {
                        "overtime_hours_max": 20,
                        "temp_staff_count_max": 5,
                        "department_restrictions": []
                    },
                    "medium_risk_threshold": {
                        "overtime_hours_max": 40,
                        "temp_staff_count_max": 10
                    },
                    "required_approvals": {
                        "LOW": [],
                        "MEDIUM": ["hr_manager"],
                        "HIGH": ["hr_manager", "department_head"],
                        "CRITICAL": ["hr_manager", "department_head", "cmo"]
                    }
                },
                "PATIENT_ADVISORY": {
                    "low_risk_threshold": {
                        "recipient_count_max": 2000,
                        "forbidden_keywords": ["prescription", "medication", "dosage"],
                        "advisory_types_allowed": ["pollution_alert", "surge_warning"]
                    },
                    "medium_risk_threshold": {
                        "recipient_count_max": 5000,
                        "advisory_types_allowed": ["pollution_alert", "surge_warning", "epidemic_alert"]
                    },
                    "required_approvals": {
                        "LOW": [],
                        "MEDIUM": ["communications_manager"],
                        "HIGH": ["communications_manager", "cmo"],
                        "CRITICAL": ["communications_manager", "cmo", "legal"]
                    }
                },
                "INVENTORY_TRANSFER": {
                    "low_risk_threshold": {
                        "value_max": 30000,  # ₹30k
                        "department_restrictions": []
                    },
                    "medium_risk_threshold": {
                        "value_max": 100000  # ₹1L
                    },
                    "required_approvals": {
                        "LOW": [],
                        "MEDIUM": ["inventory_manager"],
                        "HIGH": ["inventory_manager", "department_head"],
                        "CRITICAL": ["inventory_manager", "department_head", "cmo"]
                    }
                }
            },
            "global_rules": {
                "kill_switch_active": False,
                "max_autonomous_actions_per_hour": 50,
                "emergency_override": False
            }
        }
    
    def evaluate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate an action against trust boundaries
        
        Returns:
            {
                "can_execute": bool,
                "risk_level": RiskLevel,
                "reasons": List[str],
                "required_approvals": List[str],
                "execution_type": str
            }
        """
        action_type = action.get("type", "UNKNOWN")
        
        # Check kill switch
        if self.config.get("global_rules", {}).get("kill_switch_active", False):
            return {
                "can_execute": False,
                "risk_level": RiskLevel.CRITICAL,
                "reasons": ["Kill switch is active - all autonomous actions blocked"],
                "required_approvals": ["system_administrator"],
                "execution_type": "REJECTED"
            }
        
        # Get action-specific rules
        action_rules = self.config.get("action_types", {}).get(action_type, {})
        
        if not action_rules:
            # Unknown action type - require approval
            return {
                "can_execute": False,
                "risk_level": RiskLevel.HIGH,
                "reasons": [f"Unknown action type: {action_type}"],
                "required_approvals": ["system_administrator"],
                "execution_type": "PENDING"
            }
        
        # Evaluate risk level
        risk_level, reasons = self._evaluate_risk_level(action, action_rules)
        
        # Determine if can execute autonomously
        can_execute = risk_level == RiskLevel.LOW
        
        # Get required approvals
        required_approvals = action_rules.get("required_approvals", {}).get(risk_level.value, [])
        
        execution_type = "AUTONOMOUS" if can_execute else "PENDING"
        
        return {
            "can_execute": can_execute,
            "risk_level": risk_level.value,
            "reasons": reasons,
            "required_approvals": required_approvals,
            "execution_type": execution_type
        }
    
    def _evaluate_risk_level(self, action: Dict, action_rules: Dict) -> tuple[RiskLevel, List[str]]:
        """Evaluate the risk level for an action"""
        reasons = []
        risk_level = RiskLevel.LOW
        
        action_type = action.get("type")
        
        if action_type == "PURCHASE_ORDER":
            cost = action.get("cost", 0)
            vendor = action.get("vendor", "")
            item_category = action.get("item_category", "")
            
            low_threshold = action_rules.get("low_risk_threshold", {})
            medium_threshold = action_rules.get("medium_risk_threshold", {})
            high_threshold = action_rules.get("high_risk_threshold", {})
            
            # Check cost thresholds
            if cost > high_threshold.get("cost_max", 500000):
                risk_level = RiskLevel.CRITICAL
                reasons.append(f"Cost exceeds critical threshold: ₹{cost}")
            elif cost > medium_threshold.get("cost_max", 200000):
                risk_level = RiskLevel.HIGH
                reasons.append(f"Cost exceeds high threshold: ₹{cost}")
            elif cost > low_threshold.get("cost_max", 50000):
                risk_level = RiskLevel.MEDIUM
                reasons.append(f"Cost exceeds low threshold: ₹{cost}")
            
            # Check vendor whitelist
            vendor_whitelist = low_threshold.get("vendor_whitelist", [])
            if vendor and vendor not in vendor_whitelist:
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                reasons.append(f"Vendor not in whitelist: {vendor}")
            
            # Check item category
            allowed_categories = low_threshold.get("item_categories_allowed", [])
            if item_category and item_category not in allowed_categories:
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                reasons.append(f"Item category not allowed for low-risk: {item_category}")
        
        elif action_type == "STAFFING_CHANGE":
            overtime_hours = action.get("overtime_hours", 0)
            temp_staff_count = action.get("temp_staff_count", 0)
            
            low_threshold = action_rules.get("low_risk_threshold", {})
            medium_threshold = action_rules.get("medium_risk_threshold", {})
            
            if overtime_hours > medium_threshold.get("overtime_hours_max", 40):
                risk_level = RiskLevel.HIGH
                reasons.append(f"Overtime hours exceed threshold: {overtime_hours}h")
            elif overtime_hours > low_threshold.get("overtime_hours_max", 20):
                risk_level = RiskLevel.MEDIUM
                reasons.append(f"Overtime hours exceed low threshold: {overtime_hours}h")
            
            if temp_staff_count > medium_threshold.get("temp_staff_count_max", 10):
                risk_level = RiskLevel.HIGH
                reasons.append(f"Temp staff count exceeds threshold: {temp_staff_count}")
            elif temp_staff_count > low_threshold.get("temp_staff_count_max", 5):
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                reasons.append(f"Temp staff count exceeds low threshold: {temp_staff_count}")
        
        elif action_type == "PATIENT_ADVISORY":
            recipient_count = action.get("recipient_count", 0)
            message_content = action.get("message_content", "").lower()
            advisory_type = action.get("advisory_type", "")
            
            low_threshold = action_rules.get("low_risk_threshold", {})
            medium_threshold = action_rules.get("medium_risk_threshold", {})
            
            if recipient_count > medium_threshold.get("recipient_count_max", 5000):
                risk_level = RiskLevel.HIGH
                reasons.append(f"Recipient count exceeds threshold: {recipient_count}")
            elif recipient_count > low_threshold.get("recipient_count_max", 2000):
                risk_level = RiskLevel.MEDIUM
                reasons.append(f"Recipient count exceeds low threshold: {recipient_count}")
            
            # Check forbidden keywords
            forbidden_keywords = low_threshold.get("forbidden_keywords", [])
            for keyword in forbidden_keywords:
                if keyword in message_content:
                    risk_level = RiskLevel.HIGH
                    reasons.append(f"Message contains forbidden keyword: {keyword}")
                    break
            
            # Check advisory type
            allowed_types = low_threshold.get("advisory_types_allowed", [])
            if advisory_type and advisory_type not in allowed_types:
                if risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
                reasons.append(f"Advisory type not in low-risk allowed list: {advisory_type}")
        
        elif action_type == "INVENTORY_TRANSFER":
            value = action.get("value", 0)
            
            low_threshold = action_rules.get("low_risk_threshold", {})
            medium_threshold = action_rules.get("medium_risk_threshold", {})
            
            if value > medium_threshold.get("value_max", 100000):
                risk_level = RiskLevel.HIGH
                reasons.append(f"Transfer value exceeds threshold: ₹{value}")
            elif value > low_threshold.get("value_max", 30000):
                risk_level = RiskLevel.MEDIUM
                reasons.append(f"Transfer value exceeds low threshold: ₹{value}")
        
        if not reasons:
            reasons.append("Action within low-risk parameters")
        
        return risk_level, reasons

