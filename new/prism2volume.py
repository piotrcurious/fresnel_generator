# Installation (if needed, run in your terminal or notebook cell):
# pip install numpy-stl

import numpy as np
from stl import mesh # Correct import

# --- Parameters ---
width = 100       # width of the lens in mm (X-axis)
height = 100      # height of the lens in mm (Y-axis)
focal_length = 200 # focal length of the lens in mm (positive for converging)
n_prisms = 50     # number of divisions per row/column (higher = smoother)
refractive_index = 1.5 # refractive index of the lens material
groove_depth = 1.0   # The maximum depth of the Fresnel grooves/steps in mm
thickness = 5.0    # The total thickness of the lens body in mm

# --- Input Validation ---
if n_prisms <= 0:
    raise ValueError("n_prisms must be positive")
if width <= 0 or height <= 0:
    raise ValueError("width and height must be positive")
if focal_length == 0:
    raise ValueError("focal_length cannot be zero")
if refractive_index <= 1.0:
    raise ValueError("refractive_index must be greater than 1.0")
if groove_depth <= 0:
    raise ValueError("groove_depth must be positive")
if thickness <= 0:
     raise ValueError("thickness must be positive")

# --- Calculations ---
# We need vertices, not just prisms, so (n+1) points for n segments
num_vertices_x = n_prisms + 1
num_vertices_y = n_prisms + 1

# Create grid coordinates (centered at 0,0)
x_coords = np.linspace(-width / 2, width / 2, num_vertices_x)
y_coords = np.linspace(-height / 2, height / 2, num_vertices_y)
xx, yy = np.meshgrid(x_coords, y_coords)

# Calculate ideal continuous lens surface height (parabolic approximation)
# z = r^2 / (2 * f * (n - 1)), where r^2 = x^2 + y^2
# For diverging lens (f < 0), this formula still works if n > 1
radius_sq = xx**2 + yy**2
ideal_z = radius_sq / (2 * focal_length * (refractive_index - 1.0))

# Apply Fresnel modulo operation
# Add a small epsilon to groove_depth in modulo to handle floating point issues at boundaries
fresnel_z = ideal_z % (groove_depth + 1e-9)

# --- Mesh Generation ---
# Calculate number of triangles
# Top: n_prisms * n_prisms * 2
# Back: n_prisms * n_prisms * 2
# Sides: 4 * n_prisms * 2
num_triangles = (n_prisms * n_prisms * 4) + (4 * n_prisms * 2)
triangles = np.zeros(num_triangles, dtype=mesh.Mesh.dtype)
t_idx = 0 # Triangle index

# Generate Top Surface Triangles
for i in range(n_prisms):
    for j in range(n_prisms):
        # Get vertices for the current quad
        v1 = np.array([xx[j, i],   yy[j, i],   fresnel_z[j, i]])
        v2 = np.array([xx[j, i+1], yy[j, i+1], fresnel_z[j, i+1]])
        v3 = np.array([xx[j+1, i+1], yy[j+1, i+1], fresnel_z[j+1, i+1]])
        v4 = np.array([xx[j+1, i], yy[j+1, i], fresnel_z[j+1, i]])

        # Triangle 1 (v1, v2, v3) - CCW from top
        triangles['vectors'][t_idx] = np.array([v1, v2, v3])
        t_idx += 1
        # Triangle 2 (v1, v3, v4) - CCW from top
        triangles['vectors'][t_idx] = np.array([v1, v3, v4])
        t_idx += 1

# Generate Back Plane Triangles (at z = -thickness)
back_z = -thickness
for i in range(n_prisms):
    for j in range(n_prisms):
        # Get base vertices for the current quad
        v1b = np.array([xx[j, i],   yy[j, i],   back_z])
        v2b = np.array([xx[j, i+1], yy[j, i+1], back_z])
        v3b = np.array([xx[j+1, i+1], yy[j+1, i+1], back_z])
        v4b = np.array([xx[j+1, i], yy[j+1, i], back_z])

        # Triangle 1 (v1b, v3b, v2b) - Reversed order for CCW from bottom
        triangles['vectors'][t_idx] = np.array([v1b, v3b, v2b])
        t_idx += 1
        # Triangle 2 (v1b, v4b, v3b) - Reversed order for CCW from bottom
        triangles['vectors'][t_idx] = np.array([v1b, v4b, v3b])
        t_idx += 1

# Generate Side Wall Triangles
# Bottom edge (j=0)
for i in range(n_prisms):
    v1t = np.array([xx[0, i],   yy[0, i],   fresnel_z[0, i]])
    v2t = np.array([xx[0, i+1], yy[0, i+1], fresnel_z[0, i+1]])
    v1b = np.array([xx[0, i],   yy[0, i],   back_z])
    v2b = np.array([xx[0, i+1], yy[0, i+1], back_z])
    # Wall quad: v1b, v2b, v2t, v1t
    triangles['vectors'][t_idx] = np.array([v1b, v2b, v2t]) # Triangle 1
    t_idx += 1
    triangles['vectors'][t_idx] = np.array([v1b, v2t, v1t]) # Triangle 2
    t_idx += 1

# Top edge (j=n_prisms)
y_top_idx = n_prisms
for i in range(n_prisms):
    v4t = np.array([xx[y_top_idx, i],   yy[y_top_idx, i],   fresnel_z[y_top_idx, i]])
    v3t = np.array([xx[y_top_idx, i+1], yy[y_top_idx, i+1], fresnel_z[y_top_idx, i+1]])
    v4b = np.array([xx[y_top_idx, i],   yy[y_top_idx, i],   back_z])
    v3b = np.array([xx[y_top_idx, i+1], yy[y_top_idx, i+1], back_z])
    # Wall quad: v4b, v3b, v3t, v4t
    triangles['vectors'][t_idx] = np.array([v4b, v3b, v3t]) # Triangle 1
    t_idx += 1
    triangles['vectors'][t_idx] = np.array([v4b, v3t, v4t]) # Triangle 2
    t_idx += 1

# Left edge (i=0)
for j in range(n_prisms):
    v1t = np.array([xx[j, 0],   yy[j, 0],   fresnel_z[j, 0]])
    v4t = np.array([xx[j+1, 0], yy[j+1, 0], fresnel_z[j+1, 0]])
    v1b = np.array([xx[j, 0],   yy[j, 0],   back_z])
    v4b = np.array([xx[j+1, 0], yy[j+1, 0], back_z])
    # Wall quad: v1b, v4b, v4t, v1t
    triangles['vectors'][t_idx] = np.array([v1b, v4b, v4t]) # Triangle 1
    t_idx += 1
    triangles['vectors'][t_idx] = np.array([v1b, v4t, v1t]) # Triangle 2
    t_idx += 1

# Right edge (i=n_prisms)
x_right_idx = n_prisms
for j in range(n_prisms):
    v2t = np.array([xx[j, x_right_idx],   yy[j, x_right_idx],   fresnel_z[j, x_right_idx]])
    v3t = np.array([xx[j+1, x_right_idx], yy[j+1, x_right_idx], fresnel_z[j+1, x_right_idx]])
    v2b = np.array([xx[j, x_right_idx],   yy[j, x_right_idx],   back_z])
    v3b = np.array([xx[j+1, x_right_idx], yy[j+1, x_right_idx], back_z])
    # Wall quad: v2b, v3b, v3t, v2t
    triangles['vectors'][t_idx] = np.array([v2b, v3b, v3t]) # Triangle 1
    t_idx += 1
    triangles['vectors'][t_idx] = np.array([v2b, v3t, v2t]) # Triangle 2
    t_idx += 1


# --- Create and Save Mesh ---
# Create the mesh object
fresnel_mesh = mesh.Mesh(triangles.copy()) # Use copy to be safe

# Save the mesh to STL file
output_filename = 'fresnel_lens_radial_volume.stl'
fresnel_mesh.save(output_filename)

print(f"Generated Radial Fresnel lens with volume saved as '{output_filename}'")
print(f"Number of divisions per side: {n_prisms}")
print(f"Lens dimensions: {width}mm x {height}mm")
print(f"Focal Length: {focal_length}mm")
print(f"Groove Depth: {groove_depth}mm")
print(f"Body Thickness: {thickness}mm")
print(f"Total triangles: {t_idx}") # Verify against calculation
if t_idx != num_triangles:
    print(f"Warning: Actual triangles ({t_idx}) differs from calculated ({num_triangles})")
