"""
Patient Database - Mock patient database for Press Secretary
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class PatientDatabase:
    """Mock patient database"""
    
    def __init__(self):
        # Mock patient data
        self.patients = self._generate_mock_patients()
        logger.info(f"Patient database initialized with {len(self.patients)} mock patients")
    
    def _generate_mock_patients(self) -> List[Dict]:
        """Generate mock patient data"""
        patients = []
        
        # Respiratory patients
        for i in range(500):
            patients.append({
                "id": f"PAT_{i:04d}",
                "phone": f"+91-{random.randint(7000000000, 9999999999)}",
                "conditions": ["asthma"] if i % 2 == 0 else ["COPD"],
                "tags": ["respiratory"],
                "active_status": True,
                "consent_sms": True,
                "last_visit_days": random.randint(1, 90),
                "has_upcoming_appointment": i % 3 == 0,
                "appointment_within_days": random.randint(1, 7) if i % 3 == 0 else None
            })
        
        # Immunocompromised/elderly
        for i in range(300):
            patients.append({
                "id": f"PAT_{500+i:04d}",
                "phone": f"+91-{random.randint(7000000000, 9999999999)}",
                "conditions": ["diabetes", "hypertension"],
                "tags": ["elderly_65plus", "chronic_illness"],
                "active_status": True,
                "consent_sms": True,
                "last_visit_days": random.randint(1, 180)
            })
        
        return patients
    
    async def query_patients(
        self,
        conditions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        active_status: Optional[bool] = None,
        consent_sms: Optional[bool] = None,
        last_visit_days: Optional[int] = None,
        has_upcoming_appointment: Optional[bool] = None,
        appointment_within_days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Query patients based on criteria"""
        results = []
        
        for patient in self.patients:
            # Filter by conditions
            if conditions:
                if not any(cond in patient.get("conditions", []) for cond in conditions):
                    continue
            
            # Filter by tags
            if tags:
                if not any(tag in patient.get("tags", []) for tag in tags):
                    continue
            
            # Filter by active status
            if active_status is not None:
                if patient.get("active_status") != active_status:
                    continue
            
            # Filter by consent
            if consent_sms is not None:
                if patient.get("consent_sms") != consent_sms:
                    continue
            
            # Filter by last visit
            if last_visit_days:
                if patient.get("last_visit_days", 999) > last_visit_days:
                    continue
            
            # Filter by upcoming appointment
            if has_upcoming_appointment is not None:
                if patient.get("has_upcoming_appointment") != has_upcoming_appointment:
                    continue
            
            # Filter by appointment within days
            if appointment_within_days:
                appt_days = patient.get("appointment_within_days")
                if not appt_days or appt_days > appointment_within_days:
                    continue
            
            results.append(patient)
            
            if limit and len(results) >= limit:
                break
        
        return results
    
    async def get_complaints(
        self,
        related_to_message: Optional[str] = None,
        timeframe_hours: int = 24
    ) -> List[Dict]:
        """Get patient complaints (mock)"""
        # Mock: return 0-5 complaints randomly
        count = random.randint(0, 5)
        return [{"id": f"COMP_{i}", "message": related_to_message} for i in range(count)]
    
    async def get_opt_out_requests(
        self,
        after_message_timestamp: Optional[str] = None
    ) -> List[Dict]:
        """Get opt-out requests (mock)"""
        # Mock: return 0-3 opt-outs randomly
        count = random.randint(0, 3)
        return [{"id": f"OPTOUT_{i}"} for i in range(count)]
    
    async def get_emergency_call_count(
        self,
        after_timestamp: Optional[str] = None,
        hours: int = 24
    ) -> int:
        """Get emergency call count (mock)"""
        # Mock: return random count
        return random.randint(10, 50)

