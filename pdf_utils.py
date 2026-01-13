"""
PDF Generation Utilities for VyaparMind Cold Storage
- Premium Invoice generation
- Compliance certificates
- Temperature reports
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from datetime import datetime
import os

# --- BRANDING CONFIG ---
COLOR_PRIMARY = colors.HexColor("#009FDF") # Blue
COLOR_ACCENT = colors.HexColor("#FFCD00")  # Yellow
COLOR_DARK = colors.HexColor("#333333")
LOGO_FILENAME = "logo_no_text_1.svg"

def draw_logo(canvas, path, x, y, max_height=50, anchor='nw'):
    """Draws Logo (SVG or Image) at coords, scaling to fit max_height"""
    try:
        if not os.path.exists(path):
            return
            
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.svg':
            drawing = svg2rlg(path)
            if not drawing: return
            
            iw, ih = drawing.width, drawing.height
            factor = max_height / ih
            drawing.scale(factor, factor)
            draw_y = y - (ih * factor) if anchor == 'nw' else y
            renderPDF.draw(drawing, canvas, x, draw_y)
            
        elif ext in ['.png', '.jpg', '.jpeg']:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(path)
            iw, ih = img.getSize()
            factor = max_height / ih
            
            w = iw * factor
            h = ih * factor
            
            draw_y = y - h if anchor == 'nw' else y
            canvas.drawImage(path, x, draw_y, width=w, height=h, mask='auto')
            
    except Exception as e:
        print(f"Error drawing Logo: {e}")

def draw_header_footer(canvas, doc):
    """Draws Premium Header and Footer on every page"""
    canvas.saveState()
    w, h = A4
    
    # Extract Branding
    branding = getattr(doc, 'branding_info', {})
    logo_path = branding.get('logo_path', LOGO_FILENAME)
    company_name = branding.get('company_name', "VyaparMind Cold Storage Solutions")
    gst_num = branding.get('gst', "GST: Pending")
    phone_num = branding.get('phone', "")
    subtext = f"GST: {gst_num}"
    if phone_num:
        subtext += f" | {phone_num}"
    
    # --- HEADER ---
    # Logo
    draw_logo(canvas, logo_path, 40, h-20, max_height=60, anchor='nw')
    
    # Header Text
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(COLOR_DARK)
    canvas.drawRightString(w-40, h-45, company_name)
    
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w-40, h-58, subtext)
    
    # Decorative Line
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(40, h-75, w-40, h-75)
    
    # --- FOOTER ---
    # Blue Strip
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(0, 0, w, 50, fill=1, stroke=0)
    # Yellow Strip
    canvas.setFillColor(COLOR_ACCENT)
    canvas.rect(0, 50, w, 4, fill=1, stroke=0)
    
    # Footer Text
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(w/2, 28, "Thank You for Your Business!")
    
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w/2, 15, f"{company_name} | Powered by VyaparMind")
    
    # Page Number
    canvas.drawRightString(w-20, 15, f"Page {doc.page}")
    
    canvas.restoreState()

def generate_invoice_pdf(invoice_data, filename):
    """
    Generate a PREMIUM professional invoice PDF.
    
    Args:
        invoice_data (dict): Standard invoice data dictionary
        filename (str): Output PDF filename
    
    Returns:
        str: Path to generated PDF
    """
    
    # Layout
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=100, bottomMargin=70)
    
    # Pass branding info to doc for callback
    doc.branding_info = invoice_data.get('branding', {})
    
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-40, id='normal')
    template = PageTemplate(id='PremiumInvoice', frames=frame, onPage=draw_header_footer)
    doc.addPageTemplates([template])
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle('InvTitle', parent=styles['Heading1'], fontSize=24, textColor=COLOR_PRIMARY, alignment=TA_RIGHT, spaceAfter=20)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    style_value = ParagraphStyle('Value', parent=styles['Normal'], fontSize=10, textColor=COLOR_DARK, fontName='Helvetica-Bold')
    style_normal = ParagraphStyle('Norm', parent=styles['Normal'], fontSize=10, textColor=COLOR_DARK)
    
    # --- TITLE ---
    story.append(Paragraph("INVOICE", style_title))
    
    # --- INFO GRID ---
    # Left: Bill To, Right: Invoice Details
    
    # Bill To Block
    bill_to = [
        [Paragraph("<b>BILL TO:</b>", style_label)],
        [Paragraph(invoice_data.get('client_name', 'N/A'), style_value)],
        [Paragraph(invoice_data.get('client_address', ''), style_normal)],
        [Paragraph(f"GST: {invoice_data.get('client_gst', 'N/A')}", style_normal)],
    ]
    
    # Invoice Details Block
    inv_details = [
        [Paragraph("Invoice Number:", style_label), Paragraph(invoice_data.get('invoice_number', 'N/A'), style_value)],
        [Paragraph("Invoice Date:", style_label), Paragraph(invoice_data.get('invoice_date', 'N/A'), style_value)],
        [Paragraph("Billing Period:", style_label), Paragraph(f"{invoice_data.get('period_from')} to {invoice_data.get('period_to')}", style_value)],
    ]
    
    # Layout Grid
    grid_data = [[
        Table(bill_to, colWidths=[3*inch]), 
        Table(inv_details, colWidths=[1.5*inch, 2*inch])
    ]]
    
    grid = Table(grid_data, colWidths=[3.5*inch, 3.5*inch])
    grid.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(grid)
    story.append(Spacer(1, 0.5*inch))
    
    # --- LINE ITEMS ---
    headers = ['Commodity', 'Lot #', 'Qty', 'Pallets', 'Days', 'Rate', 'Amount']
    data = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in headers]]
    
    for item in invoice_data.get('line_items', []):
        data.append([
            item.get('commodity', ''),
            item.get('lot', ''),
            f"{item.get('quantity', 0):.0f}",
            str(item.get('pallets', 0)),
            str(item.get('days', 0)),
            f"Rs.{item.get('rate', 0):.2f}",
            f"Rs.{item.get('amount', 0):.2f}"
        ])
        
    t = Table(data, colWidths=[1.8*inch, 1*inch, 0.8*inch, 0.6*inch, 0.6*inch, 1*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Commodities left align
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))
    
    # --- TOTALS ---
    totals = [
        ['Subtotal:', f"Rs.{invoice_data.get('subtotal', 0):,.2f}"],
        ['GST (18%):', f"Rs.{invoice_data.get('gst_amount', 0):,.2f}"],
        ['', ''],
        ['TOTAL PAYABLE:', f"Rs.{invoice_data.get('total', 0):,.2f}"]
    ]
    
    tot_table = Table(totals, colWidths=[5*inch, 2*inch])
    tot_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 12),
        ('TEXTCOLOR', (0, 3), (-1, 3), COLOR_PRIMARY),
        ('LINEABOVE', (0, 3), (-1, 3), 1, COLOR_DARK),
    ]))
    story.append(tot_table)
    
    # --- TERMS ---
    story.append(Spacer(1, 0.8*inch))
    story.append(Paragraph("Terms & Conditions:", style_value))
    terms = """
    1. Payment is due within 15 days of invoice date.
    2. Interest @ 18% p.a. will be charged on delayed payments.
    3. Goods stored at owner's risk.
    """
    story.append(Paragraph(terms, style_label))
    
    doc.build(story)
    return filename

def generate_temperature_certificate_pdf(cert_data, filename):
    """
    Generate a PREMIUM Temperature Compliance Certificate.
    
    Args:
        cert_data (dict): {
            'branding': dict,
            'client_name': str,
            'period': str,
            'compliance_rate': float,
            'breach_count': int,
            'total_readings': int,
            'cert_id': str,
            'date': str
        }
        filename (str): Output PDF filename
    """
    
    # Layout with Premium Template
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=110, bottomMargin=70)
    
    # Pass branding info
    doc.branding_info = cert_data.get('branding', {})
    
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-40, id='normal')
    template = PageTemplate(id='Certificate', frames=frame, onPage=draw_header_footer)
    doc.addPageTemplates([template])
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle('CertTitle', parent=styles['Heading1'], fontSize=22, textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=20)
    style_subtitle = ParagraphStyle('CertSub', parent=styles['Normal'], fontSize=12, textColor=COLOR_DARK, alignment=TA_CENTER, spaceAfter=30)
    style_body = ParagraphStyle('CertBody', parent=styles['Normal'], fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12)
    style_label = ParagraphStyle('CertLabel', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    style_val = ParagraphStyle('CertVal', parent=styles['Normal'], fontSize=11, textColor=COLOR_DARK, fontName='Helvetica-Bold')
    
    # CONTENT
    story.append(Paragraph("CERTIFICATE OF STORAGE", style_title))
    story.append(Paragraph("Temperature & Quality Compliance", style_subtitle))
    
    story.append(Spacer(1, 0.2*inch))
    
    intro_text = f"""
    This is to certify that <b>{cert_data.get('client_name', 'N/A')}</b> has stored their goods 
    in our temperature-controlled cold storage facility during the period:
    """
    story.append(Paragraph(intro_text, style_body))
    story.append(Paragraph(f"<b>{cert_data.get('period', 'N/A')}</b>", style_subtitle))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Metrics Table
    metrics_data = [
        [Paragraph("Temperature Compliance Rate", style_label), Paragraph(f"{cert_data.get('compliance_rate', 0):.1f}%", style_val)],
        [Paragraph("Total Temperature Readings", style_label), Paragraph(str(cert_data.get('total_readings', 0)), style_val)],
        [Paragraph("Breaches Detected", style_label), Paragraph(str(cert_data.get('breach_count', 0)), style_val)],
        [Paragraph("Storage Standards", style_label), Paragraph("FSSAI Compliant, FIFO/FEFO Protocol", style_val)],
    ]
    
    t = Table(metrics_data, colWidths=[3*inch, 3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(t)
    
    story.append(Spacer(1, 0.3*inch))
    
    footer_text = """
    The storage was maintained as per industry standards with 24/7 temperature monitoring 
    and complete traceability. All goods were handled following strict quality control protocols 
    to ensure maximum freshness and preservation.
    """
    story.append(Paragraph(footer_text, style_body))
    
    story.append(Spacer(1, 0.8*inch))
    
    # Signature Block
    sig_data = [
        [Paragraph("Authorized Signatory", style_label), Paragraph(f"Certificate ID: {cert_data.get('cert_id')}", style_label)],
        [Paragraph(f"<b>{cert_data.get('branding', {}).get('company_name', 'VyaparMind Data')}</b>", style_val), Paragraph(f"Date: {cert_data.get('date')}", style_label)],
        [Image("assets/seal_placeholder.png", width=1.5*inch, height=0.5*inch) if os.path.exists("assets/seal_placeholder.png") else "", ""]
    ]
    
    sig_table = Table(sig_data, colWidths=[3.5*inch, 2.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.black), # Line for signature
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return filename
