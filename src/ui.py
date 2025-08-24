# ui.py
# User interface components and layout for Magical Texture

import gradio as gr
from .config import (
    PASTELS, COLOR_DESCRIPTIONS, EFFECT_DESCRIPTIONS,
    DEFAULT_KEEP_VALUE, DEFAULT_SAT_SCALE, DEFAULT_HIGHLIGHT, DEFAULT_AURORA_STRENGTH,
    DEFAULT_RING_INNER, DEFAULT_RING_OUTER, DEFAULT_RING_SOFT,
    GALLERY_COLUMNS, GALLERY_HEIGHT, DEFAULT_PREFIX
)
from .generators import generate_single, generate_batch


def format_color_choice(key):
    """Format color choice for dropdown display"""
    return COLOR_DESCRIPTIONS[key]


def create_ui():
    """Create and return the complete Gradio interface"""
    
    with gr.Blocks(title="Magical Texture - Eye Color Generator", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎨 Magical Texture - Eye Color Generator
        
        Transform your eye textures with beautiful pastel colors! Upload your eye image and mask, 
        then choose from 9 stunning color palettes and 3 artistic effects.
        
        **Perfect for:** Avatar creators, game developers, VTubers, and digital artists
        """)

        with gr.Tab("🎯 Single Generation"):
            gr.Markdown("""
            ### How to use:
            1. **Upload your eye texture** - The main image you want to colorize
            2. **Upload a mask** - White areas will be colored, black areas stay unchanged
            3. **Choose a color and effect** - Pick your favorite combination
            4. **Generate!** - Your new eye texture will appear below
            """)
            
            with gr.Row():
                eye_in = gr.Image(
                    type="pil", 
                    label="🖼️ Eye Texture",
                    info="Upload your eye image (PNG/JPG with or without transparency)"
                )
                mask_in = gr.Image(
                    type="pil", 
                    label="🎭 Color Mask", 
                    info="White areas = will be colored, Black areas = stay original"
                )

            with gr.Row():
                preset = gr.Dropdown(
                    choices=[(format_color_choice(k), k) for k in PASTELS.keys()], 
                    value="pastel_cyan", 
                    label="🎨 Color Palette",
                    info="Choose your favorite pastel color - each has its own magical charm!"
                )
                mode = gr.Radio(
                    choices=[("Basic - " + EFFECT_DESCRIPTIONS["Basic"], "Basic"),
                            ("Gradient - " + EFFECT_DESCRIPTIONS["Gradient"], "Gradient"),
                            ("Aurora - " + EFFECT_DESCRIPTIONS["Aurora"], "Aurora")], 
                    value="Gradient", 
                    label="✨ Effect Style",
                    info="Select the artistic style for your color transformation"
                )

            with gr.Accordion("⚙️ Advanced Settings (Optional - Default values work great!)", open=False):
                gr.Markdown("**Fine-tune the effect intensity - only adjust if you want a different look**")
                keep_value = gr.Slider(
                    0.0, 1.0, value=DEFAULT_KEEP_VALUE, step=0.05, 
                    label="💡 Original Brightness",
                    info="How much of the original texture brightness to keep (0.7 = 70% original)"
                )
                sat_scale = gr.Slider(
                    0.5, 2.0, value=DEFAULT_SAT_SCALE, step=0.05, 
                    label="🌈 Color Intensity (Basic/Aurora)",
                    info="Make colors more vivid (>1.0) or more subtle (<1.0)"
                )
                highlight = gr.Slider(
                    0.0, 1.0, value=DEFAULT_HIGHLIGHT, step=0.05, 
                    label="✨ Highlight Strength (Gradient)",
                    info="Add bright highlights to the upper area for extra sparkle"
                )
                aurora_strength = gr.Slider(
                    0.0, 0.6, value=DEFAULT_AURORA_STRENGTH, step=0.02, 
                    label="🌟 Magic Shimmer (Aurora)",
                    info="Control how much the colors dance and shimmer"
                )

            with gr.Accordion("💫 Glow Effect (Optional - For 3D engines that support emission)", open=False):
                gr.Markdown("**Create a separate glow mask for realistic light emission in 3D applications**")
                make_emission = gr.Checkbox(
                    value=False, 
                    label="🔥 Generate Glow Mask",
                    info="Creates a ring-shaped glow effect around the pupil area"
                )
                ring_inner = gr.Slider(
                    0.02, 0.30, value=DEFAULT_RING_INNER, step=0.01, 
                    label="Inner Ring Size",
                    info="How close to the center the glow starts"
                )
                ring_outer = gr.Slider(
                    0.05, 0.50, value=DEFAULT_RING_OUTER, step=0.01, 
                    label="Outer Ring Size",
                    info="How far from center the glow extends"
                )
                ring_soft = gr.Slider(
                    0.01, 0.30, value=DEFAULT_RING_SOFT, step=0.01, 
                    label="Glow Softness",
                    info="How smooth the glow edge appears"
                )

            run_btn = gr.Button("🚀 Generate My Eye Color!", variant="primary", size="lg")
            
            gr.Markdown("### 🎉 Your Results:")
            with gr.Row():
                out_img = gr.Image(
                    type="pil", 
                    label="🖼️ Colored Eye Texture",
                    info="Right-click to save this image"
                )
                emi_img = gr.Image(
                    type="pil", 
                    label="💫 Glow Mask (if enabled)",
                    info="Use this in your 3D software's emission channel"
                )

            run_btn.click(
                fn=generate_single,
                inputs=[
                    eye_in, mask_in, preset, mode, keep_value, sat_scale, 
                    highlight, aurora_strength, make_emission, ring_inner, ring_outer, ring_soft
                ],
                outputs=[out_img, emi_img],
            )

        with gr.Tab("🎨 Batch Generation & Gallery"):
            gr.Markdown("""
            ### Create Multiple Variations at Once!
            
            Generate many different color and effect combinations in one go. Perfect for:
            - Trying out different looks quickly
            - Creating color variants for characters
            - Building a library of eye textures
            
            **You'll get:** A gallery preview + ZIP file with all variations for download
            """)
            
            with gr.Row():
                eye_in_b = gr.Image(
                    type="pil", 
                    label="🖼️ Eye Texture",
                    info="Upload your eye image (same as single mode)"
                )
                mask_in_b = gr.Image(
                    type="pil", 
                    label="🎭 Color Mask",
                    info="White areas will be colored in all variations"
                )

            with gr.Row():
                colors_group = gr.CheckboxGroup(
                    choices=[(format_color_choice(k), k) for k in PASTELS.keys()],
                    value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
                    label="🎨 Colors to Generate",
                    info="Select multiple colors - each will be generated with your chosen effects"
                )
                modes_group = gr.CheckboxGroup(
                    choices=[("Basic - " + EFFECT_DESCRIPTIONS["Basic"], "Basic"),
                            ("Gradient - " + EFFECT_DESCRIPTIONS["Gradient"], "Gradient"),
                            ("Aurora - " + EFFECT_DESCRIPTIONS["Aurora"], "Aurora")],
                    value=["Gradient"],
                    label="✨ Effects to Apply",
                    info="Choose which artistic effects to create for each color"
                )
            
            filename_prefix = gr.Textbox(
                value=DEFAULT_PREFIX, 
                label="📁 File Name Prefix",
                placeholder="e.g., character_eyes, avatar_v1",
                info="This will be added to the beginning of each generated file name"
            )

            with gr.Accordion("⚙️ Batch Settings (Optional - Uses same settings for all generations)", open=False):
                keep_value_b = gr.Slider(
                    0.0, 1.0, value=DEFAULT_KEEP_VALUE, step=0.05, 
                    label="💡 Original Brightness",
                    info="Applied to all generations"
                )
                sat_scale_b = gr.Slider(
                    0.5, 2.0, value=DEFAULT_SAT_SCALE, step=0.05, 
                    label="🌈 Color Intensity",
                    info="Applied to Basic and Aurora effects"
                )
                highlight_b = gr.Slider(
                    0.0, 1.0, value=DEFAULT_HIGHLIGHT, step=0.05, 
                    label="✨ Highlight Strength",
                    info="Applied to Gradient effects"
                )
                aurora_strength_b = gr.Slider(
                    0.0, 0.6, value=DEFAULT_AURORA_STRENGTH, step=0.02, 
                    label="🌟 Magic Shimmer",
                    info="Applied to Aurora effects"
                )

            with gr.Accordion("💫 Glow Effect for Batch (Optional)", open=False):
                make_emission_b = gr.Checkbox(
                    value=False, 
                    label="🔥 Include Glow Mask in ZIP",
                    info="Adds one emission mask file that works with all color variations"
                )
                ring_inner_b = gr.Slider(0.02, 0.30, value=DEFAULT_RING_INNER, step=0.01, label="Inner Ring Size")
                ring_outer_b = gr.Slider(0.05, 0.50, value=DEFAULT_RING_OUTER, step=0.01, label="Outer Ring Size")
                ring_soft_b = gr.Slider(0.01, 0.30, value=DEFAULT_RING_SOFT, step=0.01, label="Glow Softness")

            run_batch = gr.Button("🎨 Generate All Combinations!", variant="primary", size="lg")
            
            gr.Markdown("### 🖼️ Your Gallery:")
            gallery = gr.Gallery(
                label="Generated Variations", 
                columns=GALLERY_COLUMNS, 
                height=GALLERY_HEIGHT, 
                preview=True,
                info="Click on any image to view it larger. All images are also saved in the ZIP file below."
            )
            
            gr.Markdown("### 📦 Download Everything:")
            zip_file = gr.File(
                label="ZIP Download", 
                info="Contains all generated images with descriptive filenames. Perfect for organizing your texture library!"
            )

            run_batch.click(
                fn=generate_batch,
                inputs=[
                    eye_in_b, mask_in_b, colors_group, modes_group, filename_prefix,
                    keep_value_b, sat_scale_b, highlight_b, aurora_strength_b,
                    make_emission_b, ring_inner_b, ring_outer_b, ring_soft_b
                ],
                outputs=[gallery, zip_file],
            )
    
    return demo