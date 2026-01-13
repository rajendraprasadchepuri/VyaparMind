import pdf_utils
import os
import datetime

# Dummy Data with CUSTOM BRANDING to verify dynamic loading
invoice_data = {
    'branding': {
        'company_name': 'My Custom Cold Store',
        'address': 'Plot 42, Industrial Area, Mumbai',
        'phone': '+91-9998887776',
        'gst': '27AAAAA0000A1Z5',
        'logo_path': 'logo_no_text_1.svg' 
    },
    'invoice_number': 'INV/2025/DYN/003',
    'client_name': 'Super Client Ltd',
    'client_address': 'HYD',
    'client_gst': '36ABCDE1234F1Z5',
    'invoice_date': datetime.datetime.now().strftime('%d-%b-%Y'),
    'period_from': '01-Mar-2025',
    'period_to': '31-Mar-2025',
    'line_items': [
        {'commodity': 'Apples', 'lot': 'LOT-201', 'quantity': 500, 'pallets': 1, 'days': 30, 'rate': 50, 'amount': 1500},
    ],
    'subtotal': 1500,
    'gst_amount': 270,
    'total': 1770
}

filename = "Premium_Invoice_Dynamic.pdf"

try:
    print(f"Generating {filename}...")
    pdf_utils.generate_invoice_pdf(invoice_data, filename)
    print(f"✅ Success! Generated {filename}")
    print(f"File Size: {os.path.getsize(filename)} bytes")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
