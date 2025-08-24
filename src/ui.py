# ui.py
# User interface components using Gradio

import gradio as gr
from .config import PASTELS
from .generators import generate_single, generate_batch


def create_ui():
    """Create and return the Gradio interface"""
    
    with gr.Blocks(title="Pastel Eye Colorizer — 単発/一括") as demo:
        gr.Markdown("## Pastel Eye Colorizer｜マスク領域だけパステル化（Basic / Gradient / Aurora）＋一括生成")

        with gr.Tab("単発生成"):
            with gr.Row():
                eye_in = gr.Image(type="pil", label="Eye Texture (RGBA/RGB)")
                mask_in = gr.Image(type="pil", label="Mask (白=適用, 黒=非適用)")

            with gr.Row():
                preset = gr.Dropdown(choices=list(PASTELS.keys()), value="pastel_cyan", label="パレット")
                mode = gr.Radio(choices=["Basic", "Gradient", "Aurora"], value="Basic", label="効果モード")

            with gr.Accordion("調整（必要に応じて）", open=False):
                keep_value = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="明度保持率（元テクスチャをどれだけ残すか）")
                sat_scale = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="彩度スケール（Basic/Aurora）")
                highlight = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="ハイライト量（Gradient）")
                aurora_strength = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="オーロラ色揺らぎ（Aurora）")

            with gr.Accordion("発光マスクを作る（任意）", open=False):
                make_emission = gr.Checkbox(value=False, label="Emissionマスクも出力する")
                ring_inner = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="リング内半径（相対）")
                ring_outer = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="リング外半径（相対）")
                ring_soft = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="リングのぼかし（相対）")

            run_btn = gr.Button("生成する")
            out_img = gr.Image(type="pil", label="出力テクスチャ（PNG）")
            emi_img = gr.Image(type="pil", label="Emissionマスク（任意）")

            run_btn.click(
                fn=generate_single,
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
                outputs=[out_img, emi_img],
            )

        with gr.Tab("一括生成・一覧/ZIP"):
            with gr.Row():
                eye_in_b = gr.Image(type="pil", label="Eye Texture (RGBA/RGB)")
                mask_in_b = gr.Image(type="pil", label="Mask (白=適用, 黒=非適用)")

            colors_group = gr.CheckboxGroup(
                choices=list(PASTELS.keys()),
                value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
                label="一括パレット選択（複数選択可）",
            )
            modes_group = gr.CheckboxGroup(
                choices=["Basic", "Gradient", "Aurora"],
                value=["Gradient"],
                label="一括モード選択（複数選択可）",
            )
            filename_prefix = gr.Textbox(value="eye_color", label="出力ファイル名プレフィックス", placeholder="例: eye_color")

            with gr.Accordion("調整（必要に応じて）", open=False):
                keep_value_b = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="明度保持率（元テクスチャをどれだけ残すか）")
                sat_scale_b = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="彩度スケール（Basic/Aurora）")
                highlight_b = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="ハイライト量（Gradient）")
                aurora_strength_b = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="オーロラ色揺らぎ（Aurora）")

            with gr.Accordion("発光マスクを作る（任意）", open=False):
                make_emission_b = gr.Checkbox(value=False, label="EmissionマスクもZIPに同梱する")
                ring_inner_b = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="リング内半径（相対）")
                ring_outer_b = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="リング外半径（相対）")
                ring_soft_b = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="リングのぼかし（相対）")

            run_batch = gr.Button("一括生成する")
            gallery = gr.Gallery(label="生成一覧", columns=4, height=480, preview=True)
            zip_file = gr.File(label="一括ダウンロード（ZIP）")

            run_batch.click(
                fn=generate_batch,
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
                outputs=[gallery, zip_file],
            )

    return demo