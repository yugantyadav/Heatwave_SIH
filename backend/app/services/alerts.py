# Alerts service
from app.core.config import settings

class AlertService:
    @classmethod
    async def send_sms(cls, phone_number: str, message: str):
        if not settings.TWILIO_ACCOUNT_SID:
            return {"status": "sandbox", "channel": "sms", "message": message}
        # Production Twilio integration would go here
        return {"status": "sent", "channel": "sms", "to": phone_number}

    @classmethod
    async def send_whatsapp(cls, phone_number: str, message: str):
        if not settings.WHATSAPP_BUSINESS_ACCOUNT_ID:
            return {"status": "sandbox", "channel": "whatsapp", "message": message}
        # Production WhatsApp Cloud API integration would go here
        return {"status": "sent", "channel": "whatsapp", "to": phone_number}