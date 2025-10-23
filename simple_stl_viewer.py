#!/usr/bin/env python3
"""
Simple STL Viewer
Quick visualization of STL files using matplotlib and trimesh.

Usage:
    python simple_stl_viewer.py <stl_file>
    
Examples:
    python simple_stl_viewer.py duck_3d.stl
    python simple_stl_viewer.py duck_3d_simplified.stl
"""

import argparse
import sys
from pathlib import Path

import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


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
        'bounds': mesh.bounds,
        'file_size': Path(mesh.metadata.get('file_path', '')).stat().st_size if hasattr(mesh, 'metadata') and mesh.metadata.get('file_path') else 0
    }


def print_mesh_info(mesh, file_path):
    """Print mesh information."""
    stats = get_mesh_stats(mesh)
    file_size = Path(file_path).stat().st_size
    
    print(f"📁 File: {file_path}")
    print(f"📊 Size: {format_size(file_size)}")
    print(f"🔢 Vertices: {stats['vertices']:,}")
    print(f"🔺 Faces: {stats['faces']:,}")
    if stats['volume'] > 0:
        print(f"📦 Volume: {stats['volume']:.6f} cubic units")
    bounds = stats['bounds']
    print(f"📏 Bounds: {bounds[0]} to {bounds[1]}")
    print()


def view_stl_simple(stl_file):
    """
    Simple STL viewer using trimesh's built-in viewer.
    
    Args:
        stl_file: Path to STL file
    """
    # Validate input file
    stl_path = Path(stl_file)
    if not stl_path.exists():
        raise FileNotFoundError(f"STL file not found: {stl_path}")
    
    if not stl_path.suffix.lower() == '.stl':
        raise ValueError(f"File must be an STL file: {stl_path}")
    
    print("⏱️  Loading STL file...")
    try:
        mesh = trimesh.load(str(stl_path))
        print("   ✓ STL loaded successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to load STL file: {e}")
    
    # Print mesh information
    print_mesh_info(mesh, stl_path)
    
    # Show the mesh using trimesh's built-in viewer
    print("🖼️  Opening 3D viewer...")
    print("   💡 Use mouse to rotate, scroll to zoom, right-click to pan")
    print("   💡 Close the viewer window when done")
    
    try:
        mesh.show()
        print("   ✓ Viewer closed")
    except Exception as e:
        print(f"   ⚠️  Viewer error: {e}")
        print("   🔄 Trying alternative visualization...")
        
        # Fallback: create a matplotlib 3D plot
        view_stl_matplotlib(mesh, stl_path)


def view_stl_matplotlib(mesh, file_path):
    """
    Alternative STL viewer using matplotlib.
    
    Args:
        mesh: Trimesh mesh object
        file_path: Path to the STL file
    """
    print("📊 Creating matplotlib visualization...")
    
    # Create figure and 3D axis
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Sample vertices for display (to avoid performance issues with large meshes)
    vertices = mesh.vertices
    faces = mesh.faces
    
    # If mesh is too large, sample it
    max_vertices = 10000
    if len(vertices) > max_vertices:
        print(f"   📉 Sampling mesh ({len(vertices):,} → {max_vertices:,} vertices for display)")
        # Simple random sampling
        indices = np.random.choice(len(vertices), max_vertices, replace=False)
        vertices = vertices[indices]
    
    # Plot the mesh
    ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
               c=vertices[:, 2], cmap='viridis', s=1, alpha=0.6)
    
    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'STL Viewer: {file_path.name}')
    
    # Set equal aspect ratio
    max_range = np.array([vertices[:, 0].max() - vertices[:, 0].min(),
                         vertices[:, 1].max() - vertices[:, 1].min(),
                         vertices[:, 2].max() - vertices[:, 2].min()]).max() / 2.0
    
    mid_x = (vertices[:, 0].max() + vertices[:, 0].min()) * 0.5
    mid_y = (vertices[:, 1].max() + vertices[:, 1].min()) * 0.5
    mid_z = (vertices[:, 2].max() + vertices[:, 2].min()) * 0.5
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    print("   ✓ Matplotlib viewer ready")
    print("   💡 Use mouse to rotate, scroll to zoom")
    print("   💡 Close the window when done")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Simple STL file viewer with 3D visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s duck_3d.stl
  %(prog)s duck_3d_simplified.stl
  %(prog)s assets/1.stl
        """
    )
    
    parser.add_argument(
        'stl_file',
        type=str,
        help='Path to STL file to visualize'
    )
    
    args = parser.parse_args()
    
    try:
        view_stl_simple(args.stl_file)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


