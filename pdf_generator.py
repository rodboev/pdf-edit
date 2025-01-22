from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from decimal import Decimal
import datetime
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

def create_invoice_pdf(output_path: str, base_amount: float = 200.00, tax_rate: float = 0.08875):
    """Create a new invoice PDF with the specified base amount and tax rate."""
    # Calculate values
    subtotal = base_amount * 2  # Two line items
    tax_amount = round(subtotal * tax_rate, 2)
    total_amount = subtotal + tax_amount
    amount_paid = 0.00
    amount_due = total_amount - amount_paid
    
    # Calculate individual line item amounts
    line_item_base = base_amount
    line_item_tax = round(line_item_base * tax_rate, 2)
    line_item_total = line_item_base + line_item_tax
    
    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Helper function for drawing lines
    def draw_line(x1, y1, x2, y2, width=1):
        c.setLineWidth(width)
        c.line(x1, height - y1, x2, height - y2)
    
    # Helper function for drawing text (with y-coordinate conversion)
    def draw_text(x, y, text, size=10, bold=False, right_align=False):
        font_name = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font_name, size)
        if right_align:
            text_width = c.stringWidth(text, font_name, size)
            x = x - text_width
        c.drawString(x, height - y, text)
    
    # Helper function for drawing rectangles
    def draw_rect(x, y, w, h, stroke=1, fill=0):
        c.rect(x, height - y - h, w, h, stroke=stroke, fill=fill)
    
    # Helper function for drawing images
    def draw_image(image_path, x, y, width, height):
        img = Image.open(image_path)
        img_width, img_height = img.size
        aspect = img_height / float(img_width)
        
        # Calculate dimensions to maintain aspect ratio
        if width is None:
            width = height / aspect
        if height is None:
            height = width * aspect
            
        c.drawImage(image_path, x, height - y - height, width=width, height=height)
    
    # Define alignment points
    price_right_edge = 473 + c.stringWidth("Price", "Helvetica-Bold", 10)  # Right edge of "Price"
    quantity_right_edge = 290 + c.stringWidth("Quantity", "Helvetica-Bold", 10)  # Right edge of "Quantity"
    
    # Header section
    draw_text(50, 40, "Liberty Pest Control", size=12, bold=True)  # Moved down to align with Invoice
    draw_text(50, 55, "8220 17th Avenue")
    draw_text(50, 70, "Brooklyn, NY 11214")
    draw_text(50, 85, "800-595-4692")
    
    # Logo
    try:
        draw_image("pdfs/logo.png", 50, 100, width=150, height=None)
    except Exception as e:
        print(f"Warning: Could not load logo image: {e}")
    
    # Invoice details (top right)
    draw_text(445, 40, "Invoice # 1148151", size=12, bold=True)
    
    # Evenly spaced invoice details
    detail_y = 65  # Starting Y position
    spacing = 20   # Space between items
    
    draw_text(452, detail_y, "Invoice", bold=True)
    draw_text(487, detail_y, "01/10/2025")
    
    detail_y += spacing
    draw_text(460, detail_y, "Date:", bold=True)
    draw_text(487, detail_y-7, "Friday")  # Aligned with "Date:"
    
    detail_y += spacing
    draw_text(460, detail_y, "Time:", bold=True)
    draw_text(487, detail_y, "10:44 AM")
    
    # Location and Bill-To
    draw_text(443, 115, "Location:", size=9, bold=True)
    draw_text(487, 115, "142877", size=9)
    draw_text(452, 135, "Bill-To:", size=9, bold=True)
    draw_text(487, 135, "142877", size=9)
    
    # Customer Info (both columns)
    for x in [55, 280]:
        draw_text(x, 160, "Prime Produce Community Center", size=9)
        draw_text(x, 170, "Renee Keitt", size=9)
        draw_text(x, 180, "424 W 54th St", size=9)
        draw_text(x, 190, "New York, NY 10019-4406", size=9)
    
    # Service table header with border
    y = 225
    draw_rect(15, y-5, 580, 25)  # Header box
    draw_text(18, y+10, "Service Description", size=10, bold=True)
    draw_text(290, y+10, "Quantity", size=10, bold=True)
    draw_text(473, y+10, "Price", size=10, bold=True)
    
    # Service line items
    y = 260
    draw_text(18, y, "MONTHLY COST")
    draw_text(quantity_right_edge, y, "1.00", right_align=True)
    draw_text(price_right_edge, y, f"${line_item_base:.2f}", right_align=True)
    
    y = 275
    draw_text(18, y, "NEW ACCOUNT EQUIPMENT OR SPECIAL")
    draw_text(18, y+12, "SERVICE")
    draw_text(quantity_right_edge, y, "1.00", right_align=True)
    draw_text(price_right_edge, y, f"${line_item_base:.2f}", right_align=True)
    
    # Subtotal section
    y = 315
    draw_line(365, y-8, 500, y-8)  # Line above subtotal, moved up
    draw_text(366, y, "SUBTOTAL", bold=True)
    draw_text(price_right_edge, y, f"${subtotal:.2f}", right_align=True)
    
    # Tax
    y += 15
    draw_text(366, y, "TAX", bold=True)
    draw_text(price_right_edge, y, f"${tax_amount:.2f}", right_align=True)
    
    # Amount paid
    y += 15
    draw_text(366, y, "AMT PAID", bold=True)
    draw_text(price_right_edge, y, f"(${amount_paid:.2f})", right_align=True)
    
    # Total/Amount due
    y += 15
    draw_text(366, y, "TOTAL", bold=True)
    draw_text(price_right_edge, y, f"${total_amount:.2f}", right_align=True)
    draw_text(366, y+15, "AMOUNT DUE", bold=True)
    draw_text(price_right_edge, y+15, f"${amount_due:.2f}", right_align=True)
    
    # Signature boxes and signatures
    y = 480
    signatures_present = True
    try:
        draw_image("pdfs/customer_signature.png", 34, y-25, width=150, height=50)
        draw_image("pdfs/technician_signature.png", 201, y-25, width=150, height=50)
    except Exception as e:
        print(f"Warning: Could not load signatures: {e}")
        signatures_present = False
    
    if signatures_present:
        draw_text(54, y, "CUSTOMER SIGNATURE", size=8)
        draw_text(221, y, "TECHNICIAN SIGNATURE", size=8)
    
    # Bottom section
    y = 560
    draw_text(19, y, "Bill-To:", size=9)
    draw_text(273, y+15, "PO Number:", size=9)
    draw_text(333, y, "142877", size=9)
    draw_text(435, y+15, "Invoice #:", size=9)
    draw_text(478, y+15, "1148151", size=9)
    draw_text(478, y, "01/10/2025", size=9)
    
    y += 35
    draw_text(295, y, "Terms:", size=9)
    draw_text(323, y, "NET 30", size=9)
    
    # Bottom addresses
    y = 580
    for text in ["Prime Produce Community Center", "Renee Keitt", "424 W 54th St", "New York, NY 10019-4406"]:
        draw_text(64, y, text, size=9)
        y += 10
    
    y = 670
    for text in ["Liberty Pest Control", "8220 17th Avenue", "Brooklyn, NY 11214", "800-595-4692"]:
        draw_text(64, y, text, size=9)
        y += 10
    
    # Try to add barcode from correct.pdf
    try:
        draw_image("pdfs/barcode.png", 20, 700, width=100, height=30)
    except Exception as e:
        print(f"Warning: Could not load barcode: {e}")
    
    # Decorative lines in bottom right
    y_start = 620
    for i in range(15):
        y = y_start + (i * 5)
        draw_line(575, y, 603, y, 0.5)
    
    # Save the PDF
    c.save()
    print(f"\nCreated new invoice PDF at {output_path}")
    print(f"Base Amount (per item): ${base_amount:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Tax Amount: ${tax_amount:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")
    print(f"Amount Paid: ${amount_paid:.2f}")
    print(f"Amount Due: ${amount_due:.2f}")

if __name__ == "__main__":
    output_pdf = "pdfs/generated.pdf"
    create_invoice_pdf(output_pdf) 