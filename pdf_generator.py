from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from decimal import Decimal
import datetime
import os
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader
import re

def extract_invoice_data(source_pdf_path):
    """Extract all required data from the source PDF."""
    reader = PdfReader(source_pdf_path)
    text = reader.pages[0].extract_text()
    
    print("\nRaw text from PDF:")
    print(text)
    
    # Helper function to find values
    def find_value(pattern, text, group=1):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        return match.group(group).strip() if match else None
    
    # Helper function to find matches (returns match object)
    def find_match(pattern, text):
        return re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    # Extract all required values
    data = {
        'invoice_number': find_value(r'Invoice\s*#\s*(\d+)', text),
        'day': find_value(r'Time:[^F]*Friday', text, group=0).replace('Time:', '').strip(),  # Extract "Friday"
        'date': find_value(r'(\d{2}/\d{2}/\d{4})', text),  # Extract date in correct format
        'time': find_value(r'(\d{2}:\d{2}\s*[APM]+)', text),  # Extract time in correct format
        'bill_to': None,  # Will extract below
        'location': find_value(r'Location:\s*(\d+)', text),  # Will clean up later
        'customer_name': None,
        'customer_contact': None,
        'customer_address': None,
        'customer_city_state': None,
        'service_items': [],
        'amounts': {
            'line_items': [],
            'subtotal': None,
            'tax': None,
            'total': None,
            'paid': None,
            'due': None
        },
        'terms': find_value(r'Terms:\s*([^\n]+)', text),
        'company_address': [
            "Liberty Pest Control",
            "8220 17th Avenue",
            "Brooklyn, NY 11214",
            "800-595-4692"
        ]
    }
    
    # Extract bill-to number from the text
    # Look for it in the bottom section where it's cleaner
    bill_to_match = find_match(r'(\d{6})\s+01/10/2025', text)
    if bill_to_match:
        data['bill_to'] = bill_to_match.group(1)
    
    # Clean up location number (it's concatenated with bill-to)
    if data['location'] and len(data['location']) > 6:
        data['location'] = data['location'][:6]  # Take first 6 digits
    
    # Extract customer address block (first occurrence)
    address_block = find_value(r'Prime\s+Produce[^\n]*(?:\n[^\n]+){3}', text, group=0)
    if address_block:
        address_lines = [line.strip() for line in address_block.strip().split('\n')]
        if len(address_lines) >= 4:
            data['customer_name'] = address_lines[0]
            data['customer_contact'] = address_lines[1]
            data['customer_address'] = address_lines[2]
            data['customer_city_state'] = address_lines[3].split('Prime')[0].strip()  # Remove duplicate text
    
    # Extract service items
    service_items = []
    monthly_cost_match = find_match(r'MONTHLY\s+COST\s+(\d+\.\d{2})\s+\$(\d+\.\d{2})', text)
    if monthly_cost_match:
        service_items.append({
            'description': 'MONTHLY COST',
            'quantity': monthly_cost_match.group(1),
            'price': float(monthly_cost_match.group(2))
        })
    
    # Fix the special service regex pattern to handle newlines better
    special_service_match = find_match(r'NEW\s+ACCOUNT\s+EQUIPMENT\s+OR\s+SPECIAL\s*\n*\s*SERVICE\s*(\d+\.\d{2})\s+\$(\d+\.\d{2})', text)
    if special_service_match:
        service_items.append({
            'description': 'NEW ACCOUNT EQUIPMENT OR SPECIAL SERVICE',  # No newline in description
            'quantity': special_service_match.group(1),
            'price': float(special_service_match.group(2))
        })
    data['service_items'] = service_items
    
    # Extract amounts using more specific patterns
    amounts_text = text
    
    # Initialize amounts with defaults
    data['amounts'] = {
        'subtotal': 0.0,
        'tax': 0.0,
        'total': 0.0,
        'paid': 0.0,
        'due': 0.0
    }
    
    # Handle amounts in reverse order (due to text layout)
    subtotal_match = find_match(r'\$(\d+\.\d{2})\s+SUBTOTAL', amounts_text)
    if subtotal_match:
        data['amounts']['subtotal'] = float(subtotal_match.group(1))
    
    tax_match = find_match(r'\$(\d+\.\d{2})\s+TAX', amounts_text)
    if tax_match:
        data['amounts']['tax'] = float(tax_match.group(1))
    
    total_match = find_match(r'TOTAL\s*\$(\d+\.\d{2})', amounts_text)
    if total_match:
        data['amounts']['total'] = float(total_match.group(1))
    
    # Handle the parentheses in AMT PAID
    paid_match = find_match(r'\(\$(\d+\.\d{2})\)', amounts_text)
    if paid_match:
        data['amounts']['paid'] = float(paid_match.group(1))
    
    due_match = find_match(r'\$(\d+\.\d{2})\s*AMOUNT\s+DUE', amounts_text)
    if due_match:
        data['amounts']['due'] = float(due_match.group(1))
    
    # If amounts weren't found, calculate them
    if data['amounts']['subtotal'] == 0 and len(data['service_items']) > 0:
        data['amounts']['subtotal'] = sum(item['price'] for item in data['service_items'])
    if data['amounts']['tax'] == 0 and data['amounts']['subtotal'] > 0:
        data['amounts']['tax'] = round(data['amounts']['subtotal'] * 0.08875, 2)
    if data['amounts']['total'] == 0:
        data['amounts']['total'] = data['amounts']['subtotal'] + data['amounts']['tax']
    if data['amounts']['due'] == 0:
        data['amounts']['due'] = data['amounts']['total'] - data['amounts']['paid']
    
    # Print extracted data for debugging
    print("\nExtracted Data:")
    print(f"Invoice Number: {data['invoice_number']}")
    print(f"Day: {data['day']}")
    print(f"Date: {data['date']}")
    print(f"Time: {data['time']}")
    print(f"Bill-To: {data['bill_to']}")
    print(f"Location: {data['location']}")
    print(f"Terms: {data['terms']}")
    
    print("\nCustomer Info:")
    print(f"Name: {data['customer_name']}")
    print(f"Contact: {data['customer_contact']}")
    print(f"Address: {data['customer_address']}")
    print(f"City/State: {data['customer_city_state']}")
    
    print("\nService Items:")
    for item in data['service_items']:
        print(f"Description: {item['description']}")
        print(f"Quantity: {item['quantity']}")
        print(f"Price: ${item['price']:.2f}")
        print()
    
    print("Amounts:")
    print(f"Subtotal: ${data['amounts']['subtotal']:.2f}")
    print(f"Tax: ${data['amounts']['tax']:.2f}")
    print(f"Total: ${data['amounts']['total']:.2f}")
    print(f"Amount Paid: ${data['amounts']['paid']:.2f}")
    print(f"Amount Due: ${data['amounts']['due']:.2f}")
    
    return data

def create_invoice_pdf(output_path: str, data: dict):
    """Create a new invoice PDF using the provided data."""
    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Helper function for drawing lines
    def draw_line(x1, y1, x2, y2, width=1):
        c.setLineWidth(width)
        c.line(x1, height - y1, x2, height - y2)
    
    # Helper function for drawing text (with y-coordinate conversion)
    def draw_text(x, y, text, size=10, bold=False, right_align=False):
        if text is None:  # Handle None values
            text = ""
        text = str(text)  # Convert to string
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font_name, size)
        if right_align:
            text_width = c.stringWidth(text, font_name, size)
            x = x - text_width
        c.drawString(x, height - y, text)
    
    # Helper function for word wrapping text
    def wrap_text(text, width_inches, font_name="Helvetica", font_size=10):
        c.setFont(font_name, font_size)
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        space_width = c.stringWidth(" ", font_name, font_size)
        width_points = width_inches * 72  # Convert inches to points
        
        for word in words:
            word_width = c.stringWidth(word, font_name, font_size)
            if current_width + word_width <= width_points:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                if current_line:  # Only add non-empty lines
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width + space_width
        
        if current_line:  # Add the last line if it exists
            lines.append(" ".join(current_line))
        
        return lines
    
    # Helper function for drawing rectangles
    def draw_rect(x, y, w, h, stroke=1, fill=0):
        c.rect(x, height - y - h, w, h, stroke=stroke, fill=fill)
    
    # Define alignment points
    price_right_edge = 473 + c.stringWidth("Price", "Helvetica-Bold", 10)
    quantity_right_edge = 290 + c.stringWidth("Quantity", "Helvetica-Bold", 10)
    
    # Header section - company info
    draw_text(50, 65, data['company_address'][0], size=12, bold=True)
    for i, line in enumerate(data['company_address'][1:], 1):
        draw_text(50, 65 + (15 * i), line)
    
    # Invoice details (top right)
    draw_text(445, 40, f"Invoice # {data['invoice_number']}", size=12, bold=True)
    
    # Evenly spaced invoice details
    detail_y = 65
    spacing = 15
    
    draw_text(450, detail_y, "Invoice", bold=True)
    draw_text(487, detail_y, data['date'])
    
    detail_y += spacing
    draw_text(460, detail_y, "Date:", bold=True)
    draw_text(487, detail_y, data['day'])
    
    detail_y += spacing
    draw_text(460, detail_y, "Time:", bold=True)
    draw_text(487, detail_y, data['time'])
    
    detail_y += spacing
    draw_text(454, detail_y, "Bill-To:", size=9, bold=True)
    draw_text(487, detail_y, data['bill_to'], size=9)
    
    detail_y += spacing
    draw_text(445, detail_y, "Location:", size=9, bold=True)
    draw_text(487, detail_y, data['location'], size=9)
    
    # Customer Info (both columns)
    for x in [55, 280]:
        draw_text(x, 160, data['customer_name'], size=9)
        draw_text(x, 170, data['customer_contact'], size=9)
        draw_text(x, 180, data['customer_address'], size=9)
        draw_text(x, 190, data['customer_city_state'], size=9)
    
    # Service table header
    y = 225
    draw_rect(15, y-5, 580, 25)
    draw_text(18, y+10, "Service Description", size=10, bold=True)
    draw_text(290, y+10, "Quantity", size=10, bold=True)
    draw_text(473, y+10, "Price", size=10, bold=True)
    
    # Service line items with word wrapping
    y = 260
    for item in data['service_items']:
        # Word wrap the description to 2.875 inches
        wrapped_lines = wrap_text(item['description'], 2.875)
        
        # Draw each line of the wrapped description
        for i, line in enumerate(wrapped_lines):
            draw_text(18, y + (i * 12), line)
        
        # Draw quantity and price on the first line
        draw_text(quantity_right_edge, y, str(item['quantity']), right_align=True)
        draw_text(price_right_edge, y, f"${item['price']:.2f}", right_align=True)
        
        # Move down by the height of the wrapped text plus spacing
        y += max(5, len(wrapped_lines) * 12 + 5)
    
    # Amounts section
    y = 315
    draw_line(365, y-15, 500, y-15)
    draw_text(366, y, "SUBTOTAL", bold=True)
    draw_text(price_right_edge, y, f"${data['amounts']['subtotal']:.2f}", right_align=True)
    
    y += 15
    draw_text(366, y, "TAX", bold=True)
    draw_text(price_right_edge, y, f"${data['amounts']['tax']:.2f}", right_align=True)
    
    y += 15
    draw_text(366, y, "AMT PAID", bold=True)
    draw_text(price_right_edge, y, f"(${data['amounts']['paid']:.2f})", right_align=True)
    
    y += 15
    draw_text(366, y, "TOTAL", bold=True)
    draw_text(price_right_edge, y, f"${data['amounts']['total']:.2f}", right_align=True)
    draw_text(366, y+15, "AMOUNT DUE", bold=True)
    draw_text(price_right_edge, y+15, f"${data['amounts']['due']:.2f}", right_align=True)
    
    # Bottom section
    y = 560
    draw_text(19, y, "Bill-To:", size=9)
    draw_text(273, y+15, "PO Number:", size=9)
    draw_text(333, y, data['bill_to'], size=9)
    draw_text(435, y+15, "Invoice #:", size=9)
    draw_text(478, y+15, data['invoice_number'], size=9)
    draw_text(478, y, data['date'], size=9)
    
    y += 35
    draw_text(295, y, "Terms:", size=9)
    draw_text(323, y, data['terms'], size=9)
    
    # Bottom addresses
    y = 580
    for text in [data['customer_name'], data['customer_contact'], 
                data['customer_address'], data['customer_city_state']]:
        draw_text(64, y, text, size=9)
        y += 10
    
    y = 670
    for text in data['company_address']:
        draw_text(64, y, text, size=9)
        y += 10
    
    # Save the PDF
    c.save()
    print(f"\nCreated new invoice PDF at {output_path}")

if __name__ == "__main__":
    source_pdf = "pdfs/correct.pdf"
    output_pdf = "pdfs/generated.pdf"
    
    # Extract data from source PDF
    invoice_data = extract_invoice_data(source_pdf)
    
    # Generate new PDF with extracted data
    create_invoice_pdf(output_pdf, invoice_data) 