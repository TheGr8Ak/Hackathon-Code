# app/agents/press_secretary.py
import asyncio
import json
import logging
from typing import Dict, List, Any
logger = logging.getLogger(__name__)
from app.agents.level3_base_agent import Level3Agent
from app.core.rag import MedicalGuidelineRAG
from app.services.sms_service import SMSService
from app.services.email_service import EmailService
from app.database.patient_db import PatientDatabase

class PressSecretaryAgent(Level3Agent):
    """Patient communication agent - sends advisories using RAG"""
    
    def __init__(self):
        super().__init__("Press Secretary")
        self.sms_service = SMSService()
        self.email_service = EmailService()
        self.patient_db = PatientDatabase()
        self.medical_rag = MedicalGuidelineRAG()
        
        # Message templates for fallback
        self.templates = {
            'pollution_alert': "⚠️ Air quality alert: AQI {aqi}. Respiratory patients advised to stay indoors, use prescribed inhalers. Emergency: Call 108. - {hospital_name}",
            'epidemic_alert': "🚨 Health Advisory: {disease} cases detected in your area. Practice hygiene, avoid crowded places. Symptoms? Call {helpline}. - {hospital_name}",
            'surge_warning': "📢 Hospital Notice: High patient volume expected. Non-urgent cases may experience delays. Emergency care unaffected. - {hospital_name}"
        }
    
    async def create_and_send_advisory(self, event_type: str, severity: str, details: Dict) -> Dict:
        """Create and send patient advisory using RAG"""
        
        logger.info(f"Creating {event_type} advisory with {severity} severity")
        
        # Generate message using RAG
        message = await self._generate_advisory_message(event_type, severity, details)
        
        # Get target audience
        recipients = await self._get_target_patients(event_type, severity)
        
        if len(recipients) == 0:
            logger.warning(f"No recipients found for {event_type} advisory")
            return {'status': 'SKIPPED', 'reason': 'No eligible recipients'}
        
        # Construct action
        action = {
            'type': 'PATIENT_ADVISORY',
            'advisory_type': event_type,
            'message_content': message,
            'recipient_count': len(recipients),
            'recipient_list': recipients[:100],  # Store sample for audit
            'severity': severity,
            'channel': 'SMS',  # Primary channel
            'reasoning': f"{event_type.upper()} event with {severity} severity. {len(recipients)} at-risk patients identified based on medical history.",
            'details': details
        }
        
        # Execute through Level 3 framework
        result = await self.propose_and_execute(action)
        return result
    
    async def _generate_advisory_message(self, event_type: str, severity: str, details: Dict) -> str:
        """Generate message using RAG (medical guidelines)"""
        
        try:
            # Query medical guideline database
            guidelines = await self.medical_rag.retrieve_guidelines(
                query=f"{event_type} patient advisory {severity} precautions",
                filters={'approved': True, 'language': 'en', 'type': 'public_health'},
                top_k=3
            )
            
            # Build context from RAG results
            guideline_text = "\n".join([g['content'] for g in guidelines])
            
            # Use Gemini to draft message
            prompt = f"""
Draft a patient health advisory SMS (max 160 characters) for the following situation:

Event Type: {event_type}
Severity: {severity}
Details: {json.dumps(details)}

Medical Guidelines to Follow:
{guideline_text}

Requirements:
- Clear, simple language (8th grade reading level)
- Actionable advice only
- Include emergency contact: 108
- Reassuring but urgent tone
- Must fit in 160 characters
- No medical prescriptions (only general advice)
- Include hospital name placeholder: {{hospital_name}}

Generate ONLY the SMS text, nothing else.
"""
            
            # Note: google-genai client is synchronous, so we run it in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
            )
            
            message = response.text.strip()
            
            # Safety checks
            if self._contains_medical_prescription(message):
                raise ValueError("Message contains medical prescription - requires CMO approval")
            
            if len(message) > 160:
                logger.warning(f"Message too long ({len(message)} chars). Truncating.")
                message = message[:157] + "..."
            
            # Replace placeholders
            message = message.replace('{hospital_name}', details.get('hospital_name', 'City Hospital'))
            message = message.replace('{aqi}', str(details.get('aqi', 'N/A')))
            
            return message
            
        except Exception as e:
            logger.error(f"RAG message generation failed: {e}. Using template.")
            # Fallback to template
            return self._get_template_message(event_type, details)
    
    def _get_template_message(self, event_type: str, details: Dict) -> str:
        """Fallback to predefined template"""
        template = self.templates.get(event_type, self.templates['surge_warning'])
        
        return template.format(
            aqi=details.get('aqi', 200),
            disease=details.get('disease', 'infectious disease'),
            helpline='108',
            hospital_name=details.get('hospital_name', 'City Hospital')
        )
    
    async def _get_target_patients(self, event_type: str, severity: str) -> List[Dict]:
        """Identify which patients should receive advisory"""
        
        if event_type == "pollution_alert":
            # Target respiratory patients
            patients = await self.patient_db.query_patients(
                conditions=['asthma', 'COPD', 'chronic_bronchitis', 'emphysema'],
                active_status=True,
                consent_sms=True,
                last_visit_days=90  # Active patients only
            )
        
        elif event_type == "epidemic_alert":
            # Target immunocompromised and elderly
            patients = await self.patient_db.query_patients(
                tags=['immunocompromised', 'elderly_65plus', 'chronic_illness', 'diabetes'],
                active_status=True,
                consent_sms=True
            )
        
        elif event_type == "surge_warning":
            # Target all active patients with upcoming appointments
            patients = await self.patient_db.query_patients(
                has_upcoming_appointment=True,
                appointment_within_days=7,
                consent_sms=True
            )
        
        else:
            # General broadcast
            patients = await self.patient_db.query_patients(
                active_status=True,
                consent_sms=True,
                limit=1000  # Rate limiting
            )
        
        return patients
    
    async def execute_action(self, action: Dict) -> Any:
        """Send SMS/Email to patients"""
        
        if action['type'] == 'PATIENT_ADVISORY':
            sent_count = 0
            failed_count = 0
            failed_recipients = []
            
            # Send in batches to avoid rate limiting
            batch_size = 100
            recipient_list = action['recipient_list']
            
            for i in range(0, len(recipient_list), batch_size):
                batch = recipient_list[i:i+batch_size]
                
                for recipient in batch:
                    try:
                        await self.sms_service.send(
                            to=recipient['phone'],
                            message=action['message_content'],
                            sender_id="HOSPITAL",
                            priority='high' if action['severity'] == 'CRITICAL' else 'normal'
                        )
                        sent_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        failed_recipients.append({
                            'patient_id': recipient['id'],
                            'error': str(e)
                        })
                        logger.error(f"Failed to send SMS to {recipient['id']}: {e}")
                    
                    # Rate limit: 10 SMS per second
                    await asyncio.sleep(0.1)
                
                # Batch delay
                if i + batch_size < len(recipient_list):
                    await asyncio.sleep(5)
            
            logger.info(f"SMS campaign complete: {sent_count} sent, {failed_count} failed")
            
            return {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'failed_recipients': failed_recipients[:10],  # Store first 10 failures
                'message': action['message_content'],
                'total_recipients': action['recipient_count']
            }
    
    async def verify_outcome(self, action: Dict, result: Dict) -> Dict:
        """Check if patients responded or complaints received"""
        # Wait 24 hours for feedback
        await asyncio.sleep(86400)

        # Robustly get timestamp and sent_count
        action_timestamp = action.get('timestamp') if isinstance(action, dict) else None
        sent_count = 0
        if isinstance(result, dict):
            sent_count = result.get('sent_count', 0)

        # Check complaint logs
        complaints = await self.patient_db.get_complaints(
            related_to_message=action.get('message_content', '') if isinstance(action, dict) else '',
            timeframe_hours=24
        )

        # Check opt-out requests (use timestamp if available)
        if action_timestamp:
            opt_outs = await self.patient_db.get_opt_out_requests(
                after_message_timestamp=action_timestamp
            )
        else:
            opt_outs = await self.patient_db.get_opt_out_requests()

        # Calculate success metrics
        complaint_rate = len(complaints) / sent_count if sent_count > 0 else 0
        opt_out_rate = len(opt_outs) / sent_count if sent_count > 0 else 0

        # Check if emergency calls increased (indicating people followed advice)
        if action_timestamp:
            emergency_calls = await self.patient_db.get_emergency_call_count(
                after_timestamp=action_timestamp,
                hours=24
            )
        else:
            emergency_calls = await self.patient_db.get_emergency_call_count(hours=24)

        if complaint_rate > 0.05:  # More than 5% complaints
            return {
                'success': False,
                'notes': f"High complaint rate: {complaint_rate:.2%}. {len(complaints)} complaints received."
            }

        if opt_out_rate > 0.10:  # More than 10% opt-outs
            return {
                'success': False,
                'notes': f"High opt-out rate: {opt_out_rate:.2%}. Message may have been intrusive."
            }

        return {
            'success': True,
            'notes': f"Advisory well-received. Complaints: {len(complaints)}, Opt-outs: {len(opt_outs)}, Emergency calls: {emergency_calls}",
            'metrics': {
                'complaint_rate': round(complaint_rate, 4),
                'opt_out_rate': round(opt_out_rate, 4),
                'emergency_calls': emergency_calls
            }
        }
    
    def _contains_medical_prescription(self, message: str) -> bool:
        """Check if message contains medical advice requiring CMO approval"""
        forbidden_keywords = [
            'take', 'medication', 'dosage', 'mg', 'tablet', 'prescription',
            'drug', 'medicine', 'pill', 'dose', 'inject'
        ]
        
        message_lower = message.lower()
        
        for keyword in forbidden_keywords:
            if keyword in message_lower:
                return True
        
        return False
