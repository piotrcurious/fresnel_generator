import numpy as np
from stl import mesh
import math

# Parameters
diameter = 100     # diameter of the lens in mm
focal_length = 200 # focal length of the lens in mm
n_rings = 20       # number of concentric rings
n_segments = 48    # number of angular segments per ring (higher = smoother circles)
refractive_index = 1.5 # refractive index of the lens material
max_depth = 5.0    # maximum depth/height of the lens in mm

# --- Input Validation ---
if n_rings <= 0:
    raise ValueError("n_rings must be positive")
if n_segments <= 0:
    raise ValueError("n_segments must be positive")
if diameter <= 0:
    raise ValueError("diameter must be positive")
if focal_length <= 0:
    raise ValueError("focal_length must be positive for a converging lens")
if refractive_index <= 1.0:
    raise ValueError("refractive_index must be greater than 1.0")
if max_depth <= 0:
    raise ValueError("max_depth must be positive")

# --- Calculations ---
radius = diameter / 2
ring_width = radius / n_rings

# Each ring has n_segments * 4 triangles (2 for top face, 2 for each side)
# Plus n_segments triangles for the central facet
num_triangles = n_segments * 4 * n_rings + n_segments
triangles = np.zeros(num_triangles, dtype=mesh.Mesh.dtype)

# --- Mesh Generation ---
t_idx = 0  # Triangle index

# Function to calculate the required height at a given radius
def calculate_height(r, phase_fraction=1.0):
    """
    Calculate the height of the lens surface at radius r
    
    Parameters:
    r: distance from center (mm)
    phase_fraction: fractional phase (0-1) for zone plates/diffractive elements
    
    Returns: height value
    """
    if r < 1e-6:  # Avoid division by zero at center
        return 0
    
    # Calculate the angle of refraction at this radius
    theta = np.arctan(r / focal_length)
    
    # Calculate height using lens maker's equation (simplified for small angles)
    # For a Fresnel lens, we use the slope at each point but "reset" the height periodically
    h_ideal = r**2 / (2 * focal_length * (refractive_index - 1))
    
    # Calculate the "sawtooth" height pattern (mod to keep within max_depth)
    h_mod = h_ideal % max_depth
    
    # For phase fraction < 1 (used in diffractive optics/zone plates)
    h_mod *= phase_fraction
    
    return h_mod

# Generate central facet (n_segments triangles forming a fan)
center = np.array([0, 0, 0])
for s in range(n_segments):
    angle1 = 2 * np.pi * s / n_segments
    angle2 = 2 * np.pi * (s + 1) / n_segments
    
    x1 = ring_width * np.cos(angle1)
    y1 = ring_width * np.sin(angle1)
    x2 = ring_width * np.cos(angle2)
    y2 = ring_width * np.sin(angle2)
    
    r1 = np.sqrt(x1**2 + y1**2)
    r2 = np.sqrt(x2**2 + y2**2)
    
    z1 = calculate_height(r1)
    z2 = calculate_height(r2)
    
    v1 = np.array([x1, y1, z1])
    v2 = np.array([x2, y2, z2])
    
    # Create triangle (center, v1, v2)
    triangles['vectors'][t_idx] = np.array([center, v1, v2])
    t_idx += 1

# Generate rings
for r in range(n_rings):
    inner_radius = ring_width * (r + 1)
    outer_radius = ring_width * (r + 2)
    
    for s in range(n_segments):
        angle1 = 2 * np.pi * s / n_segments
        angle2 = 2 * np.pi * (s + 1) / n_segments
        
        # Calculate vertices
        x1_inner = inner_radius * np.cos(angle1)
        y1_inner = inner_radius * np.sin(angle1)
        x2_inner = inner_radius * np.cos(angle2)
        y2_inner = inner_radius * np.sin(angle2)
        
        x1_outer = outer_radius * np.cos(angle1)
        y1_outer = outer_radius * np.sin(angle1)
        x2_outer = outer_radius * np.cos(angle2)
        y2_outer = outer_radius * np.sin(angle2)
        
        # Calculate heights at each vertex
        r1_inner = np.sqrt(x1_inner**2 + y1_inner**2)
        r2_inner = np.sqrt(x2_inner**2 + y2_inner**2)
        r1_outer = np.sqrt(x1_outer**2 + y1_outer**2)
        r2_outer = np.sqrt(x2_outer**2 + y2_outer**2)
        
        z1_inner = calculate_height(r1_inner)
        z2_inner = calculate_height(r2_inner)
        z1_outer = calculate_height(r1_outer)
        z2_outer = calculate_height(r2_outer)
        
        # Create vertices
        v1_inner = np.array([x1_inner, y1_inner, z1_inner])
        v2_inner = np.array([x2_inner, y2_inner, z2_inner])
        v1_outer = np.array([x1_outer, y1_outer, z1_outer])
        v2_outer = np.array([x2_outer, y2_outer, z2_outer])
        
        # Top face triangles
        triangles['vectors'][t_idx] = np.array([v1_inner, v2_inner, v1_outer])
        t_idx += 1
        triangles['vectors'][t_idx] = np.array([v2_inner, v2_outer, v1_outer])
        t_idx += 1
        
        # Create bottom face (flat at z=0) for solid model
        v1_inner_bottom = np.array([x1_inner, y1_inner, 0])
        v2_inner_bottom = np.array([x2_inner, y2_inner, 0])
        v1_outer_bottom = np.array([x1_outer, y1_outer, 0])
        v2_outer_bottom = np.array([x2_outer, y2_outer, 0])
        
        # Inner radial face
        triangles['vectors'][t_idx] = np.array([v1_inner, v1_inner_bottom, v2_inner_bottom])
        t_idx += 1
        triangles['vectors'][t_idx] = np.array([v1_inner, v2_inner_bottom, v2_inner])
        t_idx += 1

# Create the mesh object
fresnel_mesh = mesh.Mesh(triangles)

# Compute normals (important for proper rendering and 3D printing)
fresnel_mesh.update_normals()

# Save the mesh to STL file
output_filename = 'fresnel_lens_radial.stl'
fresnel_mesh.save(output_filename)

print(f"Generated radial Fresnel lens saved as '{output_filename}'")
print(f"Number of triangles: {t_idx}")  # Should match num_triangles
print(f"Maximum lens height: {max_depth} mm")
print(f"Lens diameter: {diameter} mm")
print(f"Focal length: {focal_length} mm")
