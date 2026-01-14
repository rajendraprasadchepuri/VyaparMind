import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate, NextPageTemplate, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from datetime import datetime
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

# --- CONFIGURATION ---
ARTIFACT_DIR = r"C:\Users\rajendraprasad\.gemini\antigravity\brain\e21ad827-c418-4d6f-8655-7ac42fe024b4"
OUTPUT_DIR = r"c:\rpworkspace\VyaparMind\documentation"
# PRIMARY LOGO
LOGO_PATH = r"c:\rpworkspace\VyaparMind\logo_no_text_1.svg"

# COLORS
COLOR_PRIMARY = colors.HexColor("#009FDF") # Blue
COLOR_ACCENT = colors.HexColor("#FFCD00")  # Yellow
COLOR_DARK = colors.HexColor("#333333")

os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()

# Styles
style_title = ParagraphStyle('DocTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=26, textColor=COLOR_PRIMARY, spaceAfter=10, alignment=TA_CENTER)
style_h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=COLOR_PRIMARY, spaceBefore=15, spaceAfter=8)
style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=COLOR_DARK, spaceBefore=12, spaceAfter=6)
style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=14, spaceAfter=6, alignment=TA_JUSTIFY)
style_bullet = ParagraphStyle('Bullet', parent=style_body, leftIndent=15, firstLineIndent=0)

def draw_svg(canvas, path, x, y, max_height=50, anchor='nw'):
    """Draws SVG at coords, scaling to fit max_height"""
    try:
        if not os.path.exists(path):
            return
            
        drawing = svg2rlg(path)
        if not drawing:
            return

        # Calculate scale
        iw = drawing.width
        ih = drawing.height
        factor = max_height / ih
        
        drawing.scale(factor, factor)
        
        # Position adjustments based on scaled size
        w = iw * factor
        h = ih * factor
        
        # Coords are usually Bottom-Left in ReportLab canvas, BUT svglib helps place it?
        # Actually renderPDF.draw(d, c, x, y) puts the BL of drawing at x,y
        # We need to adjust.
        # ReportLab coordinate system: (0,0) is bottom-left.
        
        # Adjust for anchor
        draw_x = x
        draw_y = y 
        
        if anchor == 'nw':
            # y is top, x is left
            # Drawing is drawn from bottom-up relative to its origin?
            # Actually renderPDF draws it relative to current user space.
            draw_y = y - h
            
        renderPDF.draw(drawing, canvas, draw_x, draw_y)
        
    except Exception as e:
        print(f"Error drawing SVG: {e}")

def draw_cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    
    # Header Strip
    canvas.setFillColor(colors.whitesmoke)
    canvas.rect(0, h-100, w, 100, fill=1, stroke=0)
    
    # Logo Center
    draw_svg(canvas, LOGO_PATH, (w/2)-75, h-150, max_height=100, anchor='nw') # Approximate centering logic
    # Actually simpler: Draw logo at specific spot
    draw_svg(canvas, LOGO_PATH, 40, h-30, max_height=60, anchor='nw') 
    
    # Footer Strip
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(0, 0, w, 60, fill=1, stroke=0)
    canvas.setFillColor(COLOR_ACCENT)
    canvas.rect(0, 60, w, 5, fill=1, stroke=0)
    
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(w/2, 25, "VyaparMind ERP Solutions")
    
    canvas.restoreState()

def draw_page_header(canvas, doc):
    canvas.saveState()
    w, h = A4
    
    # Header Line
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(40, h-60, w-40, h-60)
    
    # Logo Top Left (Header)
    draw_svg(canvas, LOGO_PATH, 40, h-20, max_height=30, anchor='nw')
    
    # Header Text
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(COLOR_DARK)
    canvas.drawRightString(w-40, h-35, "VyaparMind Documentation")
    
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w-40, h-45, datetime.now().strftime("%Y-%m-%d"))

    # Footer
    canvas.line(40, 40, w-40, 40)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(40, 25, "Confidential - Internal Use Only")
    canvas.drawRightString(w-40, 25, f"Page {doc.page}")
    
    canvas.restoreState()

def parse_md(text):
    flowables = []
    lines = text.split('\n')
    
    table_buf = []
    
    def flush_table():
        if not table_buf: return
        data = [[Paragraph(c.strip(), style_body) for c in r.strip('|').split('|') if c] for r in table_buf]
        if data:
            cols = len(data[0])
            t = Table(data, colWidths=[A4[0]/cols - 20]*cols) # Auto width
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            flowables.append(t)
            flowables.append(Spacer(1, 10))
        table_buf.clear()

    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith('|'):
            if '---' in line: continue
            table_buf.append(line)
            continue
        
        flush_table()
        
        if line.startswith('# '):
            flowables.append(NextPageTemplate('Normal'))
            flowables.append(Spacer(1, 2 * inch))
            flowables.append(Paragraph(line[2:], style_title))
            flowables.append(Spacer(1, 10))
            flowables.append(PageBreak())
        elif line.startswith('## '):
            flowables.append(Paragraph(line[3:], style_h1))
        elif line.startswith('### '):
            flowables.append(Paragraph(line[4:], style_h2))
        elif line.startswith('- ') or line.startswith('* '):
            p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line[2:])
            flowables.append(Paragraph(f"• {p}", style_bullet))
        else:
            p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            flowables.append(Paragraph(p, style_body))
            
    flush_table()
    return flowables

def gen_pdf(src, dst):
    doc = SimpleDocTemplate(dst, pagesize=A4, topMargin=80, bottomMargin=60)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=frame, onPage=draw_cover),
        PageTemplate(id='Normal', frames=frame, onPage=draw_page_header)
    ])
    
    with open(src, 'r', encoding='utf-8') as f:
        story = parse_md(f.read())
    
    doc.build(story)
    print(f"Generated {dst}")

if __name__ == '__main__':
    for f, out in [("VyaparMind_Industry_Map.md", "VyaparMind_Industry_Map.pdf"),
                   ("implementation_plan.md", "VyaparMind_Implementation_Plan.pdf"),
                   ("pharma_use_case_plan.md", "VyaparMind_Pharma_Use_Case.pdf"),
                   ("task.md", "VyaparMind_Task.pdf"),
                   ("walkthrough.md", "VyaparMind_Walkthrough.pdf"),
                   ("VyaparMind_Module_Catalog.md", "VyaparMind_Module_Catalog.pdf")]:
        gen_pdf(os.path.join(ARTIFACT_DIR, f), os.path.join(OUTPUT_DIR, out))
