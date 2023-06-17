# fresnel_generator
python fresnel lens junkbox, by BingAI 
The code works by dividing the lens into a grid of prisms, and then dividing each prism into a number of facets. Each facet is a triangular surface that refracts light according to Snell's law. The code calculates the coordinates of each facet vertex based on the parameters of the lens and the refractive index of the material. Then it creates a mesh object that stores the vertices of all the facets as vectors. Finally, it saves the mesh as an STL file that can be used for 3D printing or rendering.

The n_facets parameter controls how many facets are used to approximate each prism. The higher the n_facets, the smoother the lens surface and the more accurate the refraction. However, increasing n_facets also increases the computational complexity and the size of the STL file. A reasonable value for n_facets depends on the desired resolution and quality of the lens.
