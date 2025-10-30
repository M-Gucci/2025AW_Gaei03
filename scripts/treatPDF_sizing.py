import matplotlib.pyplot as plt
import sys
from matplotlib import patches

def parse_obj(filename):
    """
    Parses an OBJ file to extract vertices, lines (edges), and faces.
    Also identifies unreferenced vertices.
    """
    vertices_raw = [] # Stores all v lines as [x,y,z]
    lines = []
    faces = []
    
    # For unreferenced vertex detection
    total_vertices_count = 0
    referenced_indices_set = set()

    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'v':
                    vertices_raw.append([float(p) for p in parts[1:4]])
                    total_vertices_count += 1
                elif parts[0] == 'l':
                    line_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    lines.append(line_indices)
                    for idx in line_indices:
                        referenced_indices_set.add(idx + 1) # Store 1-based
                elif parts[0] == 'f':
                    face_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    faces.append(face_indices)
                    for idx in face_indices:
                        referenced_indices_set.add(idx + 1) # Store 1-based
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while parsing the file: {e}")
        sys.exit(1)

    # Calculate unreferenced vertices
    unreferenced_vertices_coords = []
    if total_vertices_count > 0:
        defined_indices_set = set(range(1, total_vertices_count + 1))
        unreferenced_1based_indices = defined_indices_set - referenced_indices_set
        
        for idx_1based in sorted(list(unreferenced_1based_indices)):
            # Get 0-based index for vertices_raw
            idx_0based = idx_1based - 1
            if 0 <= idx_0based < len(vertices_raw):
                unreferenced_vertices_coords.append((vertices_raw[idx_0based][0], vertices_raw[idx_0based][1])) # Store (x,y)

    # Calculate model bounding box (NEW CODE BLOCK)
    min_x_model, max_x_model = float('inf'), float('-inf')
    min_y_model, max_y_model = float('inf'), float('-inf')

    if vertices_raw:
        for v_coords in vertices_raw:
            x, y = v_coords[0], v_coords[1]
            min_x_model = min(min_x_model, x)
            max_x_model = max(max_x_model, x)
            min_y_model = min(min_y_model, y)
            max_y_model = max(max_y_model, y)
    else:
        # Fallback if no vertices, though 'if not vertices' should catch this earlier
        min_x_model, max_x_model = -1, 1
        min_y_model, max_y_model = -1, 1

    return vertices_raw, lines, faces, unreferenced_vertices_coords, min_x_model, max_x_model, min_y_model, max_y_model

def plot_obj(vertices, lines, faces, unreferenced_vertices_coords, min_x_model, max_x_model, min_y_model, max_y_model):
    """
    Plots the OBJ data in 2D by ignoring the Z-coordinate.
    - Lines ('l') are drawn in blue.
    - Face boundaries ('f') are drawn in red.
    - Individual vertices are plotted as black dots.
    - Circles are drawn around unreferenced vertices.
    """
    if not vertices:
        print("No vertices to plot.")
        return

    # Prompt user for scale
    print("\nEnter the desired scale for the output (e.g., 1.0 unit = 1.0 cm).")
    while True:
        try:
            user_scale_cm_per_unit_str = input("Enter scale (cm per unit, e.g., 1.0): ")
            user_scale_cm_per_unit = float(user_scale_cm_per_unit_str)
            if user_scale_cm_per_unit <= 0:
                print("Scale must be a positive number.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Fixed figsize to A3 portrait size
    paper_width_cm = 11.69 * 2.54 # A3 width in cm
    paper_height_cm = 16.54 * 2.54 # A3 height in cm
    
    fig = plt.figure(figsize=(paper_width_cm / 2.54, paper_height_cm / 2.54)) # Fixed A3 figsize
    ax = fig.add_subplot(111)

    # Calculate model dimensions in data units
    data_width = max_x_model - min_x_model
    data_height = max_y_model - min_y_model

    # Add a small padding in data units
    padding_factor = 0
    padding_x_data = data_width * padding_factor
    padding_y_data = data_height * padding_factor

    # Calculate the final xlim/ylim to encompass the model + padding
    final_min_x_data = min_x_model - padding_x_data
    final_max_x_data = max_x_model + padding_x_data
    final_min_y_data = min_y_model - padding_y_data
    final_max_y_data = max_y_model + padding_y_data

    # Calculate the aspect ratio of the paper (A3)
    paper_aspect_ratio = paper_height_cm / paper_width_cm

    # Calculate the aspect ratio of the model with padding
    padded_data_width = final_max_x_data - final_min_x_data
    padded_data_height = final_max_y_data - final_min_y_data
    data_aspect_ratio = padded_data_height / padded_data_width

    # Determine the effective scale
    effective_scale_cm_per_unit = user_scale_cm_per_unit
    
    # Calculate required physical dimensions on paper in cm at user's scale
    required_physical_width_cm = padded_data_width * user_scale_cm_per_unit
    required_physical_height_cm = padded_data_height * user_scale_cm_per_unit

    # Check if the model at the user's scale fits within A3. If it doesn't, adjust the scale.
    if required_physical_width_cm > paper_width_cm or required_physical_height_cm > paper_height_cm:
        print(f"\nWarning: The model at scale {user_scale_cm_per_unit} cm/unit ({required_physical_width_cm:.2f}cm x {required_physical_height_cm:.2f}cm) exceeds A3 paper size ({paper_width_cm:.2f}cm x {paper_height_cm:.2f}cm).")
        
        # Calculate scale factors to fit within A3
        scale_factor_width = paper_width_cm / required_physical_width_cm
        scale_factor_height = paper_height_cm / required_physical_height_cm
        
        # Use the smaller scale factor to ensure it fits both dimensions
        adjustment_factor = min(scale_factor_width, scale_factor_height)
        
        effective_scale_cm_per_unit = user_scale_cm_per_unit * adjustment_factor
        
        print(f"Adjusting scale to {effective_scale_cm_per_unit:.4f} cm/unit to fit on A3.")
    
    # Calculate the data range that will be displayed on the A3 paper
    # This is based on the A3 paper dimensions and the effective scale
    plot_data_width = paper_width_cm / effective_scale_cm_per_unit
    plot_data_height = paper_height_cm / effective_scale_cm_per_unit

    # Center the model within this plot_data_width/height
    x_center_model = (final_min_x_data + final_max_x_data) / 2
    y_center_model = (final_min_y_data + final_max_y_data) / 2

    plot_min_x = x_center_model - plot_data_width / 2
    plot_max_x = x_center_model + plot_data_width / 2
    plot_min_y = y_center_model - plot_data_height / 2
    plot_max_y = y_center_model + plot_data_height / 2

    # Set xlim/ylim to the calculated plot_min/max_x/y
    ax.set_xlim(plot_min_x, plot_max_x)
    ax.set_ylim(plot_min_y, plot_max_y)

    # Plot lines (edges)
    if lines:
        for line_indices in lines:
            for i in range(len(line_indices) - 1):
                v1_idx, v2_idx = line_indices[i], line_indices[i+1]
                if v1_idx < len(vertices) and v2_idx < len(vertices):
                    v1, v2 = vertices[v1_idx], vertices[v2_idx]
                    ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'b-')

    # Plot face boundaries
    if faces:
        for face_indices in faces:
            # Close the loop by adding the first vertex index to the end
            closed_face_indices = face_indices + [face_indices[0]]
            for i in range(len(closed_face_indices) - 1):
                v1_idx, v2_idx = closed_face_indices[i], closed_face_indices[i+1]
                if v1_idx < len(vertices) and v2_idx < len(vertices):
                    v1, v2 = vertices[v1_idx], vertices[v2_idx]
                    ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'r-')

    # Plot individual vertices
    # if vertices:
    #     x_coords = [v[0] for v in vertices]
    #     y_coords = [v[1] for v in vertices]
    #     ax.plot(x_coords, y_coords, 'ko', markersize=3, label='Vertices')

    # Plot circles around unreferenced vertices
    # if unreferenced_vertices_coords:
    #     print("\nUnreferenced vertices detected. Please enter the desired circle diameter.")
    #     while True:
    #         try:
    #             diameter_str = input("Enter circle diameter (e.g., 0.1): ")
    #             diameter = float(diameter_str)
    #             if diameter <= 0:
    #                 print("Diameter must be a positive number.")
    #                 continue
    #         except ValueError:
    #             print("Invalid input. Please enter a number.")

    #     for ux, uy in unreferenced_vertices_coords:
    #         circle = patches.Circle((ux, uy), radius=diameter/2, edgecolor='red', facecolor='none', linestyle='-', linewidth=1.5)
    #         ax.add_patch(circle)
    #     print(f"Circles with diameter {diameter} drawn around unreferenced vertices.")

    # Remove axis labels, title, and grid for clean output
    ax.axis('off') # Turn off all axis lines, ticks, and labels
    ax.set_aspect('equal', adjustable='box') # Keep aspect ratio for correct shape

    print("\nEnter the desired filename for the PDF output (e.g., my_plot.pdf):\n")
    while True:
        pdf_filename = input("Filename: ").strip()
        if not pdf_filename:
            print("Filename cannot be empty. Please try again.")
            continue
        if not pdf_filename.lower().endswith('.pdf'):
            pdf_filename += '.pdf'
        break
    plt.savefig(pdf_filename) # Removed bbox_inches='tight' and pad_inches=0
    print(f"Graph saved to {pdf_filename}. Effective scale: 1 unit = {effective_scale_cm_per_unit:.4f} cm.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python visualize_obj.py <path_to_obj_file>")
        sys.exit(1)

    obj_file = sys.argv[1]
    verts, lns, fcs, unref_verts_coords, min_x, max_x, min_y, max_y = parse_obj(obj_file)
    plot_obj(verts, lns, fcs, unref_verts_coords, min_x, max_x, min_y, max_y)