# Import numpy and scipy for numerical calculations
import numpy as np
import scipy.special as sc

# Import stl for writing STL files
import stl

# Define some parameters for the fresnel lens
diameter = 100 # mm
focal_length = 200 # mm
prism_height = 1 # mm
prism_pitch = 2 # mm
prism_angle = 45 # degrees

# Calculate the number of prisms in the lens
num_prisms = int(np.ceil(diameter / prism_pitch))

# Create an array of prism centers along the x-axis
prism_centers = np.linspace(-diameter / 2 + prism_pitch / 2, diameter / 2 - prism_pitch / 2, num_prisms)

# Create an array of prism slopes based on the fresnel equation
prism_slopes = np.sqrt(2 * (focal_length - np.sqrt(focal_length ** 2 - prism_centers ** 2)))

# Create an empty list to store the prism vertices
prism_vertices = []

# Loop over each prism center and slope
for c, s in zip(prism_centers, prism_slopes):
    # Calculate the coordinates of the four vertices of the prism
    v1 = (c - prism_pitch / 2, -prism_height / 2, 0) # lower left corner
    v2 = (c + prism_pitch / 2, -prism_height / 2, 0) # lower right corner
    v3 = (c + prism_pitch / 2 + s * np.tan(np.radians(prism_angle)), prism_height / 2, s) # upper right corner
    v4 = (c - prism_pitch / 2 + s * np.tan(np.radians(prism_angle)), prism_height / 2, s) # upper left corner
    
    # Append the vertices to the list
    prism_vertices.append([v1, v2, v3, v4])

# Create an empty list to store the prism faces
prism_faces = []

# Loop over each prism vertex list
for i, v in enumerate(prism_vertices):
    # Calculate the indices of the four vertices of the prism
    i1 = i * 4 # lower left corner
    i2 = i * 4 + 1 # lower right corner
    i3 = i * 4 + 2 # upper right corner
    i4 = i * 4 + 3 # upper left corner
    
    # Create two triangular faces for each prism using the vertex indices
    f1 = [i1, i2, i3] # lower face
    f2 = [i1, i3, i4] # upper face
    
    # Append the faces to the list
    prism_faces.append(f1)
    prism_faces.append(f2)

# Convert the lists of vertices and faces to numpy arrays
prism_vertices = np.array(prism_vertices)
prism_faces = np.array(prism_faces)

# Create a STL mesh object from the vertices and faces arrays
prism_mesh = stl.mesh.Mesh(np.zeros(prism_faces.shape[0], dtype=stl.mesh.Mesh.dtype))
for i, f in enumerate(prism_faces):
    for j in range(3):
        prism_mesh.vectors[i][j] = prism_vertices[f[j],:]

# Save the STL mesh object to a file
prism_mesh.save('fresnel_lens.stl')
