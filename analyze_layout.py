from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTImage, LTFigure, LTLine, LTRect
import re

def analyze_pdf_layout(pdf_path):
    """Analyze the complete layout of the PDF including text, images, lines, and boxes."""
    elements = []
    
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:  # Only include non-empty text
                    elements.append({
                        'type': 'text',
                        'content': text,
                        'bbox': element.bbox,
                        'x0': element.bbox[0],
                        'y0': element.bbox[1],
                        'x1': element.bbox[2],
                        'y1': element.bbox[3]
                    })
            elif isinstance(element, (LTImage, LTFigure)):
                elements.append({
                    'type': 'image',
                    'bbox': element.bbox,
                    'x0': element.bbox[0],
                    'y0': element.bbox[1],
                    'x1': element.bbox[2],
                    'y1': element.bbox[3]
                })
            elif isinstance(element, (LTLine, LTRect)):
                elements.append({
                    'type': 'shape',
                    'bbox': element.bbox,
                    'x0': element.bbox[0],
                    'y0': element.bbox[1],
                    'x1': element.bbox[2],
                    'y1': element.bbox[3]
                })
    
    return elements

def print_layout_analysis(elements):
    """Print the layout analysis in a structured way."""
    print("=== PDF Layout Analysis ===\n")
    
    # Group elements by vertical position (roughly)
    vertical_groups = {}
    for elem in elements:
        y_pos = round(elem['y0'] / 10) * 10  # Round to nearest 10 for grouping
        if y_pos not in vertical_groups:
            vertical_groups[y_pos] = []
        vertical_groups[y_pos].append(elem)
    
    # Print elements by vertical position (top to bottom)
    for y_pos in sorted(vertical_groups.keys(), reverse=True):
        print(f"\nAt y ≈ {y_pos}:")
        for elem in vertical_groups[y_pos]:
            if elem['type'] == 'text':
                print(f"  Text: '{elem['content']}' at ({elem['x0']:.1f}, {elem['y0']:.1f})")
            elif elem['type'] == 'image':
                print(f"  Image at ({elem['x0']:.1f}, {elem['y0']:.1f})")
            elif elem['type'] == 'shape':
                print(f"  Shape at ({elem['x0']:.1f}, {elem['y0']:.1f}) to ({elem['x1']:.1f}, {elem['y1']:.1f})")

if __name__ == "__main__":
    pdf_path = "pdfs/incorrect.pdf"
    elements = analyze_pdf_layout(pdf_path)
    print_layout_analysis(elements) 