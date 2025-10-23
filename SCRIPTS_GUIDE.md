# Hunyuan3D Scripts Guide

This document describes the key scripts available for 3D model generation and processing.

## 🚀 TL;DR - Quick Start

**For Multi-View 3D Generation:**
```bash
conda activate hunyuan
python generate_3d_multiview.py --front front.png --back back.png --left left.png --right right.png --output model.glb
```

**For 3MF Conversion (3D Printing):**
```bash
python convert_to_3mf.py model.glb model.3mf
```

**Key Points:**
- Multi-view gives better accuracy than single image
- Use 4 orthogonal views: front, back, left, right
- Processing takes ~20-30 minutes
- Convert to 3MF for 3D printing compatibility

## 🎯 Main 3D Generation Scripts

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

**Output**: GLB file with textured 3D mesh

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

**Output**: GLB file with textured 3D mesh generated from multiple views

---

## 🔧 Utility Scripts

### 3. `simple_stl_viewer.py` - 3D Model Viewer

**Purpose**: View and analyze 3D models (STL/GLB files) with statistics

**Usage**:
```bash
python simple_stl_viewer.py <model_file>
```

**Features**:
- Displays vertex count, face count, volume, and bounding box
- Interactive 3D visualization (rotate, zoom, pan)
- Supports STL and GLB formats

**Example**:
```bash
python simple_stl_viewer.py duck_3d.glb
```

**Output**: Console statistics + interactive 3D viewer window

---

### 4. `convert_to_3mf.py` - Format Converter

**Purpose**: Convert GLB/STL files to 3MF format for 3D printing

**Usage**:
```bash
python convert_to_3mf.py <input_file> [output_file]
```

**Example**:
```bash
python convert_to_3mf.py model.glb model.3mf
```

**Output**: 3MF file ready for 3D printing software

---

## 📋 Quick Comparison

| Script | Input Type | Model Used | Best For |
|--------|-----------|------------|----------|
| `generate_3d.py` | 1 image | Hunyuan3D-2 | Quick generation from photos |
| `generate_3d_multiview.py` | 4 images | Hunyuan3D-2mv | Accurate multi-view reconstruction |
| `simple_stl_viewer.py` | 3D file | N/A | Viewing/analyzing models |
| `convert_to_3mf.py` | 3D file | N/A | Preparing for 3D printing |

---

## 🚀 For UI Integration

### Environment Setup
```bash
conda activate hunyuan
```

### Key Workflow

1. **Single Image Pipeline**:
   ```
   User uploads image → generate_3d.py → GLB file → Viewer/Download
   ```

2. **Multi-View Pipeline**:
   ```
   User uploads 4 views → generate_3d_multiview.py → GLB file → Viewer/Download
   ```

3. **Post-Processing**:
   ```
   GLB file → simple_stl_viewer.py (preview) → convert_to_3mf.py (for printing)
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

**Viewer issues**: The viewer will fallback to matplotlib if pyglet is not available
