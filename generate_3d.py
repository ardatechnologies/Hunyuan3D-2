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
from pathlib import Path
from PIL import Image

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline


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
    print("Loading image...")
    image = Image.open(image_path).convert("RGBA")
    
    # Remove background if needed
    if image.mode == 'RGB':
        print("Removing background...")
        rembg = BackgroundRemover()
        image = rembg(image)
    
    # Load shape generation pipeline
    print("Loading shape generation model...")
    pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
    
    # Generate shape
    print("Generating 3D shape...")
    mesh = pipeline_shapegen(image=image)[0]
    print(f"✓ Shape generated: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    
    # Load texture generation pipeline
    print("Loading texture generation model...")
    pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained(model_path)
    
    # Apply texture
    print("Applying texture...")
    mesh = pipeline_texgen(mesh, image=image)
    
    # Export to file
    print(f"Exporting to {output_path}...")
    mesh.export(str(output_path))
    
    print(f"\n✅ Success! 3D model saved to: {output_path}")
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

