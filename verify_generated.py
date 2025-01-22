from PyPDF2 import PdfReader
import re

def extract_dollar_amounts(pdf_path):
    reader = PdfReader(pdf_path)
    amounts = []
    for page in reader.pages:
        text = page.extract_text()
        # Find all dollar amounts
        for match in re.finditer(r'\$\d+\.\d{2}', text):
            amounts.append(match.group())
    return amounts

def analyze_amounts(amounts):
    """Analyze the amounts in the correct order."""
    print("\nAmount Analysis:")
    
    # We expect amounts in this order:
    # 1. First line item ($200.00)
    # 2. Second line item ($200.00)
    # 3. Subtotal ($400.00)
    # 4. Tax ($35.50)
    # 5. Amount paid ($0.00)
    # 6. Amount due ($435.50)
    
    if len(amounts) >= 6:
        line_item1 = float(amounts[0].replace('$', ''))
        line_item2 = float(amounts[1].replace('$', ''))
        subtotal = float(amounts[2].replace('$', ''))
        tax = float(amounts[3].replace('$', ''))
        amount_paid = float(amounts[4].replace('$', ''))
        amount_due = float(amounts[5].replace('$', ''))
        
        print(f"Line Item 1: ${line_item1:.2f}")
        print(f"Line Item 2: ${line_item2:.2f}")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Tax Amount: ${tax:.2f}")
        print(f"Amount Paid: ${amount_paid:.2f}")
        print(f"Amount Due: ${amount_due:.2f}")
        
        # Verify calculations
        print("\nVerifications:")
        print(f"Subtotal Check: ${line_item1 + line_item2:.2f} (should equal ${subtotal:.2f})")
        print(f"Tax Rate: {(tax/subtotal)*100:.3f}% (should be 8.875%)")
        print(f"Total Check: ${subtotal + tax:.2f} (should equal ${amount_due:.2f})")

print("=== Generated PDF Analysis ===")
amounts = extract_dollar_amounts("pdfs/generated.pdf")
print("Dollar amounts found:", amounts)
analyze_amounts(amounts) 