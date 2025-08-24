# パステル瞳テクスチャ生成アプリを公開しよう

誰でもブラウザから使える「画像アップロード → マスク領域だけパステルカラー化（Basic/Gradient/Aurora）→ ダウンロード」まで完結するWebアプリを提案します。ホスティングは無料枠があるHugging Face Spaces（Gradio）を推奨します。ローカル実行も1コマンドです。

## できること（完成イメージ）
- 画像2枚をアップロード（eye_color.png / eye_mask.png）
- パレットから色選択（pastel cyan・pink・lavender・mint・peach・lemon・coral・sky）
- 効果モード
  - Basic: 色相だけを置換＋明るさは元テクスチャを維持
  - Gradient: 中心→外周へ自然なパステルグラデ
  - Aurora: 波状の色相揺らぎでオーロラ風
- 調整項目: 明度保持率、彩度、強さ、ハイライト量
- 追加出力（任意）: emission用リングマスク
- 出力: 生成画像（PNG）をそのままUnityに適用

***

## クイックスタート（ローカル）

1) 依存をインストール
```
pip install -U gradio pillow numpy
```

2) 下記の app.py を保存して実行
```
python app.py
```
3) ブラウザが開いたら画像を入れて変換

***

## デプロイ（Hugging Face Spaces）

1) Hugging Faceで新規Space作成（Gradio選択）
2) 下記の2ファイルをアップロード
- app.py
- requirements.txt

3) 自動ビルド後、誰でもURLで利用可能

requirements.txt
```
gradio>=4.0.0
Pillow>=10.0.0
numpy>=1.24.0
```

***

## app.py（そのまま動きます）

```python
import gradio as gr
import numpy as np
from PIL import Image
import math

# ---------- ユーティリティ ----------
def load_rgba(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGBA"), dtype=np.uint8)

def load_mask(mask_img: Image.Image, size) -> np.ndarray:
    if mask_img.size != size:
        mask_img = mask_img.resize(size, Image.Resampling.LANCZOS)
    m = np.array(mask_img.convert("L"), dtype=np.uint8)
    # 0/1の2値化（白=1で適用）
    return (m > 32).astype(np.uint8)

def rgb_to_hsv_np(rgb):  # rgb: float32 0-1
    r, g, b = rgb[...,0], rgb[...,1], rgb[...,2]
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    v = maxc
    s = np.zeros_like(v)
    nz = maxc != 0
    s[nz] = (maxc[nz] - minc[nz]) / maxc[nz]
    h = np.zeros_like(v)

    mask = maxc != minc
    rc = np.zeros_like(r); gc = np.zeros_like(g); bc = np.zeros_like(b)
    rc[mask] = (maxc[mask] - r[mask]) / (maxc[mask] - minc[mask])
    gc[mask] = (maxc[mask] - g[mask]) / (maxc[mask] - minc[mask])
    bc[mask] = (maxc[mask] - b[mask]) / (maxc[mask] - minc[mask])

    rmax = (maxc == r) & mask
    gmax = (maxc == g) & mask
    bmax = (maxc == b) & mask

    h[rmax] = (bc[rmax] - gc[rmax])
    h[gmax] = 2.0 + (rc[gmax] - bc[gmax])
    h[bmax] = 4.0 + (gc[bmax] - rc[bmax])
    h = (h / 6.0) % 1.0
    return np.stack([h, s, v], axis=-1)

def hsv_to_rgb_np(hsv):  # hsv: float32 0-1
    h, s, v = hsv[...,0], hsv[...,1], hsv[...,2]
    c = v * s
    h6 = (h * 6.0) % 6.0
    x = c * (1 - np.abs((h6 % 2) - 1))
    z = np.zeros_like(h)

    rgbp = np.zeros(hsv.shape, dtype=hsv.dtype)
    conds = [
        (0 <= h6) & (h6 < 1),
        (1 <= h6) & (h6 < 2),
        (2 <= h6) & (h6 < 3),
        (3 <= h6) & (h6 < 4),
        (4 <= h6) & (h6 < 5),
        (5 <= h6) & (h6 < 6),
    ]
    rgbs = [
        (c, x, z),
        (x, c, z),
        (z, c, x),
        (z, x, c),
        (x, z, c),
        (c, z, x),
    ]
    for cond, (rr, gg, bb) in zip(conds, rgbs):
        rgbp[...,0] = np.where(cond, rr, rgbp[...,0])
        rgbp[...,1] = np.where(cond, gg, rgbp[...,1])
        rgbp[...,2] = np.where(cond, bb, rgbp[...,2])

    m = v - c
    rgb = rgbp + np.stack([m, m, m], axis=-1)
    return rgb

def mask_centroid(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.mean()), int(ys.mean())

# パステル定義（HSV）
PASTELS = {
    "pastel_cyan":     (0.50, 0.30, 0.92),
    "pastel_pink":     (0.92, 0.25, 0.95),
    "pastel_lavender": (0.75, 0.20, 0.90),
    "pastel_mint":     (0.40, 0.25, 0.92),
    "pastel_peach":    (0.08, 0.30, 0.95),
    "pastel_lemon":    (0.15, 0.25, 0.95),
    "pastel_coral":    (0.02, 0.35, 0.90),
    "pastel_sky":      (0.55, 0.20, 0.95),
}

# ---------- 変換ロジック ----------
def apply_basic(rgb, mask01, hue, sat, val, keep_value=0.7, sat_scale=1.0):
    a = rgb[...,3:4] / 255.0
    base = rgb[...,:3] / 255.0
    hsv = rgb_to_hsv_np(base)
    # 明度は元:val を重み付け
    hsv[...,0] = hue
    hsv[...,1] = np.clip(sat * sat_scale, 0, 1)
    hsv[...,2] = np.clip(hsv[...,2] * keep_value + val * (1 - keep_value), 0, 1)
    recolor = hsv_to_rgb_np(hsv)
    mixed = np.where(mask01[...,None]==1, recolor, base)
    out = np.concatenate([mixed, a], axis=-1)
    return (np.clip(out*255,0,255).astype(np.uint8))

def apply_gradient(rgb, mask01, hue, sat, val, keep_value=0.7, highlight=0.4):
    h, w = mask01.shape
    cxcy = mask_centroid(mask01)
    base = rgb[...,:3] / 255.0
    hsv = rgb_to_hsv_np(base)

    if cxcy is None:
        return (rgb)

    cx, cy = cxcy
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    d_norm = (dist - dist[mask01==1].min()) / (dist[mask01==1].ptp()+1e-6)
    d_norm = np.clip(d_norm, 0, 1)

    # 内側→外側で彩度/明度を少し変える
    local_sat = np.clip(sat*(0.85 + 0.3*(1-d_norm)), 0, 1)
    local_val = np.clip(val*(0.9 + 0.2*(1-d_norm)), 0, 1)

    hsv[...,0] = hue
    hsv[...,1] = local_sat
    hsv[...,2] = np.clip(hsv[...,2]*keep_value + local_val*(1-keep_value), 0, 1)

    # 上側ハイライト
    top = (yy < cy - 0.05*h)
    hsv[...,2] = np.where(top & (mask01==1), np.clip(hsv[...,2] + highlight*0.15, 0, 1), hsv[...,2])

    recolor = hsv_to_rgb_np(hsv)
    out_rgb = np.where(mask01[...,None]==1, recolor, base)
    a = rgb[...,3:4] / 255.0
    out = np.concatenate([out_rgb, a], axis=-1)
    return (np.clip(out*255,0,255).astype(np.uint8))

def apply_aurora(rgb, mask01, hue, sat, val, keep_value=0.7, strength=0.3):
    h, w = mask01.shape
    base = rgb[...,:3] / 255.0
    hsv = rgb_to_hsv_np(base)
    yy, xx = np.mgrid[0:h, 0:w]
    wave = (np.sin((xx+yy)*0.02)*0.4 + np.cos(xx*0.015)*0.3 + np.sin(yy*0.02)*0.3)
    hue_offset = np.clip(wave*strength, -0.15, 0.15)

    hsv[...,0] = (hue + hue_offset) % 1.0
    hsv[...,1] = np.clip(sat + (np.sin(xx*0.01+yy*0.015)*0.1+0.1), 0, 0.6)
    hsv[...,2] = np.clip(hsv[...,2]*keep_value + val*(1-keep_value), 0, 1)

    recolor = hsv_to_rgb_np(hsv)
    out_rgb = np.where(mask01[...,None]==1, recolor, base)
    a = rgb[...,3:4] / 255.0
    out = np.concatenate([out_rgb, a], axis=-1)
    return (np.clip(out*255,0,255).astype(np.uint8))

def build_emission(mask01, inner=0.07, outer=0.14, softness=0.06):
    h, w = mask01.shape
    cxcy = mask_centroid(mask01)
    if cxcy is None:
        return (mask01*255).astype(np.uint8)
    cx, cy = cxcy
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    r = np.sqrt(np.sum((np.array(np.nonzero(mask01)).ptp(axis=1)/2)**2)) + 1e-6
    d = dist / r
    # ドーナツ型リング
    ring = np.clip((d - inner) / max(softness,1e-6), 0, 1)
    ring = 1 - np.clip((d - outer) / max(softness,1e-6), 0, 1) * ring
    ring = np.clip(ring, 0, 1) * mask01
    return (ring*255).astype(np.uint8)

# ---------- 推論関数（Gradioハンドラ） ----------
def generate(eye_img, mask_img, preset, mode,
             keep_value, sat_scale, highlight, aurora_strength,
             make_emission, ring_inner, ring_outer, ring_soft):

    if eye_img is None or mask_img is None:
        raise gr.Error("eye_texture と mask の両方をアップロードしてください。")

    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))

    hue, sat, val = PASTELS[preset]

    if mode == "Basic":
        out = apply_basic(rgba, mask01, hue, sat, val, keep_value=keep_value, sat_scale=sat_scale)
    elif mode == "Gradient":
        out = apply_gradient(rgba, mask01, hue, sat, val, keep_value=keep_value, highlight=highlight)
    else:
        out = apply_aurora(rgba, mask01, hue, sat, val, keep_value=keep_value, strength=aurora_strength)

    out_img = Image.fromarray(out, mode="RGBA")

    if make_emission:
        emi = build_emission(mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft)
        emi_img = Image.fromarray(emi, mode="L")
        return out_img, emi_img

    return out_img, None

# ---------- UI ----------
with gr.Blocks(title="Pastel Eye Colorizer") as demo:
    gr.Markdown("## Pastel Eye Colorizer｜マスク領域だけパステル化（Basic / Gradient / Aurora）")

    with gr.Row():
        eye_in = gr.Image(type="pil", label="Eye Texture (RGBA/RGB)")
        mask_in = gr.Image(type="pil", label="Mask (白=適用, 黒=非適用)")

    with gr.Row():
        preset = gr.Dropdown(choices=list(PASTELS.keys()), value="pastel_cyan", label="パレット")
        mode = gr.Radio(choices=["Basic","Gradient","Aurora"], value="Basic", label="効果モード")

    with gr.Accordion("調整（必要に応じて）", open=False):
        keep_value = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="明度保持率（元テクスチャをどれだけ残すか）")
        sat_scale = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="彩度スケール（Basic/Aurora）")
        highlight = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="ハイライト量（Gradient）")
        aurora_strength = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="オーロラ色揺らぎ（Aurora）")

    with gr.Accordion("発光マスクを作る（任意）", open=False):
        make_emission = gr.Checkbox(value=False, label="Emissionマスクも出力する")
        ring_inner = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="リング内半径（相対）")
        ring_outer = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="リング外半径（相対）")
        ring_soft  = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="リングのぼかし（相対）")

    run_btn = gr.Button("生成する")

    out_img = gr.Image(type="pil", label="出力テクスチャ（PNG）")
    emi_img = gr.Image(type="pil", label="Emissionマスク（任意）")

    run_btn.click(
        fn=generate,
        inputs=[eye_in, mask_in, preset, mode, keep_value, sat_scale, highlight, aurora_strength,
                make_emission, ring_inner, ring_outer, ring_soft],
        outputs=[out_img, emi_img]
    )

demo.launch()
```

***

## 使い方の実務メモ
- Maskは白=適用・黒=非適用。境界が硬い場合はマスク側を1–2pxぼかすと自然。
- Basicで「少しくすむ」時は「彩度スケール」を1.1〜1.3に。派手なら0.9以下へ。
- Auroraは強すぎると虹色が主張しすぎるので 0.2–0.35 が目安。
- Unityでは生成PNGを目のマテリアルに適用。発光する場合は、生成したEmissionマスクをlilToonの発光マスクに割り当て、HDR色とIntensityを調整。

***

## 将来拡張のアイデア
- 2色インナー＋外周のツートン対応（セパレートマスク）
- Modular Avatar用メニュー（複数色を一括エクスポート）
- 画像ドラッグ＆ドロップでの一括変換、ZIPダウンロード
- AIでマスク自動推定（虹彩自動検出）

***

このままのコードで「ローカル起動」も「Hugging Faceの公開アプリ」も可能です。必要なら、あなたの配色プリセットを初期値に組み込み、UI文言や既定値をカスタマイズしてお渡しします。




# GitHub Actions（CI + Hugging Face Spacesデプロイ）

以下のワークフローをリポジトリに追加すれば、mainブランチへpush（または手動実行）時に
- 依存をインストール
- Lint＋スモークテスト
- 成果物のZIPをアーティファクト化
- Hugging Face Spacesへデプロイ（自動リビルド）

までを自動化できます。

## 事前準備（Secrets）
- HF_TOKEN: Hugging Faceのアクセストークン（Write権限）
- HF_SPACE_ID: SpacesのID（例: username/pastel-eye-colorizer）
  - 先にSpacesをGradioタイプで作成しておく

## ファイル配置
- app.py（前メッセージのGradioアプリ）
- requirements.txt
- .github/workflows/ci-deploy.yml（下記）

## .github/workflows/ci-deploy.yml

```yaml
name: CI & Deploy to HuggingFace Spaces

on:
  push:
    branches: [ main ]
    paths:
      - "app.py"
      - "requirements.txt"
      - ".github/workflows/**"
      - "assets/**"
  workflow_dispatch:

jobs:
  test:
    name: Lint & Smoke Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install deps
        run: |
          python -m pip install -U pip
          pip install -r requirements.txt
          pip install flake8

      - name: Lint
        run: flake8 --max-line-length 120 app.py

      - name: Smoke test (import app)
        run: |
          python - << 'PY'
          import importlib.util
          spec = importlib.util.spec_from_file_location("app", "app.py")
          m = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(m)
          print("App import OK")
          PY

      - name: Package artifact
        if: always()
        run: |
          mkdir -p dist
          zip -r dist/pastel-eye-colorizer-${{ github.sha }}.zip app.py requirements.txt README.md || true

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ github.sha }}
          path: dist/*.zip

  deploy:
    name: Deploy to HuggingFace Spaces
    needs: test
    # mainブランチ or タグのときに実行（必要に応じ調整）
    if: github.ref_name == 'main' || startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install HuggingFace CLI
        run: |
          python -m pip install -U "huggingface_hub[cli]"

      - name: Upload to Space
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          HF_SPACE_ID: ${{ secrets.HF_SPACE_ID }} # e.g. username/pastel-eye-colorizer
        run: |
          test -n "$HF_TOKEN" || (echo "HF_TOKEN not set" && exit 1)
          test -n "$HF_SPACE_ID" || (echo "HF_SPACE_ID not set" && exit 1)
          huggingface-cli login --token "$HF_TOKEN"
          # 必要なファイルのみ転送（.git/.githubは除外）
          huggingface-cli upload . \
            --repo-id "spaces/$HF_SPACE_ID" \
            --repo-type space \
            --include "app.py" "requirements.txt" "assets" \
            --exclude ".git" ".github" --commit-message "CI deploy: $GITHUB_SHA"

      - name: Restart Space (trigger build)
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          HF_SPACE_ID: ${{ secrets.HF_SPACE_ID }}
        run: |
          python - << 'PY'
          import os
          from huggingface_hub import HfApi
          api = HfApi(token=os.environ["HF_TOKEN"])
          api.restart_space(repo_id=os.environ["HF_SPACE_ID"])
          print("Space restart triggered")
          PY
```

## 任意（超軽量のテストを追加したい場合）
tests/smoke_test.py を用意し、最低限の関数がインポートできるか確認できます。

```python
# tests/smoke_test.py
import importlib.util

def test_import_app():
    spec = importlib.util.spec_from_file_location("app", "app.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m is not None
```

そして requirements.txt に pytest を追加し、Lintの後に
- run: pytest -q
を足すと自動テストも可能です。

以上で、push→自動テスト→Spacesデプロイが回るようになります。必要に応じてトリガー条件や転送ファイルのパスを調整してください。