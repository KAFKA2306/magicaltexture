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

This is a Pastel Eye Colorizer application built with Gradio for web UI and NumPy/Pillow for image processing. The architecture is modular and well-organized for maintainability and scalability.

### Core Components

**Main Application Entry (`app.py`)**
- Entry point that imports and runs the modular application from `src/`
- Fallback handling if modular structure is not available

**Modular Structure (`src/` directory)**
- `main.py`: Application entry point and launcher
- `ui.py`: Gradio user interface components and layout
- `core.py`: Core image processing algorithms (HSV conversion, transformations)
- `config.py`: Color presets and configuration constants
- `generators.py`: Single and batch generation functions
- `__init__.py`: Package initialization

**Key Features**
- 9 pastel color presets defined in HSV space (including deep blue)
- Three color transformation modes: Basic, Gradient, Aurora
- Batch processing with gallery display and ZIP downloads
- Optional emission mask generation for glow effects

**Data Flow**
1. User uploads eye texture (RGB/RGBA) and mask image via Gradio UI
2. Images processed through modular pipeline: conversion → transformation → output
3. Single or batch processing generates results with organized file naming
4. Results displayed in gallery with ZIP download option

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

## File Structure

```
├── app.py                 # Main entry point with fallback handling
├── src/                   # Modular application code
│   ├── __init__.py       # Package initialization  
│   ├── main.py           # Application launcher
│   ├── ui.py             # Gradio interface components
│   ├── core.py           # Image processing algorithms
│   ├── config.py         # Color presets and constants
│   └── generators.py     # Generation functions
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── docs/                 # Technical documentation
├── mkdocs.yml            # Documentation site config
└── .github/workflows/    # CI/CD pipeline

```

## Deployment

The application is configured for Hugging Face Spaces deployment with metadata in README.md frontmatter. The modular structure is automatically uploaded and runs seamlessly on both local and Spaces environments.

CI/CD pipeline handles:
- Linting of both `app.py` and `src/` modules
- Smoke testing of modular imports
- Automatic deployment to Hugging Face Spaces including the `src/` directory