How to Use:

Open Blender (ensure you have a recent version, e.g., 3.0+).
Go to the "Scripting" workspace tab.
Click "New" to create a new text file in the Text Editor.
Copy the entire script below and paste it into the Blender Text Editor.
Adjust the parameters in the ### --- Lens Parameters --- ### section as desired.
Click the "Run Script" button (looks like a play icon) in the Text Editor header.
The script will:

Delete any previous "FresnelLens", "GroundPlane", "CatcherPlane", or "TestLight" objects.
Generate the Fresnel lens mesh according to your parameters.
Create a ground plane and a "catcher" plane near the focal point.
Add an Area light source above the lens.
Assign a basic glass material to the lens and diffuse materials to the planes.
Set the render engine to Cycles (required for refraction).
Suggest switching to Rendered Viewport Shading to see the result
