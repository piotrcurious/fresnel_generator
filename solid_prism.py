

# Fresnel lens generator

# Generates STL output file

# Assumes the fresnel lens is composed of array of prisms instead of rings

# Modified to make the STL file solid

import numpy as np

import stl

# Parameters

width = 100 # width of the lens in mm

height = 100 # height of the lens in mm

focal_length = 200 # focal length of the lens in mm

n_prisms = 10 # number of prisms per row and column

n_facets = 3 # number of facets per prism

refractive_index = 1.5 # refractive index of the lens material

thickness = 5 # thickness of the lens in mm

# Calculate the angle of each facet

theta = np.arcsin(1/refractive_index) # angle of refraction for normal incidence

alpha = np.arctan(focal_length/width) # angle of the lens plane with respect to the optical axis

beta = (np.pi - theta - alpha)/2 # angle of each facet with respect to the lens plane

gamma = np.pi - alpha - beta # angle of each facet with respect to the optical axis

# Create an empty mesh

mesh = stl.mesh.Mesh(np.zeros(n_prisms**2 * n_facets * 6, dtype=stl.mesh.Mesh.dtype))

# Loop over the prisms

for i in range(n_prisms):

    for j in range(n_prisms):

        # Calculate the coordinates of the prism vertices

        x1 = i * width / n_prisms # x coordinate of the lower left vertex

        x2 = (i + 1) * width / n_prisms # x coordinate of the lower right vertex

        y1 = j * height / n_prisms # y coordinate of the lower left vertex

        y2 = (j + 1) * height / n_prisms # y coordinate of the upper left vertex

        z1 = 0 # z coordinate of the lower vertices

        z2 = z1 + (x2 - x1) * np.tan(gamma) # z coordinate of the upper vertices

        

        # Loop over the facets

        for k in range(n_facets):

            # Calculate the coordinates of the facet vertices

            x3 = x1 + k * (x2 - x1) / n_facets # x coordinate of the lower left vertex of the facet

            x4 = x3 + (x2 - x1) / n_facets # x coordinate of the lower right vertex of the facet

            y3 = y1 + k * (y2 - y1) / n_facets # y coordinate of the lower left vertex of the facet

            y4 = y3 + (y2 - y1) / n_facets # y coordinate of the upper left vertex of the facet

            z3 = z1 + k * (z2 - z1) / n_facets # z coordinate of the lower vertices of the facet

            z4 = z3 + (z2 - z1) / n_facets # z coordinate of the upper vertices of the facet

            

            # Define the three vertices of the front triangle

            v1 = [x3, y3, z3]

            v2 = [x4, y4, z4]

            v3 = [x4, y3, z3]

            

            # Define the three vertices of the back triangle

            v4 = [x3, y3, z3 - thickness]

            v5 = [x4, y4, z4 - thickness]

            v6 = [x4, y3, z3 - thickness]

            

            # Add the front and back triangles to the mesh

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k] = np.array([v1, v2, v3])

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k + n_prisms**2 * n_facets] = np.array([v4, v5, v6])

            

            # Add four triangles to connect each pair of front and back vertices along each edge 

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k + n_prisms**2 * n_facets * 2] = np.array([v1, v4, v6])

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k + n_prisms**2 * n_facets * 2 + 1] = np.array([v1, v6, v3])

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k + n_prisms**2 * n_facets * 2 + 2] = np.array([v3, v6, v5])

            mesh.vectors[i * n_prisms * n_facets * 2 + j * n_facets * 2 + k + n_prisms**2 * n_facets * 2 + 3] = np.array([v3, v5, v2])

# Save the mesh as STL file

mesh.save('fresnel_lens_solid.stl')

