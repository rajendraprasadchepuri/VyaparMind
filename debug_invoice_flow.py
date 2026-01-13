import database as db
import pdf_utils
import email_utils
import os
from datetime import datetime

# 1. Fetch a client
print("Fetching clients...")
clients_df = db.get_all_storage_clients()
if clients_df.empty:
    print("❌ No clients found!")
    exit()

# Pick the first client with an email
client = None
for _, row in clients_df.iterrows():
    if row['email'] and '@' in row['email']:
        client = row
        break

if client is None:
    print("❌ No client with a valid email found!")
    exit()

print(f"✅ Selected Client: {client['company_name']} ({client['email']})")

# 2. Prepare Dummy Invoice Data
print("Preparing invoice data...")
dummy_items = [{
    'commodity': 'Test Item', 
    'lot': 'LOT-123', 
    'quantity': 1000, 
    'unit': 'KG', 
    'pallets': 2, 
    'days': 30, 
    'rate': 50, 
    'amount': 3000
}]
invoice_data = {
    'invoice_number': 'INV/TEST/001',
    'client_name': client['company_name'],
    'client_gst': client['gst_number'] or 'N/A',
    'client_address': client['email'],
    'invoice_date': datetime.now().strftime('%d-%b-%Y'),
    'period_from': '2025-01-01',
    'period_to': '2025-01-31',
    'line_items': dummy_items,
    'subtotal': 3000,
    'gst_amount': 540,
    'total': 3540
}

# 3. Generate PDF
print("Generating PDF...")
try:
    pdf_filename = f"Debug_Invoice.pdf"
    pdf_path = pdf_utils.generate_invoice_pdf(invoice_data, pdf_filename)
    print(f"✅ PDF Generated at: {pdf_path}")
    print(f"   Size: {os.path.getsize(pdf_path)} bytes")
except Exception as e:
    print(f"❌ PDF Generation Failed: {e}")
    exit()

# 4. Send Email
print(f"Sending email to {client['email']}...")
subject = "Debug Invoice Test"
body = "<h3>This is a debug test for invoice PDF attachment.</h3>"

try:
    success, msg = email_utils.send_email_report(client['email'], subject, body, attachment_path=pdf_path)
    if success:
        print(f"✅ Email Sent Successfully!")
    else:
        print(f"❌ Email Failed: {msg}")
except Exception as e:
    print(f"❌ Email Exception: {e}")

# Cleanup
# if os.path.exists(pdf_path):
#    os.remove(pdf_path)
#    print("Cleaned up PDF.")
