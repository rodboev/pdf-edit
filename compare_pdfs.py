import fitz
from PIL import Image
import io
import os

def extract_images_from_pdf(pdf_path):
    """Extract images from the PDF and save them."""
    doc = fitz.open(pdf_path)
    page = doc[0]  # First page
    
    # Get list of images on the page
    image_list = page.get_images()
    
    print(f"\nExtracting images from {os.path.basename(pdf_path)}:")
    for img_index, img in enumerate(image_list):
        # Get image data
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save with appropriate name based on index
        # First image is typically the logo
        if img_index == 0:
            output_path = "pdfs/logo.png"
        elif img_index == 1:
            output_path = "pdfs/customer_signature.png"
        elif img_index == 2:
            output_path = "pdfs/technician_signature.png"
        else:
            output_path = f"pdfs/image_{img_index}.png"
        
        # Save image
        image.save(output_path)
        print(f"Saved image to {output_path}")
        print(f"  Size: {image.size}")

def convert_pdf_to_image(pdf_path, output_path, zoom=2):
    """Convert a PDF to a high-resolution image and save it."""
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        page = doc[0]  # First page
        
        # Set high resolution
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error converting {pdf_path}: {str(e)}")
    return False

def analyze_pdf_text(pdf_path):
    """Extract and analyze text elements with their positions."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    print(f"\nAnalyzing text in {os.path.basename(pdf_path)}:")
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        font = span["font"]
                        size = span["size"]
                        bbox = span["bbox"]
                        print(f"Text: '{text}'")
                        print(f"  Position: ({bbox[0]:.1f}, {bbox[1]:.1f})")
                        print(f"  Font: {font}, Size: {size:.1f}")

def analyze_differences():
    """Convert both PDFs to images and analyze their differences."""
    # Define paths
    incorrect_path = "pdfs/incorrect.pdf"
    generated_path = "pdfs/generated.pdf"
    incorrect_img_path = "pdfs/incorrect.png"
    generated_img_path = "pdfs/generated.png"
    
    print("Converting PDFs to high-resolution images for analysis...")
    convert_pdf_to_image(incorrect_path, incorrect_img_path)
    convert_pdf_to_image(generated_path, generated_img_path)
    
    print("\nExtracting images from original PDF...")
    extract_images_from_pdf(incorrect_path)
    
    print("\nAnalyzing text layout and formatting...")
    print("\n=== Original PDF ===")
    analyze_pdf_text(incorrect_path)
    print("\n=== Generated PDF ===")
    analyze_pdf_text(generated_path)
    
    print("\nAnalysis complete. Image files generated for visual comparison:")
    print(f"Original PDF image: {incorrect_img_path}")
    print(f"Generated PDF image: {generated_img_path}")

if __name__ == "__main__":
    analyze_differences() 