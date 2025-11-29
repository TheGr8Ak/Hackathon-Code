"""
Email Service - Placeholder for email functionality
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class EmailService:
    """Email service (placeholder for future implementation)"""
    
    def __init__(self):
        logger.info("Email service initialized (mock mode)")
    
    async def send(self, to: str, subject: str, body: str) -> Dict:
        """Send email (mock implementation)"""
        logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}")
        return {
            "status": "sent",
            "to": to,
            "mock": True
        }

