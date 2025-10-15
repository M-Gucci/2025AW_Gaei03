import pymupdf
import os
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
Rect  = namedtuple("Rect", ["x0", "y0", "x1", "y1"])

namespace = {'Point': Point, 'Rect': Rect}

# Open the source PDF
doc = pymupdf.open("pawn2.pdf")
page = doc[0]
paths = page.get_drawings()

# Evaluate the path data safely
data = eval(str(paths), namespace)

# Create a new PDF for the output
out_pdf = pymupdf.open()
out_page = out_pdf.new_page(width=page.rect.width, height=page.rect.height)

# Create a shape object to draw on. This is more efficient.
shape = out_page.new_shape()

# Iterate through the drawing data
for items in data:
    # We are only interested in line drawings
    if not items.get('items') or items['items'][0][0] != 'l':
        continue

    items_list = items['items']
    line_tuple = items_list[0]
    start_point = line_tuple[1]
    end_point = line_tuple[2]

    # Calculate the length of the segment
    dis = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5

    # If the segment is too short, ignore it
    if dis < 1e-5:
        continue
    else:
        # Get the original color and width
        color = items.get("color")
        width = items.get("width", 1) # Use a default width of 1 if not present
        
        # Draw the line into the shape
        shape.draw_line(start_point, end_point)
        
        # Apply the properties to the line just drawn and finish the item
        shape.finish(color=color, width=width)

# Commit all drawings in the shape to the page at once
shape.commit()

# Save the new PDF with filtered lines
out_pdf.save("pawn_filtered.pdf")

# Close the documents
out_pdf.close()
doc.close()

print("Filtered PDF with original colors created as pawn_filtered.pdf")
