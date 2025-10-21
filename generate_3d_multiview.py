#!/usr/bin/env python3
"""
Hunyuan3D Multi-View Image-to-3D Generation Script
Generate a textured 3D model from multiple view images.

Usage:
    python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png [output_file]
    
Examples:
    python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png
    python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png my_model.glb
"""

import argparse
import sys
import time
from pathlib import Path
from PIL import Image

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline


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


def generate_3d_model_multiview(front_path, back_path, left_path, right_path, output_path=None, model_path='tencent/Hunyuan3D-2mv'):
    """
    Generate a textured 3D model from multiple view images.
    
    Args:
        front_path: Path to front view image
        back_path: Path to back view image
        left_path: Path to left view image
        right_path: Path to right view image
        output_path: Path to output .glb file (optional)
        model_path: HuggingFace model path
    
    Returns:
        Path to the generated .glb file
    """
    # Start total timer
    total_start = time.time()
    
    # Validate all input images
    image_paths = {
        'front': Path(front_path),
        'back': Path(back_path),
        'left': Path(left_path),
        'right': Path(right_path)
    }
    
    for view, path in image_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Input {view} image not found: {path}")
    
    # Generate output filename if not provided
    if output_path is None:
        output_path = image_paths['front'].stem + "_3d_multiview.glb"
    output_path = Path(output_path)
    
    print(f"📷 Input images:")
    for view, path in image_paths.items():
        print(f"   {view}: {path}")
    print(f"💾 Output file: {output_path}")
    print(f"🤖 Model: {model_path}")
    print()
    
    # Load and prepare all view images
    print("⏱️  Loading multi-view images...")
    step_start = time.time()
    images = {}
    for view, path in image_paths.items():
        image = Image.open(path).convert("RGBA")
        images[view] = image
    print(f"   ✓ All images loaded ({format_time(time.time() - step_start)})")
    
    # Remove background if needed for each view
    print("⏱️  Processing images (background removal if needed)...")
    step_start = time.time()
    rembg = BackgroundRemover()
    for view, image in images.items():
        if image.mode == 'RGB':
            images[view] = rembg(image)
    print(f"   ✓ Images processed ({format_time(time.time() - step_start)})")
    
    # Load shape generation pipeline (multi-view model)
    print("⏱️  Loading multi-view shape generation model...")
    step_start = time.time()
    pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        model_path,
        subfolder='hunyuan3d-dit-v2-mv',
        variant='fp16'
    )
    print(f"   ✓ Model loaded ({format_time(time.time() - step_start)})")
    
    # Generate shape from multi-view images
    print("⏱️  Generating 3D shape from multi-view images...")
    step_start = time.time()
    mesh = pipeline_shapegen(
        image=images,
        num_inference_steps=50,
        octree_resolution=380,
        num_chunks=20000,
        output_type='trimesh'
    )[0]
    shape_time = time.time() - step_start
    print(f"   ✓ Shape generated: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces ({format_time(shape_time)})")
    
    # Load texture generation pipeline
    print("⏱️  Loading texture generation model...")
    step_start = time.time()
    pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained(
        'tencent/Hunyuan3D-2', 
        subfolder='hunyuan3d-paint-v2-0'
    )
    print(f"   ✓ Model loaded ({format_time(time.time() - step_start)})")
    
    # Apply texture using front view only
    print("⏱️  Applying texture (using front view)...")
    step_start = time.time()
    mesh = pipeline_texgen(mesh, image=images['front'])
    texture_time = time.time() - step_start
    print(f"   ✓ Texture applied ({format_time(texture_time)})")
    
    # Export to file
    print(f"⏱️  Exporting to {output_path}...")
    step_start = time.time()
    mesh.export(str(output_path))
    print(f"   ✓ Exported ({format_time(time.time() - step_start)})")
    
    # Calculate and display total time
    total_time = time.time() - total_start
    print(f"\n✅ Success! 3D model saved to: {output_path}")
    print(f"⏱️  Total time: {format_time(total_time)}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate textured 3D models from multi-view images using Hunyuan3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --front front.png --back back.png --left left.png --right right.png
  %(prog)s --front front.png --back back.png --left left.png --right right.png custom_output.glb
  %(prog)s --front f.png --back b.png --left l.png --right r.png robot.glb
        """
    )
    
    parser.add_argument(
        '--front',
        type=str,
        required=True,
        help='Path to front view image'
    )
    
    parser.add_argument(
        '--back',
        type=str,
        required=True,
        help='Path to back view image'
    )
    
    parser.add_argument(
        '--left',
        type=str,
        required=True,
        help='Path to left view image'
    )
    
    parser.add_argument(
        '--right',
        type=str,
        required=True,
        help='Path to right view image'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output .glb file (optional, defaults to <front>_3d_multiview.glb)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='tencent/Hunyuan3D-2mv',
        help='Model to use (default: tencent/Hunyuan3D-2mv)'
    )
    
    args = parser.parse_args()
    
    try:
        generate_3d_model_multiview(
            front_path=args.front,
            back_path=args.back,
            left_path=args.left,
            right_path=args.right,
            output_path=args.output,
            model_path=args.model
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
