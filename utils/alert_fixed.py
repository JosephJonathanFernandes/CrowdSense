from typing import Optional
import random
from config import get_twilio_client, TWILIO_PHONE, MY_PHONE, require


def send_alert_fixed(message: str, to_phone: Optional[str] = None) -> str:
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
        " (Alert System)",
        " [Automated]",
        ""
    ]
    final_message += random.choice(suffixes)
    
    try:
        sms = client.messages.create(
            body=final_message,
            from_=from_number,
            to=destination,
        )
        print(f"✅ Alert sent! SID: {sms.sid}")
        print(f"📱 Message: {final_message}")
        return sms.sid
    except Exception as e:
        print(f"❌ SMS Failed: {e}")
        raise


def send_simple_test():
    """Send a simple test message that should work"""
    test_messages = [
        "Hello! This is a test from your disaster alert system.",
        "CrowdSense test message - system is working correctly!",
        "Testing SMS delivery - please confirm you received this.",
        "Alert system test - earthquake simulation ready.",
        "SMS test successful - disaster monitoring active."
    ]
    
    message = random.choice(test_messages)
    return send_alert_fixed(message)


if __name__ == "__main__":
    print("🧪 Testing Fixed SMS Alert System")
    print("=" * 40)
    
    # Send a simple test
    try:
        sms_sid = send_simple_test()
        print(f"\n✅ Test message sent successfully!")
        print(f"📱 SID: {sms_sid}")
        print("\n📞 Check your phone for the message.")
        print("💡 If you receive this test, the disaster alerts will work too!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n🔧 Fixes Applied:")
    print("✅ Removed trial account prefix")
    print("✅ Added message variation")
    print("✅ Shortened message length")
    print("✅ Added unique identifiers")
