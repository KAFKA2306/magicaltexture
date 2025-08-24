# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python app.py
```
The application runs locally with Gradio and is also deployed to Hugging Face Spaces at https://k4fka-magicaltexture.hf.space

### Testing and Linting
```bash
# Code formatting
black app.py src/

# Linting
ruff app.py src/

# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

This is a Pastel Eye Colorizer application built with Gradio for web UI and NumPy/Pillow for image processing. The architecture is intentionally simple and monolithic for performance and maintainability.

### Core Components

**Main Application (`app.py`)**
- Gradio-based web interface for uploading eye textures and masks
- Three color transformation modes: Basic, Gradient, Aurora
- 8 pastel color presets defined in HSV space
- Optional emission mask generation for glow effects

**Image Processing Pipeline**
- `load_rgba()` and `load_mask()`: Convert PIL images to NumPy arrays
- `rgb_to_hsv_np()` and `hsv_to_rgb_np()`: Custom vectorized color space conversion
- `apply_basic()`, `apply_gradient()`, `apply_aurora()`: Three transformation modes
- `build_emission()`: Generate ring-shaped emission masks for lighting effects

**Data Flow**
1. User uploads eye texture (RGB/RGBA) and mask image
2. Images converted to NumPy arrays, mask resized and binarized
3. Color transformation applied only to masked regions
4. Results converted back to PIL Images for display/download

### Key Design Patterns

- **Vectorized Operations**: All processing uses NumPy broadcasting, no pixel-level loops
- **HSV Color Space**: Transformations work in HSV for intuitive hue/saturation control
- **Mask-Based Processing**: Only pixels where mask > 32 are transformed
- **Stateless Processing**: No persistent state, each request is independent

### Color Transformation Modes

- **Basic**: Simple hue replacement with saturation/brightness blending
- **Gradient**: Distance-based color variation from mask centroid + highlight effects
- **Aurora**: Sine wave-based hue oscillation for organic color variation

### Parameters and Ranges

- `keep_value`: How much original brightness to preserve (0.0-1.0, default 0.7)
- `sat_scale`: Saturation multiplier (0.5-2.0, default 1.0)
- `highlight`: Top highlight strength for Gradient mode (0.0-1.0, default 0.4)
- `aurora_strength`: Hue variation intensity for Aurora mode (0.0-0.6, default 0.3)

## Deployment

The application is configured for Hugging Face Spaces deployment with metadata in README.md frontmatter. The same code runs locally and on Spaces without modification.