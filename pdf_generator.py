from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from decimal import Decimal
import datetime

def create_invoice_pdf(output_path: str, base_amount: float = 200.00, tax_rate: float = 0.08875):
    """Create a new invoice PDF with the specified base amount and tax rate."""
    # Calculate values
    tax_amount = round(base_amount * tax_rate, 2)
    total_amount = base_amount + tax_amount
    
    # Create the PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Set default font
    c.setFont("Helvetica-Bold", 12)
    
    # Header
    c.drawString(50, 750, "Liberty Pest Control")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "8220 17th Avenue")
    c.drawString(50, 720, "Brooklyn, NY 11214")
    c.drawString(50, 705, "800-595-4692")
    
    # Customer Info
    c.drawString(50, 675, "Prime Produce Community Center")
    c.drawString(50, 660, "424 W 54th St")
    c.drawString(50, 645, "New York, NY 10019-4406")
    
    # Invoice Details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, 750, "Invoice #: 1148151")
    c.setFont("Helvetica", 10)
    c.drawString(400, 735, f"Date: {datetime.datetime.now().strftime('%m/%d/%Y')}")
    
    # Column Headers
    y = 600
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Service Description")
    c.drawString(300, y, "Quantity")
    c.drawString(400, y, "Price")
    
    # Service Line Items
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "MONTHLY COST")
    c.drawString(300, y, "1.00")
    c.drawString(400, y, f"${base_amount:.2f}")
    
    # Tax and Total
    y -= 25
    c.drawString(300, y, "Tax:")
    c.drawString(400, y, f"${tax_amount:.2f}")
    
    y -= 25
    c.setFont("Helvetica-Bold", 10)
    c.drawString(300, y, "Total:")
    c.drawString(400, y, f"${total_amount:.2f}")
    
    # Save the PDF
    c.save()
    print(f"\nCreated new invoice PDF at {output_path}")
    print(f"Base Amount: ${base_amount:.2f}")
    print(f"Tax Amount: ${tax_amount:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")

if __name__ == "__main__":
    output_pdf = "pdfs/generated.pdf"
    create_invoice_pdf(output_pdf) 