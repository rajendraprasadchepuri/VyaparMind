import pdf_utils
import os
import datetime

# Dummy Certificate Data
cert_data = {
    'branding': {
        'company_name': 'Voltas Cold Storage',
        'address': 'Plot 42, Industrial Area, Mumbai',
        'phone': '+91-9998887776',
        'gst': '27AAAAA0000A1Z5',
        'logo_path': 'logo_no_text_1.svg' 
    },
    'client_name': 'TechCorp Solutions',
    'period': 'Last 30 Days',
    'compliance_rate': 99.8,
    'breach_count': 0,
    'total_readings': 1500,
    'cert_id': 'CERT/TEST/001',
    'date': datetime.datetime.now().strftime('%d %B %Y')
}

filename = "Test_Certificate.pdf"

try:
    print(f"Generating {filename}...")
    pdf_utils.generate_temperature_certificate_pdf(cert_data, filename)
    print(f"✅ Success! Generated {filename}")
    print(f"File Size: {os.path.getsize(filename)} bytes")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
