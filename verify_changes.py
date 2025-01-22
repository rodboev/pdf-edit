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

print("=== Original PDF ===")
original_amounts = extract_dollar_amounts("pdfs/incorrect.pdf")
print("Dollar amounts found:", original_amounts)

print("\n=== Modified PDF ===")
modified_amounts = extract_dollar_amounts("pdfs/corrected.pdf")
print("Dollar amounts found:", modified_amounts) 