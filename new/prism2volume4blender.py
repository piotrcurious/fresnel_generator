# Blender Script for Fresnel Lens Generation and Testing

import bpy
import bmesh
import numpy as np

# --- Cleanup Function ---
def cleanup_scene():
    """Deletes objects from previous runs of the script."""
    obj_names = ["FresnelLens", "GroundPlane", "CatcherPlane", "TestLight"]
    objs_to_delete = [obj for obj in bpy.data.objects if obj.name in obj_names]

    if objs_to_delete:
        bpy.ops.object.mode_set(mode='OBJECT') # Ensure object mode
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs_to_delete:
            obj.select_set(True)
        bpy.ops.object.delete()

    # Also delete associated mesh data and materials if they exist
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("FresnelLensMesh") or \
           mesh.name.startswith("GroundPlane") or \
           mesh.name.startswith("CatcherPlane"):
           if mesh.users == 0: # Only delete if unused
               bpy.data.meshes.remove(mesh)

    for mat in bpy.data.materials:
         if mat.name.startswith("FresnelGlass") or \
            mat.name.startswith("PlaneMaterial"):
            if mat.users == 0:
                bpy.data.materials.remove(mat)

    for light_data in bpy.data.lights:
        if light_data.name.startswith("TestLightData"):
             if light_data.users == 0:
                 bpy.data.lights.remove(light_data)

    print("Cleanup complete.")

# --- Lens Generation Function ---
def create_fresnel_lens(width_mm, height_mm, focal_length_mm, n_divisions,
                         refractive_index, groove_depth_mm, thickness_mm,
                         lens_name="FresnelLens"):
    """Generates the Fresnel lens mesh using BMesh."""

    print("Generating Fresnel Lens...")
    # Convert mm to Blender units (meters)
    scale_factor = 0.001
    width = width_mm * scale_factor
    height = height_mm * scale_factor
    focal_length = focal_length_mm * scale_factor
    groove_depth = groove_depth_mm * scale_factor
    thickness = thickness_mm * scale_factor

    # --- Vertex Calculations ---
    num_vertices_x = n_divisions + 1
    num_vertices_y = n_divisions + 1

    x_coords = np.linspace(-width / 2, width / 2, num_vertices_x)
    y_coords = np.linspace(-height / 2, height / 2, num_vertices_y)
    xx, yy = np.meshgrid(x_coords, y_coords)

    radius_sq = xx**2 + yy**2

    # Avoid division by zero/inf at focal_length = 0
    if abs(focal_length) < 1e-9:
        print("Warning: Focal length is near zero. Generating flat surface.")
        ideal_z = np.zeros_like(radius_sq)
    else:
         # Prevent division by zero if n=1
        n_minus_1 = refractive_index - 1.0
        if abs(n_minus_1) < 1e-9:
             print("Warning: Refractive index is near 1.0. Generating flat surface.")
             ideal_z = np.zeros_like(radius_sq)
        else:
            ideal_z = radius_sq / (2 * focal_length * n_minus_1)


    # Apply Fresnel modulo operation (handle potential zero groove_depth)
    if groove_depth > 1e-9:
        fresnel_z = ideal_z % (groove_depth + 1e-9) # Epsilon for float issues
    else:
        print("Warning: Groove depth is near zero. Using ideal surface.")
        fresnel_z = ideal_z # No stepping if groove depth is zero

    # --- Mesh Creation with BMesh ---
    bm = bmesh.new()

    # Create Vertices (Top and Back)
    print("Creating vertices...")
    top_verts = [[None] * num_vertices_x for _ in range(num_vertices_y)]
    back_verts = [[None] * num_vertices_x for _ in range(num_vertices_y)]
    back_z = -thickness

    for j in range(num_vertices_y):
        for i in range(num_vertices_x):
            # Top surface vertex
            z_top = fresnel_z[j, i]
            top_verts[j][i] = bm.verts.new((xx[j, i], yy[j, i], z_top))
            # Back surface vertex
            back_verts[j][i] = bm.verts.new((xx[j, i], yy[j, i], back_z))

    # --- Create Faces ---
    print("Creating faces...")
    # Top Surface Faces
    for j in range(n_divisions):
        for i in range(n_divisions):
            v1t = top_verts[j][i]
            v2t = top_verts[j][i+1]
            v3t = top_verts[j+1][i+1]
            v4t = top_verts[j+1][i]
            # Add faces (ensure consistent winding - CCW from top)
            bm.faces.new((v1t, v2t, v3t))
            bm.faces.new((v1t, v3t, v4t))

    # Back Surface Faces
    for j in range(n_divisions):
        for i in range(n_divisions):
            v1b = back_verts[j][i]
            v2b = back_verts[j][i+1]
            v3b = back_verts[j+1][i+1]
            v4b = back_verts[j+1][i]
            # Add faces (ensure consistent winding - CCW from bottom -> reversed order)
            bm.faces.new((v1b, v3b, v2b)) # Reversed
            bm.faces.new((v1b, v4b, v3b)) # Reversed

    # Side Wall Faces
    # Bottom edge (j=0)
    for i in range(n_divisions):
        v1t = top_verts[0][i]
        v2t = top_verts[0][i+1]
        v1b = back_verts[0][i]
        v2b = back_verts[0][i+1]
        bm.faces.new((v1b, v2b, v2t))
        bm.faces.new((v1b, v2t, v1t))

    # Top edge (j=n_divisions)
    y_top_idx = n_divisions
    for i in range(n_divisions):
        v4t = top_verts[y_top_idx][i]
        v3t = top_verts[y_top_idx][i+1]
        v4b = back_verts[y_top_idx][i]
        v3b = back_verts[y_top_idx][i+1]
        bm.faces.new((v4b, v3b, v3t))
        bm.faces.new((v4b, v3t, v4t))

    # Left edge (i=0)
    for j in range(n_divisions):
        v1t = top_verts[j][0]
        v4t = top_verts[j+1][0]
        v1b = back_verts[j][0]
        v4b = back_verts[j+1][0]
        bm.faces.new((v1b, v4b, v4t))
        bm.faces.new((v1b, v4t, v1t))

    # Right edge (i=n_divisions)
    x_right_idx = n_divisions
    for j in range(n_divisions):
        v2t = top_verts[j][x_right_idx]
        v3t = top_verts[j+1][x_right_idx]
        v2b = back_verts[j][x_right_idx]
        v3b = back_verts[j+1][x_right_idx]
        bm.faces.new((v2b, v3b, v3t))
        bm.faces.new((v2b, v3t, v2t))

    # --- Finalize Mesh ---
    print("Finalizing mesh...")
    # Recalculate normals (important for closed manifold)
    bm.normal_update()

    # Create Blender mesh datablock and object
    mesh_data = bpy.data.meshes.new(lens_name + "Mesh")
    bm.to_mesh(mesh_data)
    bm.free() # Free BMesh data

    lens_obj = bpy.data.objects.new(lens_name, mesh_data)

    # Link object to the scene collection
    bpy.context.collection.objects.link(lens_obj)
    print("Lens generation complete.")
    return lens_obj

# --- Material Setup Function ---
def setup_materials(lens_obj, refractive_index):
    """Creates and assigns materials."""
    print("Setting up materials...")
    # Create Glass Material for Lens
    glass_mat = bpy.data.materials.new(name="FresnelGlass")
    glass_mat.use_nodes = True
    principled_bsdf = glass_mat.node_tree.nodes.get('Principled BSDF')
    if principled_bsdf:
        principled_bsdf.inputs['Transmission'].default_value = 1.0  # Make it transparent
        principled_bsdf.inputs['Roughness'].default_value = 0.05 # Slightly glossy
        principled_bsdf.inputs['IOR'].default_value = refractive_index # Set Index of Refraction
    lens_obj.data.materials.append(glass_mat)

    # Create Simple Diffuse Material for Planes
    plane_mat = bpy.data.materials.new(name="PlaneMaterial")
    plane_mat.use_nodes = True
    plane_bsdf = plane_mat.node_tree.nodes.get('Principled BSDF')
    if plane_bsdf:
        plane_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0) # Light gray
        plane_bsdf.inputs['Roughness'].default_value = 0.8

    print("Materials assigned.")
    return plane_mat # Return plane material for reuse

# --- Scene Setup Function ---
def setup_test_scene(lens_obj, focal_length_mm, width_mm, height_mm, plane_mat):
    """Creates ground plane, catcher plane, and light source."""
    print("Setting up test scene...")
    scale_factor = 0.001
    focal_length = focal_length_mm * scale_factor
    width = width_mm * scale_factor
    height = height_mm * scale_factor

    # Ground Plane (optional, for context)
    ground_size = max(width, height) * 5
    bpy.ops.mesh.primitive_plane_add(size=ground_size, location=(0, 0, -focal_length * 1.5))
    ground_plane = bpy.context.object
    ground_plane.name = "GroundPlane"
    ground_plane.data.materials.append(plane_mat)


    # Catcher Plane (near focal point)
    catcher_size = max(width, height) * 1.5
    # Place it slightly beyond the focal point to see the focused spot
    catcher_z = -focal_length * 1.05
    bpy.ops.mesh.primitive_plane_add(size=catcher_size, location=(0, 0, catcher_z))
    catcher_plane = bpy.context.object
    catcher_plane.name = "CatcherPlane"
    catcher_plane.data.materials.append(plane_mat)


    # Light Source (Area Light simulating parallel rays)
    light_distance = focal_length * 2 # Place light reasonably far above
    light_size = max(width, height) * 1.2 # Make light slightly larger than lens
    light_data = bpy.data.lights.new(name="TestLightData", type='AREA')
    light_data.energy = 200 # Adjust power as needed (Watts for Area light)
    light_data.shape = 'RECTANGLE'
    light_data.size = light_size
    light_data.size_y = light_size # Make it square or match lens aspect if needed

    light_obj = bpy.data.objects.new(name="TestLight", object_data=light_data)
    light_obj.location = (0, 0, light_distance)
    # Pointing straight down (-Z) - already default for new area lights usually
    # light_obj.rotation_euler = (0, 0, 0) # Or np.radians(180) on X if needed

    bpy.context.collection.objects.link(light_obj)

    # Ensure Cycles Render Engine is selected
    bpy.context.scene.render.engine = 'CYCLES'
    # Optional: Set device to GPU if available
    # bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA' # Or 'OPTIX', 'HIP', 'METAL'
    # bpy.context.scene.cycles.device = 'GPU'

    # Set smooth shading for the lens
    lens_obj.select_set(True)
    bpy.context.view_layer.objects.active = lens_obj
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')


    print("Scene setup complete.")
    print("\n--> Switch Viewport Shading to 'Rendered' to see the effect <---")


# --- Main Execution ---

### --- Lens Parameters --- ###
LENS_WIDTH_MM = 100
LENS_HEIGHT_MM = 100
FOCAL_LENGTH_MM = 150   # Positive for converging
N_DIVISIONS = 80       # Number of steps/divisions along width/height (higher = smoother/slower)
REFRACTIVE_INDEX = 1.52 # e.g., for Acrylic
GROOVE_DEPTH_MM = 0.5   # Max depth of grooves
THICKNESS_MM = 5.0      # Overall lens thickness
### --------------------- ###

# 1. Cleanup from previous runs
cleanup_scene()

# 2. Generate the lens object
lens_object = create_fresnel_lens(
    width_mm=LENS_WIDTH_MM,
    height_mm=LENS_HEIGHT_MM,
    focal_length_mm=FOCAL_LENGTH_MM,
    n_divisions=N_DIVISIONS,
    refractive_index=REFRACTIVE_INDEX,
    groove_depth_mm=GROOVE_DEPTH_MM,
    thickness_mm=THICKNESS_MM,
    lens_name="FresnelLens"
)

if lens_object:
    # 3. Setup Materials
    plane_material = setup_materials(lens_object, REFRACTIVE_INDEX)

    # 4. Setup Test Scene
    setup_test_scene(lens_object, FOCAL_LENGTH_MM, LENS_WIDTH_MM, LENS_HEIGHT_MM, plane_material)
else:
    print("Error: Lens object not created.")
