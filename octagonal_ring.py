# Import numpy and stl libraries
import numpy as np
from stl import mesh

# Define parameters for the fresnel lens
focal_length = 100 # mm
diameter = 50 # mm
thickness = 5 # mm
n_rings = 10 # number of rings
n_sides = 8 # number of sides for each prism

# Calculate the angle and radius of each ring
angle = np.arctan(diameter / (2 * focal_length))
radius = np.linspace(0, diameter / 2, n_rings + 1)

# Create an empty list to store the vertices and faces of the mesh
vertices = []
faces = []

# Loop over each ring
for i in range(n_rings):
    # Calculate the height and width of each prism
    h = thickness - (radius[i + 1] - radius[i]) * np.tan(angle)
    w = 2 * np.pi * radius[i] / n_sides
    
    # Loop over each side of the prism
    for j in range(n_sides):
        # Calculate the angle and position of each vertex
        a = j * 2 * np.pi / n_sides
        x1 = radius[i] * np.cos(a)
        y1 = radius[i] * np.sin(a)
        z1 = 0
        
        x2 = radius[i + 1] * np.cos(a)
        y2 = radius[i + 1] * np.sin(a)
        z2 = h
        
        x3 = radius[i + 1] * np.cos(a + 2 * np.pi / n_sides)
        y3 = radius[i + 1] * np.sin(a + 2 * np.pi / n_sides)
        z3 = h
        
        x4 = radius[i] * np.cos(a + 2 * np.pi / n_sides)
        y4 = radius[i] * np.sin(a + 2 * np.pi / n_sides)
        z4 = 0
        
        # Add the vertices to the list
        vertices.append(np.array([x1, y1, z1]))
        vertices.append(np.array([x2, y2, z2]))
        vertices.append(np.array([x3, y3, z3]))
        vertices.append(np.array([x4, y4, z4]))
        
        # Add the faces to the list
        # Each face is defined by the indices of three vertices
        n = len(vertices) - 4 # The index of the first vertex of the current prism
        faces.append(np.array([n, n + 1, n + 2])) # The top face
        faces.append(np.array([n, n + 2, n + 3])) # The bottom face
        faces.append(np.array([n, n + 1, n + 3])) # The side face
        faces.append(np.array([n + 1, n + 2, n + 3])) # The side face

# Convert the lists to numpy arrays
vertices = np.array(vertices)
faces = np.array(faces)

# Create a mesh object from the vertices and faces
fresnel_lens = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        fresnel_lens.vectors[i][j] = vertices[f[j],:]

# Save the mesh as an STL file
fresnel_lens.save('fresnel_lens.stl')
