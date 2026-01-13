"""
Email Reporting Utility for VyaparMind Cold Storage
- Weekly Status Reports
- Invoices
- Expiry Digests
"""

import os
from datetime import datetime

def send_email_report(to_email, subject, body_html, attachment_path=None):
    """
    Send email with optional attachment.
    
    Args:
        to_email (str): Recipient email
        subject (str): Email subject
        body_html (str): HTML body content
        attachment_path (str): Path to file attachment (optional)
    """
    
    # DEMO MODE: Print to console
    """
    print(f'''
    ═══════════════════════════════════════════════
    📧 EMAIL REPORTING (DEMO MODE)
    ═══════════════════════════════════════════════
    TO: {to_email}
    SUBJECT: {subject}
    TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ATTACHMENT: {attachment_path if attachment_path else 'None'}
    
    BODY:
    {body_html[:500]}... (preview)
    ═══════════════════════════════════════════════
    
    ⚠️ To enable real Email sending:
    1. Configure SMTP settings in .env
    2. Uncomment production code in email_utils.py
    ''')
    
    return True, "DEMO_EMAIL_SENT"
    """
    
    # PRODUCTION CODE (Uncomment when ready)
    
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SMTP_EMAIL')
    sender_password = os.getenv('SMTP_PASSWORD')
    
    if not all([sender_email, sender_password]):
        return False, "SMTP credentials not configured"
        
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_html, 'html'))
    
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)
        
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def generate_weekly_html(client_name, data):
    """Generate HTML template for weekly report."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #009FDF;">Weekly Storage Report</h2>
        <p>Dear {client_name},</p>
        <p>Here is your inventory summary for the week:</p>
        
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ddd; padding: 8px;">Metric</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Value</th>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><b>Total Inventory</b></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{data.get('total_kg', 0):,.0f} KG</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><b>Avg Temperature Compliance</b></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{data.get('compliance_pct', 100)}%</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;"><b>Expiring Soon (<7 days)</b></td>
                <td style="border: 1px solid #ddd; padding: 8px; color: red;">{data.get('expiring_kg', 0):,.0f} KG</td>
            </tr>
        </table>
        
        <p>Login to your portal for full details.</p>
        <p>- VyaparMind Cold Storage</p>
    </body>
    </html>
    """
