import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- CONFIGURATION ---
ARTIFACT_DIR = r"C:\Users\rajendraprasad\.gemini\antigravity\brain\711bc411-6a9a-4751-a928-8432f3507221"
OUTPUT_DIR = r"c:\rpworkspace\VyaparMind\documentation"
LOGO_PATH = r"c:\rpworkspace\VyaparMind\assets\uploads\logo_O5SQLRP2SQV2KNLM.png"

# Verify Logo
if not os.path.exists(LOGO_PATH):
    print(f"Warning: Logo not found at {LOGO_PATH}. Searching for alternatives...")
    # Fallback search
    upload_dir = r"c:\rpworkspace\VyaparMind\assets\uploads"
    found = False
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            if f.startswith("logo") and f.endswith(".png"):
                LOGO_PATH = os.path.join(upload_dir, f)
                found = True
                break
    if not found:
        print("No logo found. Skipping logo.")
        LOGO_PATH = None
else:
    print(f"Using Logo: {LOGO_PATH}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def add_header(canvas, doc):
    """Draws logo at Top Left of the page"""
    canvas.saveState()
    if LOGO_PATH:
        try:
            # Top Left Coords: x=30, y=Height-70
            page_width, page_height = A4
            # Draw Logo (Height ~ 50px)
            canvas.drawImage(LOGO_PATH, 30, page_height - 70, height=40, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error drawing logo: {e}")
            
    # Add Footer with Page Number
    canvas.setFont('Helvetica', 9)
    page_num = canvas.getPageNumber()
    text = "VyaparMind ERP - Confidential"
    canvas.drawString(30, 30, text)
    canvas.drawRightString(A4[0] - 30, 30, f"Page {page_num}")
    canvas.restoreState()

def parse_markdown_to_flowables(md_content, styles):
    flowables = []
    lines = md_content.split('\n')
    
    # Styles
    title_style = styles['Title']
    h1_style = styles['Heading1']
    h1_style.spaceBefore = 10
    h1_style.spaceAfter = 10
    
    h2_style = styles['Heading2']
    h2_style.spaceBefore = 12
    h2_style.textColor = colors.HexColor("#009FDF") # Brand Blue
    
    h3_style = styles['Heading3']
    h3_style.spaceBefore = 10
    
    normal_style = styles['BodyText']
    normal_style.alignment = TA_LEFT
    normal_style.spaceAfter = 6
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['BodyText'],
        fontName='Courier',
        fontSize=8,
        backColor=colors.lightgrey,
        borderPadding=5
    )
    
    in_code_block = False
    code_buffer = []

    for line in lines:
        stripped = line.strip()
        
        # Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                # End block
                in_code_block = False
                full_code = "<br/>".join(code_buffer)
                p = Paragraph(full_code, code_style)
                flowables.append(p)
                flowables.append(Spacer(1, 6))
                code_buffer = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_buffer.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Skip empty lines
        if not stripped:
            continue
            
        # Headers
        if line.startswith("# "):
            flowables.append(Spacer(1, 20)) # Space before title
            flowables.append(Paragraph(line[2:].strip(), title_style))
            flowables.append(Spacer(1, 20))
        elif line.startswith("## "):
            flowables.append(Paragraph(line[3:].strip(), h2_style))
        elif line.startswith("### "):
            flowables.append(Paragraph(line[4:].strip(), h3_style))
        elif line.startswith("#### "):
            p = Paragraph(f"<b>{line[5:].strip()}</b>", normal_style)
            flowables.append(p)
            
        # Horizontal Rule
        elif line.startswith("---"):
            flowables.append(PageBreak())
            
        # Lists
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            # Bold Logic: Convert **text** to <b>text</b>
            content = line.strip()[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            
            p = Paragraph(f"• {content}", normal_style)
            p.leftIndent = 20
            flowables.append(p)
            
        # Tables (Too complex for simple parser, rendering as code block text)
        elif line.strip().startswith("|"):
            p = Paragraph(line, code_style)
            flowables.append(p)
            
        # Normal Text
        else:
            content = line
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content) # Bold
            content = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', content) # Inline code
            flowables.append(Paragraph(content, normal_style))
            
    return flowables

def generate_pdf(source_file, output_name):
    print(f"Generating {output_name}...")
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        doc = SimpleDocTemplate(
            os.path.join(OUTPUT_DIR, output_name),
            pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=80, bottomMargin=50 # Top Margin 80 to fit Logo
        )
        
        styles = getSampleStyleSheet()
        story = parse_markdown_to_flowables(content, styles)
        
        doc.build(story, onFirstPage=add_header, onLaterPages=add_header)
        print(f"✅ Created: {os.path.join(OUTPUT_DIR, output_name)}")
        return True
    except Exception as e:
        print(f"❌ Failed to generate {output_name}: {e}")
        return False

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    files_to_process = [
        ("product_proposal.md", "VyaparMind_Product_Proposal.pdf"),
        ("user_manual.md", "VyaparMind_User_Manual.pdf"),
        ("technical_documentation.md", "VyaparMind_Technical_Assessment.pdf")
    ]
    
    success_count = 0
    for md_file, pdf_name in files_to_process:
        full_path = os.path.join(ARTIFACT_DIR, md_file)
        if os.path.exists(full_path):
            if generate_pdf(full_path, pdf_name):
                success_count += 1
        else:
            print(f"Skipping {md_file} (Not found at {full_path})")
            
    print(f"\nCompleted. {success_count}/{len(files_to_process)} documents generated.")
