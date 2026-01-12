"""
WhatsApp Alerts Utility for VyaparMind Cold Storage
- Temperature breach alerts
- Expiry notifications
- Delivery confirmations
Uses Twilio API (commented out for demo - requires API keys)
"""

from datetime import datetime


def send_whatsapp_alert(to_phone, message):
    """
    Send WhatsApp message using Twilio API.
    
    Args:
        to_phone (str): Phone number in format '+919876543210'
        message (str): Message text to send
    
    Returns:
        tuple: (success, message_id or error)
    """
    
    # DEMO MODE: Print to console instead of sending
    # To enable: Uncomment Twilio code and add credentials
    
    print(f"""
    ═══════════════════════════════════════════════
    📱 WHATSAPP ALERT (DEMO MODE)
    ═══════════════════════════════════════════════
    TO: {to_phone}
    TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    MESSAGE:
    {message}
    ═══════════════════════════════════════════════
    
    ⚠️ To enable real WhatsApp alerts:
    1. Sign up at https://www.twilio.com/whatsapp
    2. Get Account SID, Auth Token, WhatsApp number
    3. Uncomment Twilio code below
    4. Add credentials to .env file
    """)
    
    return True, "DEMO_MESSAGE_ID"
    
    # PRODUCTION CODE (Uncomment when ready):
    """
    try:
        from twilio.rest import Client
        import os
        
        # Get credentials from environment
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_whatsapp = os.getenv('TWILIO_WHATSAPP_NUMBER')  # e.g., 'whatsapp:+14155238886'
        
        if not all([account_sid, auth_token, from_whatsapp]):
            return False, "Twilio credentials not configured"
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message
        message = client.messages.create(
            from_=from_whatsapp,
            body=message,
            to=f'whatsapp:{to_phone}'
        )
        
        return True, message.sid
        
    except Exception as e:
        return False, str(e)
    """


def send_temperature_breach_alert(zone_name, recorded_temp, target_min, target_max, manager_phone='+919876543210'):
    """
    Send alert when temperature breach detected.
    
    Args:
        zone_name (str): Name of the zone
        recorded_temp (float): Actual temperature
        target_min (float): Minimum safe temperature
        target_max (float): Maximum safe temperature
        manager_phone (str): Manager's WhatsApp number
    """
    
    message = f"""
🚨 TEMPERATURE BREACH ALERT 🚨

Zone: {zone_name}
Recorded: {recorded_temp}°C
Safe Range: {target_min}°C to {target_max}°C
Time: {datetime.now().strftime('%d-%b-%Y %H:%M')}

⚠️ IMMEDIATE ACTION REQUIRED
Check equipment and take corrective action.

- VyaparMind Cold Storage
"""
    
    return send_whatsapp_alert(manager_phone, message.strip())


def send_expiry_alert(client_name, client_phone, commodity_name, lot_number, days_to_expiry, quantity):
    """
    Send alert to client about expiring inventory.
    
    Args:
        client_name (str): Client company name
        client_phone (str): Client WhatsApp number
        commodity_name (str): Product name
        lot_number (str): Lot number
        days_to_expiry (int): Days until expiry
        quantity (float): Quantity in KG
    """
    
    urgency = "🔴 URGENT" if days_to_expiry <= 7 else "🟡 NOTICE"
    
    message = f"""
{urgency} - Expiry Alert

Dear {client_name},

Your inventory is approaching expiry:

Item: {commodity_name}
Lot #: {lot_number}
Quantity: {quantity} KG
Expires in: {days_to_expiry} days

Please arrange pickup/dispatch at earliest.

Contact us: 9876543210

- VyaparMind Cold Storage
"""
    
    return send_whatsapp_alert(client_phone, message.strip())


def send_delivery_confirmation(client_name, client_phone, delivery_number, items_count, dispatch_date):
    """
    Send delivery confirmation to client.
    
    Args:
        client_name (str): Client company name
        client_phone (str): Client WhatsApp number
        delivery_number (str): Delivery note number
        items_count (int): Number of items
        dispatch_date (str): Dispatch date
    """
    
    message = f"""
✅ Delivery Confirmation

Dear {client_name},

Your goods have been dispatched!

Delivery #: {delivery_number}
Items: {items_count}
Date: {dispatch_date}

Track your delivery or contact us at:
📞 9876543210

Thank you for choosing us!

- VyaparMind Cold Storage
"""
    
    return send_whatsapp_alert(client_phone, message.strip())


def send_weekly_summary(client_name, client_phone, compliance_rate, breach_count, total_inventory_kg):
    """
    Send weekly temperature compliance summary to client.
    
    Args:
        client_name (str): Client company name
        client_phone (str): Client WhatsApp number
        compliance_rate (float): Compliance percentage
        breach_count (int): Number of breaches
        total_inventory_kg (float): Total inventory quantity
    """
    
    message = f"""
📊 Weekly Storage Report

Dear {client_name},

Summary for week ending {datetime.now().strftime('%d-%b-%Y')}:

✅ Temperature Compliance: {compliance_rate:.1f}%
🌡️ Breaches Detected: {breach_count}
📦 Current Inventory: {total_inventory_kg:,.0f} KG

All your goods are being stored under optimal conditions.

View detailed reports: [Portal Link]

- VyaparMind Cold Storage
"""
    
    return send_whatsapp_alert(client_phone, message.strip())


# Configuration helper
def setup_whatsapp_config():
    """
    Display setup instructions for WhatsApp alerts.
    """
    return """
    🔧 WhatsApp Alerts Setup Guide
    ================================
    
    1. Create Twilio Account:
       - Visit: https://www.twilio.com/try-twilio
       - Sign up (Free trial available)
    
    2. Enable WhatsApp:
       - Go to Twilio Console → Messaging → Try it out
       - Follow WhatsApp sandbox setup
       - Get your WhatsApp-enabled number
    
    3. Get Credentials:
       - Account SID: Found in Console Dashboard
       - Auth Token: Found in Console Dashboard
       - WhatsApp Number: From WhatsApp sandbox
    
    4. Configure VyaparMind:
       - Create .env file in project root
       - Add:
         TWILIO_ACCOUNT_SID=your_account_sid
         TWILIO_AUTH_TOKEN=your_auth_token
         TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
         MANAGER_PHONE=+919876543210
    
    5. Install Twilio SDK:
       - Run: pip install twilio
    
    6. Uncomment production code in whatsapp_utils.py
    
    Cost: ~$0.005 per message (approx ₹0.40)
    Free tier: $15 credit (3000+ messages)
    """
