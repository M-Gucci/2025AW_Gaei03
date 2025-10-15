import pymupdf
import os
from collections import namedtuple

# --- Data Structures ---
Point = namedtuple("Point", ["x", "y"])
Rect  = namedtuple("Rect", ["x0", "y0", "x1", "y1"])
namespace = {'Point': Point, 'Rect': Rect}

# --- Main Function ---
def process_pdf(pdf_filename):
    """
    Opens a PDF, removes very short line segments from all pages, 
    and saves the result to a new file with a '_treated' suffix.
    """
    # 1. Construct output filename and validate input
    base_name, ext = os.path.splitext(pdf_filename)
    if ext.lower() != '.pdf':
        print(f"Error: '{pdf_filename}' is not a .pdf file.")
        return
    output_filename = f"{base_name}_treated.pdf"

    # 2. Open the source PDF with error handling
    try:
        doc = pymupdf.open(pdf_filename)
    except Exception as e:
        print(f"Error opening or reading file '{pdf_filename}': {e}")
        return

    # Create a new PDF for the output
    out_pdf = pymupdf.open()

    print(f"Processing {len(doc)} pages from '{pdf_filename}'...")

    # 3. Process each page in the document
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Create a corresponding new page with the same dimensions
        out_page = out_pdf.new_page(width=page.rect.width, height=page.rect.height)
        
        paths = page.get_drawings()
        try:
            # Safely evaluate the drawing data
            data = eval(str(paths), namespace)
        except Exception:
            data = [] # If eval fails, assume no paths on this page

        shape = out_page.new_shape()

        for items in data:

            items_list = items['items']
            line_tuple = items_list[0]
            start_point = line_tuple[1]
            end_point = line_tuple[2]

            # Calculate segment length
            dis = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5

            # Ignore if the segment is too short
            if dis < 1e-5:
                continue
            else:
                # Get original color and width
                color = items.get("color")
                width = items.get("width", 1)
                
                # Draw the line into the shape and apply properties
                shape.draw_line(start_point, end_point)
                shape.finish(color=color, width=width)
        
        # Commit all drawings for this page
        shape.commit()

    # 4. Save the new PDF
    out_pdf.save(output_filename)

    # 5. Close documents
    out_pdf.close()
    doc.close()

    print(f"\nSuccessfully created '{output_filename}'.")

# --- Script Execution ---
if __name__ == "__main__":
    try:
        # Get PDF filename from user
        filename = input("Enter the name of the PDF file to process: ")
        process_pdf(filename)
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
