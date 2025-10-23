#!/usr/bin/env python3
"""
GLB to STL Converter Script
Convert GLB files to STL format with optional mesh optimization for 3D printing.

Usage:
    python convert_glb_to_stl.py <input_glb> [output_stl]
    
Examples:
    python convert_glb_to_stl.py duck_3d.glb
    python convert_glb_to_stl.py duck_3d.glb my_model.stl
    python convert_glb_to_stl.py assets/1.glb
"""

import argparse
import sys
import time
import os
from pathlib import Path

import trimesh


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


def format_size(bytes_size):
    """Format bytes into a human-readable string."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024**2:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024**3:
        return f"{bytes_size / (1024**2):.1f} MB"
    else:
        return f"{bytes_size / (1024**3):.1f} GB"


def get_mesh_stats(mesh):
    """Get mesh statistics."""
    return {
        'vertices': len(mesh.vertices),
        'faces': len(mesh.faces),
        'volume': mesh.volume if hasattr(mesh, 'volume') and mesh.volume is not None else 0,
        'bounds': mesh.bounds
    }


def print_mesh_stats(stats, label="Mesh"):
    """Print mesh statistics."""
    print(f"   {label}: {stats['vertices']:,} vertices, {stats['faces']:,} faces")
    if stats['volume'] > 0:
        print(f"   Volume: {stats['volume']:.6f} cubic units")
    bounds = stats['bounds']
    print(f"   Bounds: {bounds[0]} to {bounds[1]}")


def convert_glb_to_stl(input_glb, output_stl=None, simplify_factor=0.5):
    """
    Convert GLB file to STL format with optional mesh optimization.
    
    Args:
        input_glb: Path to input GLB file
        output_stl: Path to output STL file (optional)
        simplify_factor: Factor for mesh simplification (0.0-1.0, lower = more simplified)
    
    Returns:
        Tuple of (standard_stl_path, simplified_stl_path)
    """
    # Start total timer
    total_start = time.time()
    
    # Validate input file
    input_path = Path(input_glb)
    if not input_path.exists():
        raise FileNotFoundError(f"Input GLB file not found: {input_path}")
    
    if not input_path.suffix.lower() == '.glb':
        raise ValueError(f"Input file must be a GLB file: {input_path}")
    
    # Generate output filenames if not provided
    if output_stl is None:
        output_stl = input_path.stem + ".stl"
    output_path = Path(output_stl)
    
    # Generate simplified output filename
    simplified_output = output_path.parent / f"{output_path.stem}_simplified{output_path.suffix}"
    
    print(f"📁 Input GLB: {input_path}")
    print(f"💾 Standard STL: {output_path}")
    print(f"🔧 Simplified STL: {simplified_output}")
    print()
    
    # Load GLB file
    print("⏱️  Loading GLB file...")
    step_start = time.time()
    try:
        mesh = trimesh.load(str(input_path))
        print(f"   ✓ GLB loaded ({format_time(time.time() - step_start)})")
    except Exception as e:
        raise RuntimeError(f"Failed to load GLB file: {e}")
    
    # Handle scene objects (GLB files can contain multiple meshes)
    if hasattr(mesh, 'geometry'):
        # If it's a scene, combine all meshes
        print("   📦 Combining multiple meshes from scene...")
        combined_mesh = trimesh.util.concatenate([m for m in mesh.geometry.values() if hasattr(m, 'vertices')])
        mesh = combined_mesh
    
    # Get original mesh stats
    original_stats = get_mesh_stats(mesh)
    print_mesh_stats(original_stats, "Original")
    print()
    
    # Standard conversion
    print("⏱️  Converting to standard STL...")
    step_start = time.time()
    try:
        mesh.export(str(output_path), file_type='stl')
        standard_time = time.time() - step_start
        standard_size = output_path.stat().st_size
        print(f"   ✓ Standard STL exported ({format_time(standard_time)}) - {format_size(standard_size)}")
    except Exception as e:
        raise RuntimeError(f"Failed to export standard STL: {e}")
    
    # Simplified conversion
    print("⏱️  Creating simplified version for 3D printing...")
    step_start = time.time()
    try:
        # Create a copy for simplification
        simplified_mesh = mesh.copy()
        
        # Fix normals
        print("   🔧 Fixing mesh normals...")
        simplified_mesh.fix_normals()
        
        # Remove duplicate faces
        print("   🧹 Removing duplicate faces...")
        simplified_mesh.update_faces(simplified_mesh.unique_faces())
        
        # Remove degenerate faces
        print("   🧹 Removing degenerate faces...")
        simplified_mesh.update_faces(simplified_mesh.nondegenerate_faces())
        
        # Simplify mesh
        target_faces = int(len(simplified_mesh.faces) * simplify_factor)
        if target_faces < len(simplified_mesh.faces):
            print(f"   📉 Simplifying mesh ({len(simplified_mesh.faces):,} → {target_faces:,} faces)...")
            try:
                # Try fast simplification first
                simplified_mesh = simplified_mesh.simplify_quadric_decimation(face_count=target_faces)
            except (ImportError, AttributeError):
                # Fallback: use decimation with a different approach
                print("   ⚠️  Fast simplification not available, using basic decimation...")
                try:
                    # Use trimesh's built-in decimation
                    simplified_mesh = trimesh.decimation.decimate(simplified_mesh, face_count=target_faces)
                except:
                    # If all else fails, skip simplification but warn user
                    print("   ⚠️  Mesh simplification not available, exporting original mesh...")
        
        # Final cleanup
        simplified_mesh.remove_unreferenced_vertices()
        
        # Export simplified mesh
        simplified_mesh.export(str(simplified_output), file_type='stl')
        simplified_time = time.time() - step_start
        
        # Get simplified mesh stats
        simplified_stats = get_mesh_stats(simplified_mesh)
        simplified_size = simplified_output.stat().st_size
        
        print(f"   ✓ Simplified STL exported ({format_time(simplified_time)}) - {format_size(simplified_size)}")
        print_mesh_stats(simplified_stats, "Simplified")
        
        # Show reduction statistics
        vertex_reduction = (1 - simplified_stats['vertices'] / original_stats['vertices']) * 100
        face_reduction = (1 - simplified_stats['faces'] / original_stats['faces']) * 100
        size_reduction = (1 - simplified_size / standard_size) * 100
        
        print(f"   📊 Reduction: {vertex_reduction:.1f}% vertices, {face_reduction:.1f}% faces, {size_reduction:.1f}% file size")
        
    except Exception as e:
        raise RuntimeError(f"Failed to create simplified STL: {e}")
    
    # Calculate and display total time
    total_time = time.time() - total_start
    print(f"\n✅ Success! STL files created:")
    print(f"   📄 Standard: {output_path} ({format_size(standard_size)})")
    print(f"   🔧 Simplified: {simplified_output} ({format_size(simplified_size)})")
    print(f"⏱️  Total time: {format_time(total_time)}")
    
    return output_path, simplified_output


def main():
    parser = argparse.ArgumentParser(
        description="Convert GLB files to STL format with optional mesh optimization for 3D printing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s duck_3d.glb
  %(prog)s duck_3d.glb my_model.stl
  %(prog)s assets/1.glb --simplify 0.3
        """
    )
    
    parser.add_argument(
        'input_glb',
        type=str,
        help='Path to input GLB file'
    )
    
    parser.add_argument(
        'output_stl',
        type=str,
        nargs='?',
        default=None,
        help='Path to output STL file (optional, defaults to <input>.stl and <input>_simplified.stl)'
    )
    
    parser.add_argument(
        '--simplify',
        type=float,
        default=0.5,
        help='Simplification factor for 3D printing optimization (0.0-1.0, default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Validate simplify factor
    if not 0.0 <= args.simplify <= 1.0:
        print("❌ Error: Simplify factor must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)
    
    try:
        convert_glb_to_stl(
            input_glb=args.input_glb,
            output_stl=args.output_stl,
            simplify_factor=args.simplify
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
