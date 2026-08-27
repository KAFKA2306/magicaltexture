from urllib.parse import urlencode

import gradio as gr

from .config import PASTELS, PRETTY
from .generators import generate_batch, generate_single


ISSUE_BASE_URL = "https://github.com/KAFKA2306/magicaltexture/issues/new"
SERVICE_GUIDE_URL = "https://github.com/KAFKA2306/magicaltexture/blob/main/docs/business.md"


def _inquiry_url(*, generation_type, modes, palettes, request_type):
    mode_value = ", ".join(modes) if isinstance(modes, list) else str(modes)
    palette_value = ", ".join(palettes) if isinstance(palettes, list) else str(palettes)
    body = "\n".join(
        [
            "## 制作相談",
            "",
            f"- request_type: {request_type}",
            f"- source: huggingface-space",
            f"- generation_type: {generation_type}",
            f"- mode: {mode_value}",
            f"- palette: {palette_value}",
            "",
            "### 対象アバター / 用途",
            "",
            "### 希望する納品物",
            "",
            "### 希望時期（任意）",
            "",
            "### 権利確認",
            "依頼に使用する元テクスチャについて、編集・納品に必要な権利または許諾があることを確認してください。",
        ]
    )
    query = urlencode(
        {
            "title": f"制作相談: {request_type}",
            "body": body,
        }
    )
    return f"{ISSUE_BASE_URL}?{query}"


def _cta_markdown(*, generation_type, modes, palettes):
    avatar_url = _inquiry_url(
        generation_type=generation_type,
        modes=modes,
        palettes=palettes,
        request_type="avatar_customization",
    )
    creator_url = _inquiry_url(
        generation_type=generation_type,
        modes=modes,
        palettes=palettes,
        request_type="creator_color_package",
    )
    return (
        "### 制作者向け制作相談\n"
        "生成結果をベースに、アバター別調整・複数色セット・Emission差分・専用パレットの制作を相談できます。\n\n"
        f"[このアバター向けに制作を相談する]({avatar_url}) · "
        f"[販売アバター用の複数色セットを相談する]({creator_url}) · "
        f"[納品内容・必要素材・権利条件を見る]({SERVICE_GUIDE_URL})"
    )


def _generate_single_with_cta(*args):
    image, emission = generate_single(*args)
    preset = args[2]
    mode = args[3]
    return image, emission, _cta_markdown(
        generation_type="single",
        modes=mode,
        palettes=preset,
    )


def _generate_batch_with_cta(*args):
    gallery, zip_path = generate_batch(*args)
    palettes = args[2]
    modes = args[3]
    return gallery, zip_path, _cta_markdown(
        generation_type="batch",
        modes=modes,
        palettes=palettes,
    )


def create_ui():
    """Create and return the Gradio interface."""
    color_choices = [(PRETTY[key], key) for key in PASTELS]
    with gr.Blocks(title="Pastel Eye Colorizer — 単発/一括") as demo:
        gr.Markdown(
            "# Pastel Eye Colorizer\n瞳テクスチャをパステルカラーへ変換します。"
        )
        with gr.Tab("🎯 Single Generation"):
            with gr.Row():
                eye_in = gr.Image(type="pil", label="📸 Eye Texture (RGBA/RGB)")
                mask_in = gr.Image(
                    type="pil", label="🎭 Color Mask (White=Apply, Black=Ignore)"
                )
            with gr.Row():
                preset = gr.Dropdown(
                    choices=color_choices, value="pastel_cyan", label="🎨 Color Palette"
                )
                mode = gr.Radio(
                    choices=["Basic", "Gradient", "Aurora"],
                    value="Gradient",
                    label="🎭 Effect Mode",
                )
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                keep_value = gr.Slider(
                    0.0, 1.0, value=0.7, step=0.05, label="💡 Original Brightness"
                )
                sat_scale = gr.Slider(
                    0.5, 2.0, value=1.0, step=0.05, label="🌈 Color Intensity"
                )
                highlight = gr.Slider(
                    0.0, 1.0, value=0.4, step=0.05, label="✨ Highlight Strength"
                )
                aurora_strength = gr.Slider(
                    0.0, 0.6, value=0.3, step=0.02, label="🌌 Aurora Shimmer"
                )
            with gr.Accordion("💫 Emission Mask (For 3D/Glow Effects)", open=False):
                make_emission = gr.Checkbox(value=False, label="Generate emission mask")
                ring_inner = gr.Slider(
                    0.02, 0.30, value=0.07, step=0.01, label="Inner Ring Radius"
                )
                ring_outer = gr.Slider(
                    0.05, 0.50, value=0.14, step=0.01, label="Outer Ring Radius"
                )
                ring_soft = gr.Slider(
                    0.01, 0.30, value=0.06, step=0.01, label="Ring Softness"
                )
            run_btn = gr.Button(
                "🚀 Generate My Eye Color!", variant="primary", size="lg"
            )
            with gr.Row():
                out_img = gr.Image(type="pil", label="✨ Generated Eye Texture")
                emi_img = gr.Image(type="pil", label="💫 Emission Mask (Optional)")
            single_cta = gr.Markdown()
            run_btn.click(
                fn=_generate_single_with_cta,
                inputs=[
                    eye_in,
                    mask_in,
                    preset,
                    mode,
                    keep_value,
                    sat_scale,
                    highlight,
                    aurora_strength,
                    make_emission,
                    ring_inner,
                    ring_outer,
                    ring_soft,
                ],
                outputs=[out_img, emi_img, single_cta],
            )
        with gr.Tab("📦 Batch Generation"):
            with gr.Row():
                eye_in_b = gr.Image(type="pil", label="📸 Eye Texture (RGBA/RGB)")
                mask_in_b = gr.Image(
                    type="pil", label="🎭 Color Mask (White=Apply, Black=Ignore)"
                )
            colors_group = gr.CheckboxGroup(
                choices=color_choices,
                value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
                label="🌈 Batch Color Selection (Multiple)",
            )
            modes_group = gr.CheckboxGroup(
                choices=["Basic", "Gradient", "Aurora"],
                value=["Gradient"],
                label="🎭 Batch Effect Selection",
            )
            filename_prefix = gr.Textbox(
                value="eye_color", label="📁 Output Filename Prefix"
            )
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                keep_value_b = gr.Slider(
                    0.0, 1.0, value=0.7, step=0.05, label="💡 Original Brightness"
                )
                sat_scale_b = gr.Slider(
                    0.5, 2.0, value=1.0, step=0.05, label="🌈 Color Intensity"
                )
                highlight_b = gr.Slider(
                    0.0, 1.0, value=0.4, step=0.05, label="✨ Highlight Strength"
                )
                aurora_strength_b = gr.Slider(
                    0.0, 0.6, value=0.3, step=0.02, label="🌌 Aurora Shimmer"
                )
            with gr.Accordion("💫 Emission Masks (For 3D/Glow Effects)", open=False):
                make_emission_b = gr.Checkbox(
                    value=False, label="Include emission masks in ZIP"
                )
                ring_inner_b = gr.Slider(
                    0.02, 0.30, value=0.07, step=0.01, label="Inner Ring Radius"
                )
                ring_outer_b = gr.Slider(
                    0.05, 0.50, value=0.14, step=0.01, label="Outer Ring Radius"
                )
                ring_soft_b = gr.Slider(
                    0.01, 0.30, value=0.06, step=0.01, label="Ring Softness"
                )
            run_batch = gr.Button(
                "🚀 Generate Batch Colors!", variant="primary", size="lg"
            )
            gallery = gr.Gallery(
                label="🎨 Generated Variations", columns=4, height=480, preview=True
            )
            zip_file = gr.File(label="📦 Download ZIP Archive")
            batch_cta = gr.Markdown()
            run_batch.click(
                fn=_generate_batch_with_cta,
                inputs=[
                    eye_in_b,
                    mask_in_b,
                    colors_group,
                    modes_group,
                    filename_prefix,
                    keep_value_b,
                    sat_scale_b,
                    highlight_b,
                    aurora_strength_b,
                    make_emission_b,
                    ring_inner_b,
                    ring_outer_b,
                    ring_soft_b,
                ],
                outputs=[gallery, zip_file, batch_cta],
            )
        with gr.Tab("🧰 Creator Services"):
            gr.Markdown(
                """## VRChatアバター制作者・改変向け制作相談

無料生成で方向性を確認した後、実際のアバターや販売用途に合わせた納品を相談できます。

- アバター別の瞳色・Emission調整
- 販売アバター同梱向けの複数色セット
- ブランドカラーに合わせた専用パレット
- マスク作成を含む個別調整
- lilToon導入時の設定情報を含む納品

**必要素材:** 元テクスチャ、編集範囲が分かる情報、対象アバター/用途。依頼者が編集・納品に必要な権利または許諾を持つ素材のみ対象です。

実商品・販売実績は、公開されているものだけを案内します。現在は制作相談を受け付けます。

[制作内容と権利条件を確認する](https://github.com/KAFKA2306/magicaltexture/blob/main/docs/business.md) · [制作相談を始める](https://github.com/KAFKA2306/magicaltexture/issues/new?title=%E5%88%B6%E4%BD%9C%E7%9B%B8%E8%AB%87&body=%23%23%20%E5%AF%BE%E8%B1%A1%E3%82%A2%E3%83%90%E3%82%BF%E3%83%BC%20%2F%20%E7%94%A8%E9%80%94%0A%0A%23%23%20%E5%B8%8C%E6%9C%9B%E3%81%99%E3%82%8B%E7%B4%8D%E5%93%81%E7%89%A9%0A%0A%23%23%20%E5%B8%8C%E6%9C%9B%E6%99%82%E6%9C%9F%EF%BC%88%E4%BB%BB%E6%84%8F%EF%BC%89%0A)
"""
            )
    return demo
