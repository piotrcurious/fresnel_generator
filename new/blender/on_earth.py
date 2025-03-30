# Blender Script for Fresnel Lens Generation and Testing
# Uses Sun Position addon for realistic lighting based on Lat/Lon/Date/Time

import bpy
import bmesh
import numpy as np
import datetime # Used for time conversion

# --- Parameters ---

# Lens Parameters
LENS_WIDTH_MM = 100
LENS_HEIGHT_MM = 100
FOCAL_LENGTH_MM = 150   # Positive for converging
N_DIVISIONS = 80       # Number of steps/divisions along width/height
REFRACTIVE_INDEX = 1.52 # e.g., for Acrylic
GROOVE_DEPTH_MM = 0.5   # Max depth of grooves
THICKNESS_MM = 5.0      # Overall lens thickness

# Location Parameters
LATITUDE = 34.0522  # Decimal degrees (e.g., Los Angeles)
LONGITUDE = -118.2437 # Decimal degrees (e.g., Los Angeles)

# Date & Time Parameters (Local Time)
YEAR = 2025
MONTH = 3       # March
DAY = 30
HOUR = 14        # 2 PM (24-hour format)
MINUTE = 0
SECOND = 0
UTC_OFFSET = -7 # Example: Pacific Daylight Time (PDT). Standard (PST) would be -8. Adjust for your zone and DST.

# Scene Parameters
SUN_ENERGY = 5.0 # Strength of the sun lamp

# --- Helper Functions ---

def enable_addon(addon_module_name):
    """Checks if an addon is enabled, enables it if not."""
    if addon_module_name not in bpy.context.preferences.addons:
        print(f"Addon '{addon_module_name}' not found. Please install or ensure it's available.")
        return False

    if not bpy.context.preferences.addons[addon_module_name].preferences.is_enabled:
        print(f"Enabling addon: {addon_module_name}")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
    else:
        print(f"Addon '{addon_module_name}' is already enabled.")

    # Check again after trying to enable
    return bpy.context.preferences.addons[addon_module_name].preferences.is_enabled


def cleanup_scene():
    """Deletes objects from previous runs of the script."""
    obj_names = ["FresnelLens", "GroundPlane", "CatcherPlane", "SunLight"] # Changed name
    objs_to_delete = [obj for obj in bpy.data.objects if obj.name in obj_names]

    if objs_to_delete:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs_to_delete:
            obj.select_set(True)
        bpy.ops.object.delete()

    # Clean up unused data blocks
    for mesh in bpy.data.meshes:
        if mesh.name.startswith("FresnelLensMesh") or \
           mesh.name.startswith("GroundPlane") or \
           mesh.name.startswith("CatcherPlane"):
           if mesh.users == 0:
               bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
         if mat.name.startswith("FresnelGlass") or \
            mat.name.startswith("PlaneMaterial"):
            if mat.users == 0:
                bpy.data.materials.remove(mat)
    for light_data in bpy.data.lights:
        if light_data.name.startswith("SunData"): # Changed name
             if light_data.users == 0:
                 bpy.data.lights.remove(light_data)

    print("Cleanup complete.")


def create_fresnel_lens(width_mm, height_mm, focal_length_mm, n_divisions,
                         refractive_index, groove_depth_mm, thickness_mm,
                         lens_name="FresnelLens"):
    """Generates the Fresnel lens mesh using BMesh. (Identical to previous version)"""

    print("Generating Fresnel Lens...")
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

    if abs(focal_length) < 1e-9:
        print("Warning: Focal length is near zero. Generating flat surface.")
        ideal_z = np.zeros_like(radius_sq)
    else:
        n_minus_1 = refractive_index - 1.0
        if abs(n_minus_1) < 1e-9:
             print("Warning: Refractive index is near 1.0. Generating flat surface.")
             ideal_z = np.zeros_like(radius_sq)
        else:
            ideal_z = radius_sq / (2 * focal_length * n_minus_1)

    if groove_depth > 1e-9:
        fresnel_z = ideal_z % (groove_depth + 1e-9)
    else:
        print("Warning: Groove depth is near zero. Using ideal surface.")
        fresnel_z = ideal_z

    # --- Mesh Creation with BMesh ---
    bm = bmesh.new()
    print("Creating vertices...")
    top_verts = [[None] * num_vertices_x for _ in range(num_vertices_y)]
    back_verts = [[None] * num_vertices_x for _ in range(num_vertices_y)]
    back_z = -thickness

    for j in range(num_vertices_y):
        for i in range(num_vertices_x):
            z_top = fresnel_z[j, i]
            top_verts[j][i] = bm.verts.new((xx[j, i], yy[j, i], z_top))
            back_verts[j][i] = bm.verts.new((xx[j, i], yy[j, i], back_z))

    print("Creating faces...")
    # Top Surface Faces
    for j in range(n_divisions):
        for i in range(n_divisions):
            v1t,v2t,v3t,v4t = top_verts[j][i], top_verts[j][i+1], top_verts[j+1][i+1], top_verts[j+1][i]
            bm.faces.new((v1t, v2t, v3t)); bm.faces.new((v1t, v3t, v4t))
    # Back Surface Faces
    for j in range(n_divisions):
        for i in range(n_divisions):
            v1b,v2b,v3b,v4b = back_verts[j][i], back_verts[j][i+1], back_verts[j+1][i+1], back_verts[j+1][i]
            bm.faces.new((v1b, v3b, v2b)); bm.faces.new((v1b, v4b, v3b))
    # Side Wall Faces (Bottom, Top, Left, Right)
    for i in range(n_divisions): # Bottom j=0
        v1t,v2t,v1b,v2b=top_verts[0][i], top_verts[0][i+1], back_verts[0][i], back_verts[0][i+1]
        bm.faces.new((v1b, v2b, v2t)); bm.faces.new((v1b, v2t, v1t))
    y_top_idx = n_divisions
    for i in range(n_divisions): # Top j=N
        v4t,v3t,v4b,v3b=top_verts[y_top_idx][i], top_verts[y_top_idx][i+1], back_verts[y_top_idx][i], back_verts[y_top_idx][i+1]
        bm.faces.new((v4b, v3b, v3t)); bm.faces.new((v4b, v3t, v4t))
    for j in range(n_divisions): # Left i=0
        v1t,v4t,v1b,v4b=top_verts[j][0], top_verts[j+1][0], back_verts[j][0], back_verts[j+1][0]
        bm.faces.new((v1b, v4b, v4t)); bm.faces.new((v1b, v4t, v1t))
    x_right_idx = n_divisions
    for j in range(n_divisions): # Right i=N
        v2t,v3t,v2b,v3b=top_verts[j][x_right_idx], top_verts[j+1][x_right_idx], back_verts[j][x_right_idx], back_verts[j+1][x_right_idx]
        bm.faces.new((v2b, v3b, v3t)); bm.faces.new((v2b, v3t, v2t))

    print("Finalizing mesh...")
    bm.normal_update()
    mesh_data = bpy.data.meshes.new(lens_name + "Mesh")
    bm.to_mesh(mesh_data)
    bm.free()
    lens_obj = bpy.data.objects.new(lens_name, mesh_data)
    bpy.context.collection.objects.link(lens_obj)
    print("Lens generation complete.")
    return lens_obj


def setup_materials(lens_obj, refractive_index):
    """Creates and assigns materials. (Identical to previous version)"""
    print("Setting up materials...")
    # Glass Material
    glass_mat = bpy.data.materials.new(name="FresnelGlass")
    glass_mat.use_nodes = True
    principled_bsdf = glass_mat.node_tree.nodes.get('Principled BSDF')
    if principled_bsdf:
        principled_bsdf.inputs['Transmission'].default_value = 1.0
        principled_bsdf.inputs['Roughness'].default_value = 0.05
        principled_bsdf.inputs['IOR'].default_value = refractive_index
    lens_obj.data.materials.append(glass_mat)
    # Plane Material
    plane_mat = bpy.data.materials.new(name="PlaneMaterial")
    plane_mat.use_nodes = True
    plane_bsdf = plane_mat.node_tree.nodes.get('Principled BSDF')
    if plane_bsdf:
        plane_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
        plane_bsdf.inputs['Roughness'].default_value = 0.8
    print("Materials assigned.")
    return plane_mat


def setup_sun_scene(lens_obj, focal_length_mm, width_mm, height_mm, plane_mat,
                     lat, lon, year, month, day, hour, minute, second, utc_offset, sun_energy):
    """Sets up scene with Sun Position addon driving a Sun lamp and sky."""
    print("Setting up Sun Position scene...")
    scale_factor = 0.001
    focal_length = focal_length_mm * scale_factor
    width = width_mm * scale_factor
    height = height_mm * scale_factor

    # --- Ensure Sun Position Addon is Enabled ---
    if not enable_addon('sun_position'):
         print("ERROR: Sun Position addon could not be enabled. Aborting scene setup.")
         # Optionally raise an error: raise RuntimeError("Sun Position addon failed to enable")
         return # Exit setup if addon fails

    # --- Ground Plane ---
    ground_size = max(width, height) * 10 # Larger ground
    bpy.ops.mesh.primitive_plane_add(size=ground_size, location=(0, 0, -focal_length * 1.5 - thickness_mm*scale_factor)) # Lower ground slightly
    ground_plane = bpy.context.object
    ground_plane.name = "GroundPlane"
    if plane_mat: ground_plane.data.materials.append(plane_mat)

    # --- Catcher Plane ---
    catcher_size = max(width, height) * 1.5
    catcher_z = -focal_length # Place relative to lens center (at z=0 average)
    bpy.ops.mesh.primitive_plane_add(size=catcher_size, location=(0, 0, catcher_z))
    catcher_plane = bpy.context.object
    catcher_plane.name = "CatcherPlane"
    if plane_mat: catcher_plane.data.materials.append(plane_mat)

    # --- Create Sun Lamp ---
    sun_data = bpy.data.lights.new(name="SunData", type='SUN')
    sun_data.energy = sun_energy # Adjust brightness
    sun_obj = bpy.data.objects.new(name="SunLight", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    print(f"Created Sun Lamp: {sun_obj.name}")

    # --- Configure Sun Position Addon ---
    world = bpy.context.scene.world
    if world is None:
        print("Creating new World")
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    # Access addon properties (might differ slightly across Blender versions)
    # Usually attached to World properties
    sp_props = world.sun_position_properties # Get the addon's property group

    # Set Location
    sp_props.latitude = lat
    sp_props.longitude = lon

    # Set Date & Time
    # The addon takes local time + UTC offset
    sp_props.year = year
    sp_props.month = month
    sp_props.day = day
    # Convert time to decimal hours for the addon property
    sp_props.time = hour + minute / 60.0 + second / 3600.0
    sp_props.utc_offset = utc_offset

    # Link the Sun object we created
    sp_props.sun_object = sun_obj
    print(f"Linked {sun_obj.name} to Sun Position addon.")

    # Enable Sky Texture integration
    sp_props.use_sky_texture = True
    world.use_nodes = True # Ensure world nodes are enabled

    # Update the sun position (may not be strictly necessary, but good practice)
    # This might trigger internal updates in the addon
    world.update_tag()
    bpy.context.view_layer.update() # Update the view layer as well

    print(f"Sun position calculated for {lat=}, {lon=}, Date={year}-{month:02d}-{day:02d}, Time={hour:02d}:{minute:02d}:{second:02d}, UTC Offset={utc_offset:+}")
    print(f"Sun Object Rotation (Euler XYZ): {np.degrees(sun_obj.rotation_euler)}")


    # --- Final Scene Adjustments ---
    bpy.context.scene.render.engine = 'CYCLES'
    lens_obj.select_set(True)
    bpy.context.view_layer.objects.active = lens_obj
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')

    print("Scene setup complete.")
    print("\n--> Switch Viewport Shading to 'Rendered' to see the effect <---")
    print("--> You may need to increase Sun Energy or adjust Exposure (Render Properties > Color Management) <--")


# --- Main Execution ---

# 1. Cleanup
cleanup_scene()

# 2. Generate Lens
lens_object = create_fresnel_lens(
    width_mm=LENS_WIDTH_MM,
    height_mm=LENS_HEIGHT_MM,
    focal_length_mm=FOCAL_LENGTH_MM,
    n_divisions=N_DIVISIONS,
    refractive_index=REFRACTIVE_INDEX,
    groove_depth_mm=GROOVE_DEPTH_MM,
    thickness_mm=THICKNESS_MM
)

if lens_object:
    # 3. Setup Materials
    plane_material = setup_materials(lens_object, REFRACTIVE_INDEX)

    # 4. Setup Sun Scene
    setup_sun_scene(
        lens_obj=lens_object,
        focal_length_mm=FOCAL_LENGTH_MM,
        width_mm=LENS_WIDTH_MM,
        height_mm=LENS_HEIGHT_MM,
        plane_mat=plane_material,
        lat=LATITUDE,
        lon=LONGITUDE,
        year=YEAR,
        month=MONTH,
        day=DAY,
        hour=HOUR,
        minute=MINUTE,
        second=SECOND,
        utc_offset=UTC_OFFSET,
        sun_energy=SUN_ENERGY
    )
else:
    print("Error: Lens object could not be created.")
