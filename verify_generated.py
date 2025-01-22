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

print("=== Generated PDF Analysis ===")
amounts = extract_dollar_amounts("pdfs/generated.pdf")
print("Dollar amounts found:", amounts)

# Verify calculations
if len(amounts) >= 3:
    base = float(amounts[0].replace('$', ''))
    tax = float(amounts[1].replace('$', ''))
    total = float(amounts[2].replace('$', ''))
    
    print("\nVerification:")
    print(f"Base Amount: ${base:.2f}")
    print(f"Tax Amount: ${tax:.2f}")
    print(f"Total Amount: ${total:.2f}")
    print(f"Tax Rate: {(tax/base)*100:.3f}%")
    print(f"Sum Check: ${base + tax:.2f} (should equal total)") 