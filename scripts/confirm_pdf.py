import pymupdf
import sys
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
Rect  = namedtuple("Rect", ["x0", "y0", "x1", "y1"])

namespace = {'Point': Point, 'Rect': Rect}

filename = input("Enter the name of the PDF file to process: ")

# Open the source PDF
try:
        doc = pymupdf.open(filename)
except Exception as e:
    print(f"Error opening or reading file '{filename}': {e}")
    sys.exit(1)

page = doc[0]
paths = page.get_drawings()

# Evaluate the path data safely
data = eval(str(paths), namespace)

# Iterate through the drawing data
for items in data:

    items_list = items['items']
    line_tuple = items_list[0]
    start_point = line_tuple[1]
    end_point = line_tuple[2]

    # Calculate the length of the segment
    dis = ((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)**0.5

    # If the segment is too short, ignore it
    if dis < 1e-5:
        print("existing point...")

