# Installation (if needed, run in your terminal or notebook cell):
# pip install numpy-stl

import numpy as np
from stl import mesh # Correct import

# Parameters
width = 100       # width of the lens in mm (X-axis)
height = 100      # height of the lens in mm (Y-axis)
focal_length = 200 # focal length of the lens in mm
n_prisms = 20     # number of prisms per row/column (higher number = smoother approximation)
refractive_index = 1.5 # refractive index of the lens material
# n_facets parameter removed as the original implementation was flawed,
# and this version uses 2 triangles per prism top face.

# --- Input Validation ---
if n_prisms <= 0:
    raise ValueError("n_prisms must be positive")
if width <= 0 or height <= 0:
    raise ValueError("width and height must be positive")
if focal_length <= 0:
    raise ValueError("focal_length must be positive for a converging lens")
if refractive_index <= 1.0:
    raise ValueError("refractive_index must be greater than 1.0")

# --- Calculations ---
prism_width = width / n_prisms
prism_height = height / n_prisms

# Calculate the number of triangles needed:
# Each prism has 2 triangles for the sloped top and 2 for the vertical riser face.
num_triangles = n_prisms * n_prisms * 4
triangles = np.zeros(num_triangles, dtype=mesh.Mesh.dtype)

# --- Mesh Generation ---
t_idx = 0 # Triangle index

for i in range(n_prisms): # Loop over columns (X)
    for j in range(n_prisms): # Loop over rows (Y)

        # Calculate base coordinates (origin at lens center)
        x1 = i * prism_width - width / 2
        x2 = (i + 1) * prism_width - width / 2
        y1 = j * prism_height - height / 2
        y2 = (j + 1) * prism_height - height / 2

        # Calculate prism center coordinates
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        # Calculate distance from the optical axis (center)
        # For this simplified square prism model, we base the slope primarily on the x-distance
        # to create a linear Fresnel effect. A true radial effect is more complex on a square grid.
        r_eff = abs(cx) # Effective distance determining the slope

        # Calculate the required slope angle (phi) of the prism surface relative to XY plane
        # Using small angle approximation: tan(delta) ≈ r / f
        # and Snell's law approximation for small angles at prism surface: delta ≈ (n - 1) * phi
        # So, tan(phi) ≈ tan(delta) / (n - 1) ≈ r / (f * (n - 1))
        if r_eff < 1e-9: # Avoid division by zero at the center
            tan_phi = 0.0
        else:
            # Using arctan for slightly better accuracy than pure small angle approx
            delta = np.arctan(r_eff / focal_length)
            tan_phi = np.tan(delta) / (refractive_index - 1)

        # Calculate the height difference (step height) across this prism based on its width
        # The height increases towards the edge further from the center x=0
        prism_step_height = prism_width * tan_phi

        # Define the 8 vertices of the prism element
        # Base vertices (at z=0)
        v1b = np.array([x1, y1, 0])
        v2b = np.array([x2, y1, 0])
        v3b = np.array([x2, y2, 0])
        v4b = np.array([x1, y2, 0])

        # Top vertices (sloped surface)
        # Height depends on which side (+x or -x) the prism is on
        if cx >= 0: # Prism is on the right side or center column
            z_inner = 0 # Height at the inner edge (closer to x=0)
            z_outer = prism_step_height # Height at the outer edge
            v1t = np.array([x1, y1, z_inner])
            v2t = np.array([x2, y1, z_outer])
            v3t = np.array([x2, y2, z_outer])
            v4t = np.array([x1, y2, z_inner])
            # Riser is at x2
            riser_v1 = v2b
            riser_v2 = v3b
            riser_v3 = v3t
            riser_v4 = v2t
        else: # Prism is on the left side
            z_inner = prism_step_height # Height at the inner edge (further from x=0)
            z_outer = 0 # Height at the outer edge (closer to x=0)
            v1t = np.array([x1, y1, z_inner])
            v2t = np.array([x2, y1, z_outer])
            v3t = np.array([x2, y2, z_outer])
            v4t = np.array([x1, y2, z_inner])
            # Riser is at x1
            riser_v1 = v1b
            riser_v2 = v4b
            riser_v3 = v4t
            riser_v4 = v1t

        # Create triangles for the sloped top face
        triangles['vectors'][t_idx] = np.array([v1t, v2t, v3t])
        t_idx += 1
        triangles['vectors'][t_idx] = np.array([v1t, v3t, v4t])
        t_idx += 1

        # Create triangles for the vertical riser face (step)
        # Ensure consistent winding order (e.g., counter-clockwise from outside)
        triangles['vectors'][t_idx] = np.array([riser_v1, riser_v2, riser_v3])
        t_idx += 1
        triangles['vectors'][t_idx] = np.array([riser_v1, riser_v3, riser_v4])
        t_idx += 1

# Create the mesh object
fresnel_mesh = mesh.Mesh(triangles)

# Save the mesh to STL file
output_filename = 'fresnel_lens_corrected.stl'
fresnel_mesh.save(output_filename)

print(f"Generated Fresnel lens saved as '{output_filename}'")
print(f"Number of triangles: {t_idx}") # Should match num_triangles
