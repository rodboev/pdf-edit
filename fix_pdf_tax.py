import PyPDF2
import re
from pathlib import Path
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import pdfrw

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text

def extract_dollar_amounts(text):
    # Only find amounts that start with $
    amounts = re.findall(r'\$\d+\.?\d*', text)
    return amounts

def extract_tax_from_total(amount, tax_rate=0.08875):
    # Given a total amount that includes tax, extract the base and tax portions
    base = round(amount / (1 + tax_rate), 2)
    tax = round(amount - base, 2)
    return base, tax

def create_overlay_pdf(amounts, width, height):
    # Create a new PDF in memory
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))
    
    # Set font and size
    c.setFont("Helvetica", 10)
    
    # Extract the monthly charge and calculate base/tax
    monthly_charge = float(amounts[0].replace('$', ''))
    base, tax = extract_tax_from_total(monthly_charge)
    
    # Draw white rectangles to cover original amounts
    c.setFillColorRGB(1, 1, 1)  # White
    
    # Cover the original amounts (adjust coordinates as needed)
    c.rect(400, 500, 100, 15, fill=1)  # Cover first amount
    c.rect(400, 450, 100, 15, fill=1)  # Cover second amount
    c.rect(400, 400, 100, 15, fill=1)  # Cover tax amount
    
    # Draw new amounts
    c.setFillColorRGB(0, 0, 0)  # Black
    c.drawString(400, 500, f"${base:.2f}")  # First base amount
    c.drawString(400, 450, f"${base:.2f}")  # Second base amount
    c.drawString(400, 400, f"${tax*2:.2f}")  # Total tax amount
    
    c.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    return packet

def fix_pdf_tax(input_pdf_path, output_pdf_path):
    # Extract text and amounts from input PDF
    text = extract_text_from_pdf(input_pdf_path)
    amounts = extract_dollar_amounts(text)
    
    if not amounts:
        raise ValueError("No dollar amounts found in PDF")
    
    # Get PDF dimensions from input
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    width = float(template_pdf.pages[0].MediaBox[2])
    height = float(template_pdf.pages[0].MediaBox[3])
    
    # Create overlay with new amounts
    overlay_buffer = create_overlay_pdf(amounts, width, height)
    overlay_pdf = PyPDF2.PdfReader(overlay_buffer)
    
    # Merge original PDF with overlay
    output = PyPDF2.PdfWriter()
    
    # Read the input PDF
    original = PyPDF2.PdfReader(input_pdf_path)
    
    # For each page
    for i in range(len(original.pages)):
        # Get the page
        page = original.pages[i]
        
        # Merge with overlay if it's the first page
        if i == 0:
            page.merge_page(overlay_pdf.pages[0])
        
        # Add to output
        output.add_page(page)
    
    # Write the output PDF
    with open(output_pdf_path, 'wb') as output_file:
        output.write(output_file)

def process_directory(input_dir='pdfs', output_dir='pdfs'):
    # Process all PDFs in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf') and not filename.endswith('-fixed.pdf'):
            input_path = os.path.join(input_dir, filename)
            # Add -fixed before the .pdf extension
            base_name = filename[:-4]  # remove .pdf
            output_path = os.path.join(output_dir, f'{base_name}-fixed.pdf')
            
            print(f"Processing {filename}...")
            try:
                fix_pdf_tax(input_path, output_path)
                print(f"Successfully created {output_path}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == '__main__':
    process_directory() 