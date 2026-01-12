"""
PDF Generation Utilities for VyaparMind Cold Storage
- Invoice generation
- Compliance certificates
- Temperature reports
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


def generate_invoice_pdf(invoice_data, filename):
    """
    Generate a professional invoice PDF.
    
    Args:
        invoice_data (dict): {
            'invoice_number': str,
            'client_name': str,
            'client_gst': str,
            'client_address': str,
            'invoice_date': str,
            'period_from': str,
            'period_to': str,
            'line_items': list of dicts,
            'subtotal': float,
            'gst_amount': float,
            'total': float
        }
        filename (str): Output PDF filename
    
    Returns:
        str: Path to generated PDF
    """
    
    # Create PDF
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#009FDF'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    # Header
    story.append(Paragraph("COLD STORAGE INVOICE", title_style))
    story.append(Paragraph("VyaparMind Cold Storage Solutions", header_style))
    story.append(Paragraph("GST: 36XXXXX1234X1ZX | Phone: +91-XXXXXXXXXX", header_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Invoice Details
    invoice_info = [
        ['Invoice Number:', invoice_data.get('invoice_number', 'N/A'), 'Invoice Date:', invoice_data.get('invoice_date', 'N/A')],
        ['Billing Period:', f"{invoice_data.get('period_from', 'N/A')} to {invoice_data.get('period_to', 'N/A')}", '', '']
    ]
    
    invoice_table = Table(invoice_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Bill To
    story.append(Paragraph("<b>Bill To:</b>", styles['Normal']))
    story.append(Paragraph(f"<b>{invoice_data.get('client_name', 'N/A')}</b>", styles['Normal']))
    story.append(Paragraph(f"GST: {invoice_data.get('client_gst', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Line Items Table
    line_items_data = [['Commodity', 'Lot #', 'Quantity', 'Pallets', 'Days', 'Rate', 'Amount']]
    
    for item in invoice_data.get('line_items', []):
        line_items_data.append([
            item.get('commodity', ''),
            item.get('lot', ''),
            f"{item.get('quantity', 0):.0f} {item.get('unit', 'KG')}",
            f"{item.get('pallets', 0)}",
            f"{item.get('days', 0)}",
            f"₹{item.get('rate', 0):.2f}",
            f"₹{item.get('amount', 0):.2f}"
        ])
    
    items_table = Table(line_items_data, colWidths=[1.5*inch, 1*inch, 1*inch, 0.8*inch, 0.7*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#009FDF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Totals
    totals_data = [
        ['Subtotal:', f"₹{invoice_data.get('subtotal', 0):.2f}"],
        ['GST (18%):', f"₹{invoice_data.get('gst_amount', 0):.2f}"],
        ['', ''],
        ['<b>TOTAL PAYABLE:</b>', f"<b>₹{invoice_data.get('total', 0):.2f}</b>"]
    ]
    
    totals_table = Table(totals_data, colWidths=[5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
        ('BACKGROUND', (1, 3), (1, 3), colors.HexColor('#FFCD00')),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Footer
    story.append(Paragraph("<i>Thank you for your business!</i>", header_style))
    story.append(Paragraph("This is a computer-generated invoice and does not require a signature.", header_style))
    
    # Build PDF
    doc.build(story)
    
    return filename


def generate_temperature_certificate_pdf(cert_data, filename):
    """
    Generate temperature compliance certificate.
    
    Args:
        cert_data (dict): {
            'client_name': str,
            'period': str,
            'compliance_rate': float,
            'breach_count': int,
            'total_readings': int
        }
        filename (str): Output PDF filename
    """
    
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#041E42'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Header
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("CERTIFICATE OF STORAGE", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Certificate Body
    cert_text = f"""
    <para alignment="justify">
    This is to certify that <b>{cert_data.get('client_name', 'N/A')}</b> has stored their goods 
    in our temperature-controlled cold storage facility during the period <b>{cert_data.get('period', 'N/A')}</b>.
    <br/><br/>
    <b>Storage Conditions:</b>
    <br/>
    - Temperature Compliance Rate: <b>{cert_data.get('compliance_rate', 0):.1f}%</b>
    <br/>
    - Total Temperature Readings: <b>{cert_data.get('total_readings', 0)}</b>
    <br/>
    - Temperature Breaches Detected: <b>{cert_data.get('breach_count', 0)}</b>
    <br/>
    - Quality Controls: <b>All inward and outward quality checks passed</b>
    <br/>
    - Certifications: <b>FSSAI Licensed Facility</b>
    <br/><br/>
    The storage was maintained as per industry standards with 24/7 temperature monitoring 
    and complete traceability. All goods were handled following FIFO/FEFO principles to 
    ensure maximum freshness and quality preservation.
    <br/><br/>
    </para>
    """
    
    story.append(Paragraph(cert_text, styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Signature Section
    story.append(Paragraph("_______________________", styles['Normal']))
    story.append(Paragraph("<b>Authorized Signatory</b>", styles['Normal']))
    story.append(Paragraph("VyaparMind Cold Storage", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    cert_id = f"CERT/{datetime.now().strftime('%Y%m%d')}/001"
    story.append(Paragraph(f"<i>Certificate ID: {cert_id}</i>", styles['Normal']))
    story.append(Paragraph(f"<i>Date: {datetime.now().strftime('%d %B %Y')}</i>", styles['Normal']))
    
    doc.build(story)
    return filename
