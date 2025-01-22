import PyPDF2
import re

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

# Extract text from both PDFs
correct_text = extract_text_from_pdf('pdfs/correct.pdf')
incorrect_text = extract_text_from_pdf('pdfs/incorrect.pdf')

# Extract dollar amounts
correct_amounts = extract_dollar_amounts(correct_text)
incorrect_amounts = extract_dollar_amounts(incorrect_text)

print("=== Tax Analysis (NYC Rate: 8.875%) ===\n")

# Analyze correct PDF
print("Correct PDF Analysis:")
correct_total = float(correct_amounts[4].replace('$', ''))  # $435.50
correct_base = float(correct_amounts[6].replace('$', ''))   # $400.00
correct_tax = float(correct_amounts[5].replace('$', ''))    # $35.50
print(f"Base Amount: ${correct_base:.2f}")
print(f"Tax Amount: ${correct_tax:.2f}")
print(f"Total: ${correct_total:.2f}")
print(f"Actual Tax Rate: {(correct_tax/correct_base)*100:.3f}%")

# Analyze incorrect PDF (with baked-in tax)
print("\nIncorrect PDF Current State:")
monthly_charge = float(incorrect_amounts[0].replace('$', ''))  # $217.75
base, tax = extract_tax_from_total(monthly_charge)
print(f"Monthly Charge (with baked-in tax): ${monthly_charge:.2f}")
print(f"  Should be broken down as:")
print(f"  - Base Amount: ${base:.2f}")
print(f"  - Tax Amount: ${tax:.2f}")

print(f"\nTotal for two charges:")
print(f"Total Base: ${base*2:.2f}")
print(f"Total Tax: ${tax*2:.2f}")
print(f"Total Amount: ${monthly_charge*2:.2f}")

print("\nThe Issue:")
print(f"1. The ${tax*2:.2f} tax is currently hidden within the two ${monthly_charge:.2f} charges")
print(f"2. The tax line shows $0.00 when it should show ${tax*2:.2f}")
print(f"3. Need to extract the tax from the charges and display it separately") 