# Hunyuan3D Scripts Guide

This document describes the key scripts available for 3D model generation.

## 🚀 TL;DR - Quick Start

**For Multi-View 3D Generation:**
```bash
conda activate hunyuan
python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png --output model.glb
```

**For Single Image 3D Generation:**
```bash
conda activate hunyuan
python generate_3d.py image.png output.glb
```

**Key Points:**
- Multi-view gives better accuracy than single image
- Use 4 orthogonal views: front, back, left, right
- Processing takes ~20-30 minutes (multi-view) or ~5-15 minutes (single)
- Output is a textured GLB file ready for use

## 🎯 3D Generation Scripts

### 1. `generate_3d.py` - Single Image to 3D

**Purpose**: Generate textured 3D models from a single image

**Usage**:
```bash
python generate_3d.py <input_image> [output_file] [--model MODEL]
```

**Examples**:
```bash
# Basic usage (output defaults to <input>_3d.glb)
python generate_3d.py assets/example_images/astronaut.png

# With custom output filename
python generate_3d.py photo.jpg my_model.glb

# Using a different model
python generate_3d.py image.png output.glb --model tencent/Hunyuan3D-2mini
```

**Model Options**:
- `tencent/Hunyuan3D-2` (default) - Full model, best quality
- `tencent/Hunyuan3D-2mini` - Smaller/faster model

---

### 2. `generate_3d_multiview.py` - Multi-View to 3D

**Purpose**: Generate 3D models from 4 orthogonal view images for better accuracy

**Usage**:
```bash
python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png [--output output.glb] [--model MODEL]
```

**Required Arguments**:
- `--front` - Front view image
- `--back` - Back view image
- `--left` - Left view image
- `--right` - Right view image

**Optional Arguments**:
- `--output` - Output filename (default: `<front>_3d_multiview.glb`)
- `--model` - Model path (default: `tencent/Hunyuan3D-2mv`)

**Example**:
```bash
python generate_3d_multiview.py \
  --front assets/arda_images/duck_4views/duck_front.png \
  --back assets/arda_images/duck_4views/duck_back.png \
  --left assets/arda_images/duck_4views/duck_left.png \
  --right assets/arda_images/duck_4views/duck_right.png \
  --output duck_3d.glb
```

---

### 3. `convert_glb_to_stl.py` - GLB to STL Converter

**Purpose**: Convert GLB files to STL format with optional mesh optimization for 3D printing

**Usage**:
```bash
python convert_glb_to_stl.py <input_glb> [output_stl] [--simplify FACTOR]
```

**Examples**:
```bash
# Basic conversion (creates both standard and simplified versions)
python convert_glb_to_stl.py duck_3d.glb

# With custom output name
python convert_glb_to_stl.py duck_3d.glb my_model.stl

# With custom simplification factor (0.0-1.0, lower = more simplified)
python convert_glb_to_stl.py duck_3d.glb --simplify 0.3
```

**Features**:
- Creates both standard and simplified STL versions
- Automatic mesh optimization for 3D printing
- Face reduction, normal fixing, and cleanup
- Detailed statistics on mesh reduction

**Output**: Two STL files - standard and simplified versions

---

## 🔄 Multi-Step Generation Process

Both scripts follow a similar multi-step pipeline from image(s) to final GLB file:

### Step 1: Image Loading & Preprocessing
- **Load images**: Convert to RGBA format
- **Background removal**: Automatically applied if images are RGB
- **Image validation**: Ensure all required views are present

### Step 2: Shape Generation
- **Model loading**: Download and load the appropriate Hunyuan3D model
- **Diffusion sampling**: Generate 3D geometry using diffusion process
  - Single-view: 50 inference steps
  - Multi-view: 50 inference steps with 4 views
- **Volume decoding**: Convert latent representation to 3D mesh
- **Initial mesh**: High-resolution mesh with ~500K+ vertices

### Step 3: Mesh Optimization & Decimation
- **Face reduction**: Automatically reduce mesh complexity
  - Target: ~40,000 faces (down from 500K+)
  - Method: Quadric edge collapse decimation
  - Preserves topology and boundaries
- **Floater removal**: Remove disconnected mesh components
- **Degenerate face removal**: Clean up invalid geometry

### Step 4: Texture Generation
- **UV mapping**: Generate UV coordinates for texture application
- **Multi-view rendering**: Render mesh from multiple camera angles
- **Texture synthesis**: Generate high-resolution texture maps
- **Texture baking**: Apply textures to the optimized mesh

### Step 5: Export
- **GLB export**: Save as GLB format with embedded textures
- **File optimization**: Compress and optimize for file size

---

## 📋 Script Comparison

| Script | Input | Output | Processing Time | Use Case |
|--------|-------|--------|----------------|----------|
| `generate_3d.py` | 1 image | GLB | ~5-15 minutes | Quick generation from photos |
| `generate_3d_multiview.py` | 4 images | GLB | ~20-30 minutes | Accurate multi-view reconstruction |
| `convert_glb_to_stl.py` | GLB | STL | ~1-2 minutes | 3D printing preparation |

---

## 🚀 For UI Integration

### Environment Setup
```bash
conda activate hunyuan
```

### Key Workflow

1. **Single Image Pipeline**:
   ```
   User uploads image → generate_3d.py → GLB file → Download
   ```

2. **Multi-View Pipeline**:
   ```
   User uploads 4 views → generate_3d_multiview.py → GLB file → Download
   ```

3. **3D Printing Pipeline**:
   ```
   GLB file → convert_glb_to_stl.py → STL files (standard + simplified) → 3D Printing
   ```

### API Integration Considerations

**For generate_3d.py**:
- Input: Single image file
- Parameters: model selection (optional)
- Processing time: ~5-15 minutes
- Output: GLB file path

**For generate_3d_multiview.py**:
- Input: 4 image files (front, back, left, right)
- Parameters: model selection (optional)
- Processing time: ~20-30 minutes
- Output: GLB file path

**For convert_glb_to_stl.py**:
- Input: GLB file
- Parameters: simplification factor (optional)
- Processing time: ~1-2 minutes
- Output: Two STL files (standard + simplified)

**Error Handling**:
- All scripts provide detailed progress output
- Check for missing dependencies (conda environment)
- Validate input images exist before processing

---

## 📝 Notes

- All generation scripts include timing information
- Models are automatically downloaded on first use
- Background removal is applied automatically if needed
- Generated GLB files include both geometry and texture
- Multi-view generation provides better accuracy but takes longer
- Automatic mesh decimation reduces file size while maintaining quality

---

## 🐛 Troubleshooting

**Module not found errors**: Make sure conda environment is activated:
```bash
conda activate hunyuan
```

**Out of memory**: Try using the mini model:
```bash
python generate_3d.py image.png output.glb --model tencent/Hunyuan3D-2mini
```

**Long processing times**: This is normal - the pipeline includes multiple AI models and mesh processing steps
