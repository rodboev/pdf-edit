from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PyPDF2 import PdfReader
import re
from decimal import Decimal

def extract_positions(pdf_path):
    """Extract positions of text elements from the PDF."""
    positions = []
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    
    def visitor_body(text, cm, tm, fontDict, fontSize):
        x = tm[4]
        y = tm[5]
        if '$' in text:
            positions.append({
                'text': text.strip(),
                'x': x,
                'y': y,
                'font': fontDict,
                'size': fontSize
            })
    
    page.extract_text(visitor_text=visitor_body)
    return positions

def create_corrected_pdf(input_path: str, output_path: str):
    """Create a new PDF with corrected values."""
    # Get positions from original PDF
    positions = extract_positions(input_path)
    
    # Create a new PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Set font
    c.setFont("Helvetica", 12)
    
    # Print positions for debugging
    print("\nFound text elements:")
    for pos in positions:
        print(f"Text: {pos['text']}, Position: ({pos['x']:.2f}, {pos['y']:.2f})")
        
        # Replace values
        text = pos['text']
        if text == '$217.75':
            text = '$200.00'
        elif text == '$0.00' and pos['y'] < 500:  # Only replace the tax amount
            text = '$35.50'
        
        # Draw text at the same position
        c.drawString(pos['x'], pos['y'], text)
    
    # Save the PDF
    c.save()
    print(f"\nCreated new PDF with corrected values at {output_path}")

if __name__ == "__main__":
    input_pdf = "pdfs/incorrect.pdf"
    output_pdf = "pdfs/corrected.pdf"
    create_corrected_pdf(input_pdf, output_pdf) 