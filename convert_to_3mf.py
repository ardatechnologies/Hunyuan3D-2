#!/usr/bin/env python3
"""
GLB to Automated 3MF Converter

This script converts a textured GLB 3D model into a single, multi-part 3MF file
with embedded color information. The output is specifically structured to be
compatible with slicers like Bambu Studio, allowing for one-click import of a
multi-color model ready for printing with an AMS (Automatic Material System).

The process involves:
1. Loading a GLB file using the 'trimesh' library.
2. Partitioning the mesh into separate parts based on a defined color palette.
3. Manually cleaning the geometry of each part to ensure compatibility.
4. Programmatically constructing a 3MF file using the 'lib3mf' library,
   where each color part is a distinct object with a base color material.

Dependencies:
- trimesh
- numpy
- lib3mf

Usage:
    python create_automated_3mf.py [input_file] [output_file] [--tolerance N]
    
Examples:
    # Use default input/output names
    python create_automated_3mf.py

    # Specify input and output files
    python create_automated_3mf.py astronaut_3d.glb automated_astronaut.3mf

    # Adjust the color matching tolerance
    python create_automated_3mf.py --tolerance 20
"""

import argparse
import sys
import time
from pathlib import Path

import trimesh
from trimesh import repair
import numpy as np
import lib3mf
from lib3mf import get_wrapper


def get_color_distance(rgb1, rgb2):
    """
    Calculates the perceptual distance between two RGB colors.
    Uses a weighted Euclidean distance that approximates human perception.
    A low distance (e.g., < 10) means they are very similar.
    """
    # Convert to float and normalize to 0-1 range
    r1, g1, b1 = rgb1[0]/255.0, rgb1[1]/255.0, rgb1[2]/255.0
    r2, g2, b2 = rgb2[0]/255.0, rgb2[1]/255.0, rgb2[2]/255.0
    
    # Simple perceptual distance using weighted RGB differences
    # Human eye is more sensitive to green, then red, then blue
    dr = (r1 - r2) ** 2
    dg = (g1 - g2) ** 2 * 2  # Green is more perceptually important
    db = (b1 - b2) ** 2
    
    # Return perceptual distance (scaled to be similar to delta_e_cie2000)
    return np.sqrt(dr + dg + db) * 100


def format_time(seconds):
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def convert_glb_to_automated_3mf(input_file, output_file, mode='hardcoded', tolerance=15):
    """
    Convert a GLB file to a single multi-part 3MF file with embedded colors.
    
    Args:
        input_file: Path to input GLB file
        output_file: Path for the output 3MF file
        mode: 'hardcoded' or 'auto' (auto not implemented yet)
        tolerance: Color matching tolerance for hardcoded mode
    
    Returns:
        Path to the generated 3MF file
    """
    # Start total timer
    total_start = time.time()
    
    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input GLB file not found: {input_path}")
    
    output_path = Path(output_file)
    
    print(f"📁 Input GLB: {input_path}")
    print(f"💾 Output 3MF: {output_path}")
    print(f"🎨 Mode: {mode}")
    print(f"🎯 Tolerance: {tolerance}")
    print()
    
    # Define color palette for hardcoded mode
    if mode == 'hardcoded':
        COLOR_PALETTE = {
            "WHITE": [255, 255, 255],
            "RED": [210, 30, 45],       # Approximate red from gloves/boots
            "BLUE_VISOR": [25, 30, 70]  # Approximate blue from visor
        }
    elif mode == 'auto':
        print("⚠️  Auto mode not implemented yet. Using hardcoded mode instead.")
        COLOR_PALETTE = {
            "WHITE": [255, 255, 255],
            "RED": [210, 30, 45],
            "BLUE_VISOR": [25, 30, 70]
        }
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # Load the GLB file
    print("⏱️  Loading GLB file...")
    step_start = time.time()
    try:
        mesh = trimesh.load(input_path, force='mesh')
        print(f"   ✓ GLB loaded: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces ({format_time(time.time() - step_start)})")
    except Exception as e:
        raise RuntimeError(f"Failed to load GLB file: {e}")
    
    # Convert texture to vertex colors
    print("⏱️  Converting texture to vertex colors...")
    step_start = time.time()
    try:
        # Check if mesh has visual data
        if hasattr(mesh.visual, 'to_color'):
            mesh.vertex_colors = mesh.visual.to_color().vertex_colors
            print(f"   ✓ Vertex colors extracted ({format_time(time.time() - step_start)})")
        else:
            raise RuntimeError("No visual/texture data found in GLB file")
    except Exception as e:
        raise RuntimeError(f"Failed to convert texture to vertex colors: {e}")
    
    # Group faces by their average color
    print("⏱️  Grouping faces by color...")
    step_start = time.time()
    
    face_indices_by_color = {name: [] for name in COLOR_PALETTE}
    unmatched_faces = []
    
    for i, face in enumerate(mesh.faces):
        # Get the colors of the three vertices for this face
        vertex_colors = mesh.vertex_colors[face]
        
        # Get the average color of the face (R, G, B channels, ignore Alpha)
        avg_color = np.mean(vertex_colors[:, :3], axis=0)
        
        # Find the closest matching color from our palette
        best_match = None
        min_dist = float('inf')
        
        for color_name, color_rgb in COLOR_PALETTE.items():
            dist = get_color_distance(avg_color, color_rgb)
            if dist < min_dist:
                min_dist = dist
                best_match = color_name
        
        # If the match is "close enough", add its index to the list
        if min_dist < tolerance:
            face_indices_by_color[best_match].append(i)
        else:
            # For unmatched faces, assign to closest color anyway (option a)
            face_indices_by_color[best_match].append(i)
            unmatched_faces.append((i, min_dist))
    
    print(f"   ✓ Face grouping complete ({format_time(time.time() - step_start)})")
    
    # Report face distribution
    for color_name, face_indices in face_indices_by_color.items():
        print(f"   📊 {color_name}: {len(face_indices)} faces")
    
    if unmatched_faces:
        print(f"   ⚠️  {len(unmatched_faces)} faces assigned to closest color (outside tolerance)")
    
    # Create new meshes by splitting based on the face groups
    print("⏱️  Creating separate meshes per color...")
    step_start = time.time()
    
    # Define material colors for each color name
    material_colors = {
        "WHITE": [255, 255, 255, 255],    # RGBA
        "RED": [210, 30, 45, 255],         # RGBA  
        "BLUE_VISOR": [25, 30, 70, 255]    # RGBA
    }
    
    new_meshes = []
    for color_name, face_indices in face_indices_by_color.items():
        if not face_indices:  # Skip if no faces were found for this color
            print(f"   ⚠️  No faces found for {color_name}, skipping")
            continue
        
        # Create a new mesh for this color
        new_mesh = mesh.copy()
        
        # Keep only the faces that match this color
        new_mesh.update_faces(face_indices)
        
        # Remove any vertices that are no longer used
        new_mesh.remove_unreferenced_vertices()
        
        # Remove any existing vertex colors (they get lost anyway)
        if hasattr(new_mesh, 'vertex_colors'):
            new_mesh.vertex_colors = None
        
        # Apply material color to the entire mesh
        material_color = material_colors[color_name]
        new_mesh.visual.face_colors = material_color
        
        # Store this mesh with color name for identification
        new_mesh.metadata = {'color_name': color_name}
        new_meshes.append(new_mesh)
        
        print(f"   ✓ {color_name}: {len(new_mesh.vertices)} vertices, {len(new_mesh.faces)} faces")
        print(f"   🎨 Applied material color: {material_color[:3]} (RGB)")
    
    print(f"   ✓ Mesh splitting complete ({format_time(time.time() - step_start)})")
    
    # Export to a single, multi-part 3MF file using lib3mf
    if new_meshes:
        print("⏱️  Constructing automated 3MF file...")
        step_start = time.time()
        
        # Initialize the lib3mf wrapper and create a new 3MF model object.
        # This model will be our container for all the parts and colors.
        wrapper = get_wrapper()
        model = wrapper.CreateModel()

        # Define the colors we'll be using as a "Base Material Group".
        # This creates a palette inside the 3MF file that can be referenced by objects.
        base_material_group = model.AddBaseMaterialGroup()
        for color_name, color in material_colors.items():
            lib3mf_color = wrapper.RGBAToColor(*color)
            base_material_group.AddMaterial(color_name, lib3mf_color)

        # Process each color-separated trimesh object.
        for i, mesh in enumerate(new_meshes):
            color_name = mesh.metadata['color_name']
            
            # CRITICAL STEP: Clean the mesh geometry.
            # The lib3mf library is very strict and will fail on "degenerate faces"
            # (i.e., triangles with a repeated vertex, like [100, 200, 100]).
            # This helper function manually filters them out.
            clean_faces = remove_degenerate_faces(mesh.faces)
            
            # Create a new, empty mesh object within the 3MF model's resources.
            mesh_object = model.AddMeshObject()
            mesh_object.SetName(f"{output_path.stem}_{color_name}")
            
            # Assign a color from our Base Material Group to this entire object.
            # The PropertyID corresponds to the material's 1-based index in the group.
            mesh_object.SetObjectLevelProperty(base_material_group.GetResourceID(), i + 1)
            
            # The lib3mf API requires adding geometry piece by piece.
            # We add all the vertices first, then the cleaned faces.
            vertices = [lib3mf.Position(Coordinates=tuple(v)) for v in mesh.vertices]
            for v in vertices:
                mesh_object.AddVertex(v)

            triangles = [lib3mf.Triangle(Indices=tuple(f)) for f in clean_faces]
            for t in triangles:
                mesh_object.AddTriangle(t)
            
            # Add the completed mesh object to the final "Build Scene".
            # This tells the slicer to place this part on the build plate.
            model.AddBuildItem(mesh_object, wrapper.GetIdentityTransform())
            print(f"   ✓ Added {color_name} part to 3MF scene.")

        # Write the complete model structure to a .3mf file.
        writer = model.QueryWriter("3mf")
        writer.WriteToFile(str(output_path))
        
        print(f"   ✓ 3MF export complete ({format_time(time.time() - step_start)})")
        
        # Calculate and display total time
        total_time = time.time() - total_start
        print(f"\n✅ Success! Automated 3MF file saved to: {output_path}")
        print(f"⏱️  Total time: {format_time(total_time)}")
        print(f"🎨 Parts: {len(new_meshes)} separate objects in file")
        
        return output_path
    else:
        raise RuntimeError("No meshes were generated. Check color matching and tolerance settings.")


def remove_degenerate_faces(faces):
    """
    Manually filters out faces that have duplicate vertex indices.

    The lib3mf library enforces strict geometry standards and will raise an
    exception if it finds a "degenerate face" (a triangle where two or more
    vertices are the same, e.g., [100, 200, 100]). This function is a
    brute-force way to ensure all faces are valid before exporting.

    Args:
        faces (np.ndarray): A NumPy array of face indices (n, 3).

    Returns:
        np.ndarray: A cleaned NumPy array of face indices.
    """
    new_faces = []
    for face in faces:
        if len(set(face)) == 3:
            new_faces.append(face)
    return np.array(new_faces)


def main():
    parser = argparse.ArgumentParser(
        description="Convert GLB files to a single multi-part 3MF file for Bambu Lab AMS printing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s astronaut_3d.glb automated_astronaut.3mf
  %(prog)s --mode auto --tolerance 20
  %(prog)s input.glb output.3mf --tolerance 25
        """
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        nargs='?',
        default='astronaut_3d.glb',
        help='Path to input GLB file (default: astronaut_3d.glb)'
    )
    
    parser.add_argument(
        'output_file',
        type=str,
        nargs='?',
        default='automated_astronaut.3mf',
        help='Path for the output 3MF file (default: automated_astronaut.3mf)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['hardcoded', 'auto'],
        default='hardcoded',
        help='Color detection mode (default: hardcoded)'
    )
    
    parser.add_argument(
        '--tolerance',
        type=float,
        default=15,
        help='Color matching tolerance (default: 15)'
    )
    
    args = parser.parse_args()
    
    try:
        convert_glb_to_automated_3mf(
            input_file=args.input_file,
            output_file=args.output_file,
            mode=args.mode,
            tolerance=args.tolerance
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
