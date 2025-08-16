#!/usr/bin/env python3
"""
Check SMS message status and troubleshoot delivery issues
"""

from config import get_twilio_client, MY_PHONE, TWILIO_PHONE

def check_sms_status():
    """Check recent SMS message status"""
    try:
        client = get_twilio_client()
        
        print("📱 Checking SMS Status...")
        print(f"From: {TWILIO_PHONE}")
        print(f"To: {MY_PHONE}")
        print("="*50)
        
        # Get recent messages
        messages = client.messages.list(limit=10)
        
        if not messages:
            print("❌ No messages found in Twilio console")
            return
            
        for i, msg in enumerate(messages, 1):
            print(f"\n📨 Message {i}:")
            print(f"  SID: {msg.sid}")
            print(f"  Status: {msg.status}")
            print(f"  Error Code: {msg.error_code if msg.error_code else 'None'}")
            print(f"  Error Message: {msg.error_message if msg.error_message else 'None'}")
            print(f"  To: {msg.to}")
            print(f"  From: {msg.from_}")
            print(f"  Body: {msg.body[:100]}{'...' if len(msg.body) > 100 else ''}")
            print(f"  Date Created: {msg.date_created}")
            print(f"  Price: {msg.price} {msg.price_unit}")
            
            # Status meanings
            status_info = {
                'queued': '🟡 Queued for delivery',
                'sending': '🟡 Currently sending',
                'sent': '🟢 Successfully sent to carrier',
                'delivered': '✅ Delivered to recipient',
                'undelivered': '❌ Failed to deliver',
                'failed': '❌ Failed to send'
            }
            
            print(f"  Status Meaning: {status_info.get(msg.status, 'Unknown status')}")
            
        # Check account balance
        print("\n💰 Account Info:")
        account = client.api.accounts(client.account_sid).fetch()
        print(f"  Account Status: {account.status}")
        
        # Get balance
        balance = client.balance.fetch()
        print(f"  Balance: {balance.balance} {balance.currency}")
        
    except Exception as e:
        print(f"❌ Error checking SMS status: {e}")
        import traceback
        traceback.print_exc()


def test_simple_sms():
    """Send a simple test SMS"""
    try:
        from alert import send_alert
        
        print("\n🧪 Sending Test SMS...")
        message = "🧪 TEST: CrowdSense SMS is working! This is a test message."
        
        sms_sid = send_alert(message)
        print(f"✅ Test SMS sent successfully!")
        print(f"📱 SID: {sms_sid}")
        print("📞 Check your phone for the message.")
        
    except Exception as e:
        print(f"❌ Error sending test SMS: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔍 CrowdSense SMS Troubleshooting Tool")
    print("="*50)
    
    # Check existing message status
    check_sms_status()
    
    # Ask if user wants to send test
    print("\n" + "="*50)
    choice = input("📤 Send a test SMS now? (y/n): ").lower().strip()
    
    if choice == 'y':
        test_simple_sms()
        
        # Check status again after test
        print("\n🔄 Checking status after test...")
        check_sms_status()
    
    print("\n📋 Common Issues & Solutions:")
    print("1. ❌ Status 'failed' or 'undelivered': Check phone number format")
    print("2. ❌ No messages: Check Twilio credentials")
    print("3. ⏳ Status 'sent' but not received: Carrier delay (try different carrier)")
    print("4. 💰 Low balance: Add credits to Twilio account")
    print("5. 🌍 International SMS: May take longer or be blocked by carrier")
    print("6. 📱 Spam filter: Check spam/junk folder on phone")
    print("7. 🔢 Phone format: Ensure number includes country code (+91 for India)")
