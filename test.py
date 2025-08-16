import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables
load_dotenv()


def test_twilio():
    """Simple test to verify Twilio SMS is working"""
    try:
        # Get credentials from .env file
        account_sid = os.getenv("TWILIO_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone = os.getenv("TWILIO_PHONE")
        my_phone = os.getenv("MY_PHONE")

        print(f"📱 Testing Twilio SMS...")
        print(f"From: {twilio_phone}")
        print(f"To: {my_phone}")

        # Create Twilio client
        client = Client(account_sid, auth_token)

        # Send test message
        message = client.messages.create(
            body="Hi this is me.. Testing Twilio SMS from CrowdSense! 🚀",
            from_=twilio_phone,
            to=my_phone,
        )

        print(f"✅ Message sent successfully!")
        print(f"Message SID: {message.sid}")
        print(f"Status: {message.status}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_twilio()
