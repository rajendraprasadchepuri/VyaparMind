import pdf_utils
import os
import datetime

# Dummy Data for Visualization
invoice_data = {
    'invoice_number': 'INV/2025/PREMIUM/001',
    'client_name': 'TechCorp Solutions Pvt Ltd',
    'client_address': '123 Innovation Park, Hyderabad, India',
    'client_gst': '36ABCDE1234F1Z5',
    'invoice_date': datetime.datetime.now().strftime('%d-%b-%Y'),
    'period_from': '01-Jan-2025',
    'period_to': '31-Jan-2025',
    'line_items': [
        {'commodity': 'Frozen Peas', 'lot': 'LOT-101', 'quantity': 5000, 'pallets': 10, 'days': 30, 'rate': 50, 'amount': 15000},
        {'commodity': 'Ice Cream', 'lot': 'LOT-102', 'quantity': 2000, 'pallets': 4, 'days': 15, 'rate': 60, 'amount': 3600},
        {'commodity': 'Butter', 'lot': 'LOT-103', 'quantity': 1000, 'pallets': 2, 'days': 30, 'rate': 55, 'amount': 3300},
        {'commodity': 'Cheese', 'lot': 'LOT-104', 'quantity': 500, 'pallets': 1, 'days': 10, 'rate': 50, 'amount': 500},
    ],
    'subtotal': 22400,
    'gst_amount': 4032,
    'total': 26432
}

filename = "Premium_Invoice_Test.pdf"

try:
    print(f"Generating {filename}...")
    pdf_utils.generate_invoice_pdf(invoice_data, filename)
    print(f"✅ Success! Generated {filename}")
    print(f"File Size: {os.path.getsize(filename)} bytes")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
