"""
SMS Service - Sends SMS via Twilio (or mock)
"""
import logging
import os
from typing import Dict, Optional
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service using Twilio"""
    
    def __init__(self):
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if account_sid and auth_token:
            try:
                self.client = TwilioClient(account_sid, auth_token)
                self.enabled = True
                logger.info("SMS service initialized with Twilio")
            except Exception as e:
                logger.warning(f"Twilio initialization failed: {e}. Using mock mode.")
                self.client = None
                self.enabled = False
        else:
            logger.warning("Twilio credentials not found. Using mock mode.")
            self.client = None
            self.enabled = False
    
    async def send(
        self,
        to: str,
        message: str,
        sender_id: str = "HOSPITAL",
        priority: str = "normal"
    ) -> Dict:
        """
        Send SMS
        
        Args:
            to: Recipient phone number
            message: Message content
            sender_id: Sender identifier
            priority: Message priority (normal/high)
        
        Returns:
            Dict with status, message_sid
        """
        if not self.enabled or not self.client:
            # Mock SMS sending
            logger.info(f"[MOCK SMS] To: {to}, Message: {message[:50]}...")
            return {
                "status": "sent",
                "message_sid": f"mock_{to}_{hash(message)}",
                "to": to,
                "mock": True
            }
        
        try:
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            logger.info(f"SMS sent to {to}: {result.sid}")
            return {
                "status": "sent",
                "message_sid": result.sid,
                "to": to,
                "mock": False
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {e}")
            raise

