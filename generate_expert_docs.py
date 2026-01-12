import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate, NextPageTemplate, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm, mm
from reportlab.pdfgen import canvas
from datetime import datetime
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

# --- CONFIGURATION ---
ARTIFACT_DIR = r"C:\Users\rajendraprasad\.gemini\antigravity\brain\711bc411-6a9a-4751-a928-8432f3507221"
OUTPUT_DIR = r"c:\rpworkspace\VyaparMind\documentation"
LOGO_PATH = r"c:\rpworkspace\VyaparMind\logo_no_text_1.svg"

# BRAND COLORS
COLOR_PRIMARY = colors.HexColor("#009FDF")  # Vyapar Blue
COLOR_ACCENT = colors.HexColor("#FFCD00")   # Vyapar Yellow
COLOR_DARK = colors.HexColor("#212529")     # Deep Grey (Almost Black)
COLOR_TEXT = colors.HexColor("#444444")     # Standard Text
COLOR_LIGHT_ACCENT = colors.HexColor("#E3F2FD") # Light Blue background for tables

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- TYPOGRAPHY ---
styles = getSampleStyleSheet()

# 1. Document Title (Cover Page Only)
style_doc_title = ParagraphStyle(
    'DocTitle', 
    parent=styles['Heading1'], 
    fontName='Helvetica-Bold', 
    fontSize=32, 
    leading=40,
    textColor=COLOR_PRIMARY, 
    spaceAfter=30, 
    alignment=TA_LEFT
)

style_doc_sub = ParagraphStyle(
    'DocSub', 
    parent=styles['Heading2'], 
    fontName='Helvetica', 
    fontSize=14, 
    leading=20,
    textColor=colors.grey, 
    spaceAfter=60, 
    alignment=TA_LEFT
)

# 2. Section Headers
style_h1 = ParagraphStyle(
    'H1', 
    parent=styles['Heading1'], 
    fontName='Helvetica-Bold', 
    fontSize=20, 
    leading=24,
    textColor=COLOR_PRIMARY, 
    spaceBefore=24, 
    spaceAfter=12,
    borderWidth=0,
    borderPadding=0
)

style_h2 = ParagraphStyle(
    'H2', 
    parent=styles['Heading2'], 
    fontName='Helvetica-Bold', 
    fontSize=14, 
    leading=18,
    textColor=COLOR_DARK, 
    spaceBefore=18, 
    spaceAfter=8
)

# 3. Body Text (Professional Readability)
style_body = ParagraphStyle(
    'Body', 
    parent=styles['Normal'], 
    fontName='Helvetica', 
    fontSize=10, 
    leading=16,  # Generous leading for readability
    spaceAfter=12, 
    alignment=TA_JUSTIFY,
    textColor=COLOR_TEXT
)

style_bullet = ParagraphStyle(
    'Bullet', 
    parent=style_body, 
    leftIndent=24, 
    firstLineIndent=-12, # Hanging indent
    spaceAfter=8
)

# --- GRAPHICS UTILS ---
def draw_svg(canvas, path, x, y, width=None, height=None, anchor='nw'):
    """Draws SVG. Specify EITHER width OR height to scale proportionately."""
    try:
        if not os.path.exists(path): return
        d = svg2rlg(path)
        if not d: return

        # Scale Logic
        if width and not height:
            factor = width / d.width
        elif height and not width:
            factor = height / d.height
        elif width and height:
            factor = min(width/d.width, height/d.height)
        else:
            factor = 1.0

        d.scale(factor, factor)
        d.width *= factor
        d.height *= factor
        
        # Draw Coords
        dx, dy = x, y
        if anchor == 'nw':
            dy -= d.height
        elif anchor == 'sw':
            pass # default
        elif anchor == 'c':
            dx -= d.width / 2
            dy -= d.height / 2
            
        renderPDF.draw(d, canvas, dx, dy)
    except Exception as e:
        print(f"SVG Error: {e}")

# --- PAGE TEMPLATES ---

def cover_page_bg(canvas, doc):
    """
    Business Professional Cover Page
    - Left colored sidebar
    - Logo top left (in white area)
    - Content will flow into the white area
    """
    canvas.saveState()
    w, h = A4
    
    # 1. Accent Sidebar (Left)
    sidebar_w = 1.5 * cm
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(0, 0, sidebar_w, h, fill=1, stroke=0)
    
    # 2. Top-Right Accent Line
    canvas.setFillColor(COLOR_ACCENT)
    canvas.rect(sidebar_w, h - 1.5*cm, w-sidebar_w, 0.2*cm, fill=1, stroke=0)
    
    # 3. Logo (Large, Top Left relative to content area)
    draw_svg(canvas, LOGO_PATH, sidebar_w + 1*cm, h - 2.5*cm, height=1.2*inch, anchor='nw')
    
    # 4. Bottom Footer Metadata (Date/Version)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(sidebar_w + 1*cm, 3*cm, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawString(sidebar_w + 1*cm, 3*cm - 12, "Confidential - For Internal Use Only")
    
    canvas.restoreState()

def header_footer(canvas, doc):
    """
    Standard Page: minimal header, clean footer
    """
    canvas.saveState()
    w, h = A4
    
    # --- HEADER ---
    # Logo Small (Top Left)
    draw_svg(canvas, LOGO_PATH, 2*cm, h - 1*cm, height=0.4*inch, anchor='nw')
    
    # Doc Title (Top Right)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w - 2.5*cm, h - 1.35*cm, "VyaparMind Documentation")
    
    # Line
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, h - 1.8*cm, w - 2*cm, h - 1.8*cm)
    
    # --- FOOTER ---
    # Line
    canvas.line(2*cm, 1.8*cm, w - 2*cm, 1.8*cm)
    
    # Page Number (Right)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w - 2.5*cm, 1.2*cm, f"Page {doc.page}")
    
    # Brand (Left)
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.drawString(2*cm, 1.2*cm, "VyaparMind ERP")
    
    canvas.restoreState()

from xml.sax.saxutils import escape

# --- PARSER ---
def parse_markdown(text):
    flowables = []
    lines = text.split('\n')
    
    # Table Buffer
    table_rows = []
    
    def render_table():
         if not table_rows: return
         
         # Convert text to Paragraphs
         data = []
         for r in table_rows:
             cells = r.strip('|').split('|')
             # Filter empty split results if any (like start/end pipe)
             row_data = []
             for c in cells:
                 c_raw = escape(c.strip())
                 c_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c_raw)
                 row_data.append(Paragraph(c_text, style_body))
             data.append(row_data)
             
         if data:
             cols = len(data[0])
             # Intelligent Widths: Column availability
             # A4 width = 210mm. Margins = 2.5cm L + 2cm R = 4.5cm. Available ~16.5cm
             available_w = A4[0] - (4.5*cm)
             col_w = available_w / cols
             
             t = Table(data, colWidths=[col_w]*cols)
             t.setStyle(TableStyle([
                 ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY), # Header Blue
                 ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                 ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                 ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                 ('VALIGN', (0,0), (-1,-1), 'TOP'),
                 ('PADDING', (0,0), (-1,-1), 8),
                 ('BOTTOMPADDING', (0,0), (-1,0), 12),
                 ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                 ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, COLOR_LIGHT_ACCENT]), # Zebra
             ]))
             flowables.append(t)
             flowables.append(Spacer(1, 16))
         
         table_rows.clear()

    # Pre-process Title
    # Looking for first H1 for Cover Page Title
    title_found = False
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Table Logic
        if line.startswith('|'):
            if '---' in line: continue # Skip separator
            table_rows.append(line)
            continue
        else:
            render_table()

        # Headers
        if line.startswith('# '):
            if not title_found: # COVER PAGE TITLE
                flowables.append(NextPageTemplate('Normal')) # Switch after cover
                # Push Text Down for Cover
                flowables.append(Spacer(1, 8*cm)) 
                flowables.append(Paragraph(line[2:], style_doc_title))
                flowables.append(Paragraph("Comprehensive Documentation Suite", style_doc_sub))
                flowables.append(PageBreak())
                title_found = True
            else:
                flowables.append(Paragraph(line[2:], style_h1))
                
        elif line.startswith('## '):
            flowables.append(Paragraph(line[3:], style_h1)) # Map H2 -> H1 style visually
        elif line.startswith('### '):
            flowables.append(Paragraph(line[4:], style_h2))
            
        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            txt_raw = escape(line[2:])
            txt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', txt_raw)
            flowables.append(Paragraph(f"• {txt}", style_bullet))
            
        # Normal Text
        else:
            txt_raw = escape(line)
            txt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', txt_raw)
            # Inline Code
            txt = re.sub(r'`(.*?)`', r'<font face="Courier" color="#E83E8C">\1</font>', txt)
            flowables.append(Paragraph(txt, style_body))
            
    render_table()
    return flowables

def generate_pdf(src_path, dest_path):
    print(f"Processing {src_path}...")
    
    # Doc Layout
    doc = SimpleDocTemplate(
        dest_path, 
        pagesize=A4,
        leftMargin=2.5*cm, # Professional Margins
        rightMargin=2.0*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm
    )
    
    # Frames
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    
    templates = [
        PageTemplate(id='Cover', frames=frame, onPage=cover_page_bg),
        PageTemplate(id='Normal', frames=frame, onPage=header_footer)
    ]
    doc.addPageTemplates(templates)
    
    with open(src_path, 'r', encoding='utf-8') as f:
        story = parse_markdown(f.read())
        
    doc.build(story)
    print(f"✅ Expert PDF Created: {dest_path}")

if __name__ == "__main__":
    docs = [
        ("product_proposal.md", "VyaparMind_Proposal_Expert.pdf"),
        ("user_manual.md", "VyaparMind_Manual_Expert.pdf"),
        ("technical_documentation.md", "VyaparMind_Tech_Expert.pdf")
    ]
    
    for s, d in docs:
        in_p = os.path.join(ARTIFACT_DIR, s)
        out_p = os.path.join(OUTPUT_DIR, d)
        if os.path.exists(in_p):
            generate_pdf(in_p, out_p)
