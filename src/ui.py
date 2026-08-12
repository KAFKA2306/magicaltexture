import gradio as gr

from .config import PASTELS, PRETTY
from .generators import generate_batch, generate_single


def create_ui():
    """Create and return the Gradio interface."""
    color_choices = [(PRETTY[key], key) for key in PASTELS]
    with gr.Blocks(title="Pastel Eye Colorizer — 単発/一括") as demo:
        gr.Markdown("# Pastel Eye Colorizer\n瞳テクスチャをパステルカラーへ変換します。")
        with gr.Tab("🎯 Single Generation"):
            with gr.Row():
                eye_in = gr.Image(type="pil", label="📸 Eye Texture (RGBA/RGB)")
                mask_in = gr.Image(type="pil", label="🎭 Color Mask (White=Apply, Black=Ignore)")
            with gr.Row():
                preset = gr.Dropdown(choices=color_choices, value="pastel_cyan", label="🎨 Color Palette")
                mode = gr.Radio(choices=["Basic", "Gradient", "Aurora"], value="Gradient", label="🎭 Effect Mode")
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                keep_value = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="💡 Original Brightness")
                sat_scale = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="🌈 Color Intensity")
                highlight = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="✨ Highlight Strength")
                aurora_strength = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="🌌 Aurora Shimmer")
            with gr.Accordion("💫 Emission Mask (For 3D/Glow Effects)", open=False):
                make_emission = gr.Checkbox(value=False, label="Generate emission mask")
                ring_inner = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="Inner Ring Radius")
                ring_outer = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="Outer Ring Radius")
                ring_soft = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="Ring Softness")
            run_btn = gr.Button("🚀 Generate My Eye Color!", variant="primary", size="lg")
            with gr.Row():
                out_img = gr.Image(type="pil", label="✨ Generated Eye Texture")
                emi_img = gr.Image(type="pil", label="💫 Emission Mask (Optional)")
            run_btn.click(
                fn=generate_single,
                inputs=[eye_in, mask_in, preset, mode, keep_value, sat_scale, highlight, aurora_strength,
                        make_emission, ring_inner, ring_outer, ring_soft],
                outputs=[out_img, emi_img],
            )
        with gr.Tab("📦 Batch Generation"):
            with gr.Row():
                eye_in_b = gr.Image(type="pil", label="📸 Eye Texture (RGBA/RGB)")
                mask_in_b = gr.Image(type="pil", label="🎭 Color Mask (White=Apply, Black=Ignore)")
            colors_group = gr.CheckboxGroup(
                choices=color_choices,
                value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
                label="🌈 Batch Color Selection (Multiple)",
            )
            modes_group = gr.CheckboxGroup(
                choices=["Basic", "Gradient", "Aurora"], value=["Gradient"], label="🎭 Batch Effect Selection"
            )
            filename_prefix = gr.Textbox(value="eye_color", label="📁 Output Filename Prefix")
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                keep_value_b = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="💡 Original Brightness")
                sat_scale_b = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="🌈 Color Intensity")
                highlight_b = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="✨ Highlight Strength")
                aurora_strength_b = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="🌌 Aurora Shimmer")
            with gr.Accordion("💫 Emission Masks (For 3D/Glow Effects)", open=False):
                make_emission_b = gr.Checkbox(value=False, label="Include emission masks in ZIP")
                ring_inner_b = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="Inner Ring Radius")
                ring_outer_b = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="Outer Ring Radius")
                ring_soft_b = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="Ring Softness")
            run_batch = gr.Button("🚀 Generate Batch Colors!", variant="primary", size="lg")
            gallery = gr.Gallery(label="🎨 Generated Variations", columns=4, height=480, preview=True)
            zip_file = gr.File(label="📦 Download ZIP Archive")
            run_batch.click(
                fn=generate_batch,
                inputs=[eye_in_b, mask_in_b, colors_group, modes_group, filename_prefix, keep_value_b,
                        sat_scale_b, highlight_b, aurora_strength_b, make_emission_b, ring_inner_b,
                        ring_outer_b, ring_soft_b],
                outputs=[gallery, zip_file],
            )
    return demo
