#!/usr/bin/env python3
"""
Hunyuan3D Image-to-3D Generation Script
Generate a textured 3D model from an input image.

Usage:
    python generate_3d.py <input_image> [output_file]
    
Examples:
    python generate_3d.py my_image.png
    python generate_3d.py my_image.png output.glb
    python generate_3d.py assets/example_images/004.png my_model.glb
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


def generate_3d_model(image_path, output_path=None, model_path='tencent/Hunyuan3D-2'):
    """
    Generate a textured 3D model from an input image.
    
    Args:
        image_path: Path to input image
        output_path: Path to output .glb file (optional)
        model_path: HuggingFace model path
    
    Returns:
        Path to the generated .glb file
    """
    # Start total timer
    total_start = time.time()
    
    # Validate input image
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")
    
    # Generate output filename if not provided
    if output_path is None:
        output_path = image_path.stem + "_3d.glb"
    output_path = Path(output_path)
    
    print(f"📷 Input image: {image_path}")
    print(f"💾 Output file: {output_path}")
    print(f"🤖 Model: {model_path}")
    print()
    
    # Load and prepare image
    print("⏱️  Loading image...")
    step_start = time.time()
    image = Image.open(image_path).convert("RGBA")
    print(f"   ✓ Image loaded ({format_time(time.time() - step_start)})")
    
    # Remove background if needed
    if image.mode == 'RGB':
        print("⏱️  Removing background...")
        step_start = time.time()
        rembg = BackgroundRemover()
        image = rembg(image)
        print(f"   ✓ Background removed ({format_time(time.time() - step_start)})")
    
    # Load shape generation pipeline
    print("⏱️  Loading shape generation model...")
    step_start = time.time()
    pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
    print(f"   ✓ Model loaded ({format_time(time.time() - step_start)})")
    
    # Generate shape
    print("⏱️  Generating 3D shape...")
    step_start = time.time()
    mesh = pipeline_shapegen(image=image)[0]
    shape_time = time.time() - step_start
    print(f"   ✓ Shape generated: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces ({format_time(shape_time)})")
    
    # Load texture generation pipeline
    print("⏱️  Loading texture generation model...")
    step_start = time.time()
    pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained(model_path)
    print(f"   ✓ Model loaded ({format_time(time.time() - step_start)})")
    
    # Apply texture
    print("⏱️  Applying texture...")
    step_start = time.time()
    mesh = pipeline_texgen(mesh, image=image)
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
        description="Generate textured 3D models from images using Hunyuan3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s my_image.png
  %(prog)s my_image.png custom_output.glb
  %(prog)s assets/example_images/004.png robot.glb
  %(prog)s photo.jpg --model tencent/Hunyuan3D-2mini
        """
    )
    
    parser.add_argument(
        'input_image',
        type=str,
        help='Path to input image (PNG, JPG, etc.)'
    )
    
    parser.add_argument(
        'output_file',
        type=str,
        nargs='?',
        default=None,
        help='Path to output .glb file (optional, defaults to <input>_3d.glb)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='tencent/Hunyuan3D-2',
        help='Model to use (default: tencent/Hunyuan3D-2). Options: tencent/Hunyuan3D-2, tencent/Hunyuan3D-2mini, tencent/Hunyuan3D-2mv'
    )
    
    args = parser.parse_args()
    
    try:
        generate_3d_model(
            image_path=args.input_image,
            output_path=args.output_file,
            model_path=args.model
        )
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

