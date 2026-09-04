from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import gradio as gr
from PIL import Image

from .config import PASTELS, PRETTY
from .core import (
    apply_aurora,
    apply_basic,
    apply_gradient,
    build_emission,
    load_mask,
    load_rgba,
)


def _sanitize(s: str) -> str:
    """Sanitize filename string."""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _png_bytes(image: Image.Image, mode: str) -> bytes:
    """Serialize a normalized input/output image as deterministic PNG bytes."""
    normalized = image.convert(mode)
    buf = io.BytesIO()
    normalized.save(buf, format="PNG")
    return buf.getvalue()


def _generator_revision() -> str:
    """Return the exact deployed revision when available, otherwise an explicit local state."""
    revision_file = Path(__file__).resolve().parent.parent / ".magicaltexture-revision"
    if revision_file.is_file():
        revision = revision_file.read_text(encoding="utf-8").strip()
        if revision:
            return revision
    return (
        os.environ.get("MAGICALTEXTURE_REVISION")
        or os.environ.get("GITHUB_SHA")
        or "local-unpinned"
    )


def _package_guide(*, primary_preview: str, has_emission: bool) -> bytes:
    """Build a concise delivery guide without claiming rights or runtime validation."""
    emission_step = (
        "- emission_mask.png: lilToonのEmissionで使うマスク候補です。実際の色・強度はUnity上で調整してください。\n"
        if has_emission
        else "- Emission maskはこのZIPでは生成していません。\n"
    )
    text = (
        "magicaltexture creator package\n"
        "==============================\n\n"
        "このZIPは、生成した瞳テクスチャと再現条件をまとめた納品準備用パッケージです。\n"
        "生成成功はUnity・lilToon・VRChat上の見た目確認を意味しません。\n\n"
        "内容\n"
        "----\n"
        "- *.png: 生成したMain Texture候補です。\n"
        f"- primary preview: {primary_preview}\n"
        f"{emission_step}"
        "- preset_manifest.json: 入力ハッシュ、生成条件、generator revision、出力ハッシュを記録します。\n"
        "- README.txt: このファイルです。\n\n"
        "Unity / lilToonでの確認\n"
        "----------------------\n"
        "1. 生成PNGをUnityへimportします。\n"
        "2. 対象materialのlilToon Main Textureへ生成したMain Texture候補を設定します。\n"
        "3. Emissionを使う場合は、使用中のlilToonのEmission設定へemission_mask.pngを割り当てます。\n"
        "4. 対象avatarでUV、alpha、左右の目、明所・暗所、必要ならBloom有無を確認します。\n"
        "5. 使用中のlilToon versionの公式ドキュメントを確認し、material設定を調整します。\n\n"
        "権利と配布\n"
        "----------\n"
        "- このZIPは元テクスチャやavatarの利用許諾を追加・変更しません。\n"
        "- 編集、納品、販売、再配布の可否は元素材の規約と権利者の許諾を確認してください。\n"
        "- preset_manifest.jsonのハッシュは生成物の同一性確認用で、権利証明ではありません。\n"
    )
    return text.encode("utf-8")


def generate_single(
    eye_img: Image.Image,
    mask_img: Image.Image,
    preset: str,
    mode: str,
    keep_value: float,
    sat_scale: float,
    highlight: float,
    aurora_strength: float,
    make_emission: bool,
    ring_inner: float,
    ring_outer: float,
    ring_soft: float,
):
    """Generate single eye texture with specified parameters."""
    if eye_img is None or mask_img is None:
        raise gr.Error("eye_texture と mask の両方をアップロードしてください。")
    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))
    hue, sat, val = PASTELS[preset]
    if mode == "Basic":
        out = apply_basic(
            rgba, mask01, hue, sat, val, keep_value=keep_value, sat_scale=sat_scale
        )
    elif mode == "Gradient":
        out = apply_gradient(
            rgba, mask01, hue, sat, val, keep_value=keep_value, highlight=highlight
        )
    else:
        out = apply_aurora(
            rgba, mask01, hue, sat, val, keep_value=keep_value, strength=aurora_strength
        )
    out_img = Image.fromarray(out, mode="RGBA")
    if make_emission:
        emi = build_emission(
            mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft
        )
        emi_img = Image.fromarray(emi, mode="L")
        return out_img, emi_img
    return out_img, None


def generate_batch(
    eye_img: Image.Image,
    mask_img: Image.Image,
    selected_colors: List[str],
    selected_modes: List[str],
    filename_prefix: str,
    keep_value: float,
    sat_scale: float,
    highlight: float,
    aurora_strength: float,
    make_emission: bool,
    ring_inner: float,
    ring_outer: float,
    ring_soft: float,
):
    """Generate a creator-ready batch ZIP with reproducibility and rights guidance."""
    if eye_img is None or mask_img is None:
        raise gr.Error("eye_texture と mask の両方をアップロードしてください。")
    if not selected_colors:
        raise gr.Error("少なくとも1つのパレットを選択してください。")
    if not selected_modes:
        raise gr.Error("少なくとも1つの効果モードを選択してください。")

    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))
    eye_png = _png_bytes(eye_img, "RGBA")
    mask_png = _png_bytes(mask_img, "L")

    gallery_items = []
    output_manifest = []
    primary_preview = None
    zip_buf = io.BytesIO()
    zip_name = f"{_sanitize(filename_prefix) or 'batch'}_{uuid.uuid4().hex[:8]}.zip"

    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if make_emission:
            emi = build_emission(
                mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft
            )
            emi_png = _png_bytes(Image.fromarray(emi, mode="L"), "L")
            emission_name = "emission_mask.png"
            zf.writestr(emission_name, emi_png)
            output_manifest.append(
                {
                    "path": emission_name,
                    "kind": "emission_mask",
                    "sha256": _sha256(emi_png),
                    "size_bytes": len(emi_png),
                }
            )

        for ckey in selected_colors:
            hue, sat, val = PASTELS[ckey]
            for mode in selected_modes:
                if mode == "Basic":
                    out = apply_basic(
                        rgba,
                        mask01,
                        hue,
                        sat,
                        val,
                        keep_value=keep_value,
                        sat_scale=sat_scale,
                    )
                elif mode == "Gradient":
                    out = apply_gradient(
                        rgba,
                        mask01,
                        hue,
                        sat,
                        val,
                        keep_value=keep_value,
                        highlight=highlight,
                    )
                else:
                    out = apply_aurora(
                        rgba,
                        mask01,
                        hue,
                        sat,
                        val,
                        keep_value=keep_value,
                        strength=aurora_strength,
                    )

                pil = Image.fromarray(out, mode="RGBA")
                caption = f"{PRETTY.get(ckey, ckey)} · {mode}"
                gallery_items.append((pil, caption))
                fname = (
                    f"{_sanitize(filename_prefix) or 'eye'}_{ckey}_{mode.lower()}.png"
                )
                if primary_preview is None:
                    primary_preview = fname
                png = _png_bytes(pil, "RGBA")
                zf.writestr(fname, png)
                output_manifest.append(
                    {
                        "path": fname,
                        "kind": "main_texture",
                        "palette": ckey,
                        "mode": mode,
                        "sha256": _sha256(png),
                        "size_bytes": len(png),
                    }
                )

        if primary_preview is None:
            raise RuntimeError("Batch generation produced no main texture output.")

        guide_name = "README.txt"
        guide = _package_guide(
            primary_preview=primary_preview,
            has_emission=make_emission,
        )
        zf.writestr(guide_name, guide)
        output_manifest.append(
            {
                "path": guide_name,
                "kind": "package_guide",
                "sha256": _sha256(guide),
                "size_bytes": len(guide),
            }
        )

        manifest = {
            "schema_version": 1,
            "generator": {
                "name": "magicaltexture",
                "repository": "https://github.com/KAFKA2306/magicaltexture",
                "revision": _generator_revision(),
            },
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "eye_texture": {
                    "normalized_png_sha256": _sha256(eye_png),
                    "width": eye_img.width,
                    "height": eye_img.height,
                    "mode": "RGBA",
                },
                "mask": {
                    "normalized_png_sha256": _sha256(mask_png),
                    "width": mask_img.width,
                    "height": mask_img.height,
                    "mode": "L",
                },
            },
            "selection": {
                "palettes": list(selected_colors),
                "modes": list(selected_modes),
                "filename_prefix": _sanitize(filename_prefix) or "eye",
            },
            "parameters": {
                "keep_value": keep_value,
                "sat_scale": sat_scale,
                "highlight": highlight,
                "aurora_strength": aurora_strength,
                "make_emission": make_emission,
                "ring_inner": ring_inner,
                "ring_outer": ring_outer,
                "ring_soft": ring_soft,
            },
            "package": {
                "guide": guide_name,
                "primary_preview": primary_preview,
                "runtime_validation": "not_performed",
            },
            "outputs": output_manifest,
            "rights": {
                "source_files_embedded": False,
                "notice": (
                    "Generated-output redistribution/commercial rights remain subject "
                    "to the source texture and avatar license."
                ),
            },
        }
        zf.writestr(
            "preset_manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode(
                "utf-8"
            ),
        )

    zip_buf.seek(0)
    zip_path = os.path.join(tempfile.gettempdir(), zip_name)
    with open(zip_path, "wb") as f:
        f.write(zip_buf.read())
    return gallery_items, zip_path
