import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import random
from utils.config import get_twilio_client, TWILIO_PHONE, MY_PHONE, require


def send_alert(message: str, to_phone: Optional[str] = None) -> str:
    """
    Send an SMS alert via Twilio with carrier-friendly formatting
    
    Fixes for Error 30044 (Carrier Filtering):
    1. Remove trial account prefix
    2. Add random variation to prevent spam detection
    3. Use cleaner message format
    """
    client = get_twilio_client()
    from_number = require(TWILIO_PHONE, "TWILIO_PHONE")
    destination = require(to_phone or MY_PHONE, "MY_PHONE")
    
    # Clean up message - remove trial prefix if present
    clean_message = message
    if "Sent from your Twilio trial account -" in clean_message:
        clean_message = clean_message.replace("Sent from your Twilio trial account - ", "")
    
    # Add variation to prevent spam filtering
    variations = [
        "🚨 CrowdSense Alert: ",
        "⚠️ Disaster Alert: ",
        "🔔 Emergency Notice: ",
        "📢 Alert System: ",
        "🚨 Warning: "
    ]
    
    # Add random variation prefix
    prefix = random.choice(variations)
    
    # Keep message concise to avoid filtering
    if len(clean_message) > 140:
        clean_message = clean_message[:137] + "..."
    
    final_message = prefix + clean_message
    
    # Add random suffix to make each message unique
    suffixes = [
        " #CrowdSense",
        " -CS",
        " (Alert)",
        " [Auto]",
        ""
    ]
    final_message += random.choice(suffixes)
    
    sms = client.messages.create(
        body=final_message,
        from_=from_number,
        to=destination,
    )
    print(f"✅ Alert sent! SID: {sms.sid}")
    print(f"📱 Message: {final_message}")
    return sms.sid


if __name__ == "__main__":
    send_alert("🚨 Test Alert from CrowdSense!Hi Pratik")
    
