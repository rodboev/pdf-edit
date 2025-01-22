import PyPDF2
import re
from pathlib import Path
import os

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

def fix_pdf_tax(input_pdf_path, output_pdf_path):
    # Read the PDF
    reader = PyPDF2.PdfReader(input_pdf_path)
    writer = PyPDF2.PdfWriter()
    
    # Process each page
    for page in reader.pages:
        # Get the text content
        text = page.extract_text()
        
        # Find all dollar amounts
        amounts = extract_dollar_amounts(text)
        if not amounts:
            continue
            
        # Get the monthly charge (which includes tax)
        monthly_charge = float(amounts[0].replace('$', ''))
        base, tax = extract_tax_from_total(monthly_charge)
        
        # Create a new content stream
        content = page.get_contents()
        if content:
            # Replace the tax amount ($0.00) with the correct tax ($35.50)
            content_str = content.get_data().decode('utf-8')
            content_str = content_str.replace('$0.00', f'${tax*2:.2f}')
            
            # Replace the charges that include tax with base amounts
            content_str = content_str.replace(f'${monthly_charge:.2f}', f'${base:.2f}')
            
            # Update the page content
            page.update({
                PyPDF2.generic.NameObject('/Contents'): PyPDF2.generic.StreamObject(content_str.encode('utf-8'))
            })
        
        writer.add_page(page)
    
    # Save the modified PDF
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)

def process_directory(input_dir='pdfs', output_dir='pdfs'):
    # Process all PDFs in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
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