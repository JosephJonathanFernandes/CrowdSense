import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

def send_alert(message):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_PHONE")
    my_phone = os.getenv("MY_PHONE")

    client = Client(account_sid, auth_token)
    sms = client.messages.create(
        body=message,
        from_=twilio_phone,
        to=my_phone
    )
    print(f"✅ Alert sent! SID: {sms.sid}")

if __name__ == "__main__":
    send_alert("🚨 Test Alert from CrowdSense!")
