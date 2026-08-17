---
title: Pastel Eye Colorizer
emoji: 🎨
colorFrom: blue
colorTo: pink
sdk: gradio
sdk_version: "4.0.0"
app_file: app.py
pinned: false
---

# magicaltexture — Pastel Eye Colorizer

[![CI & Deploy to HuggingFace Spaces](https://github.com/KAFKA2306/magicaltexture/actions/workflows/deploy.yml/badge.svg)](https://github.com/KAFKA2306/magicaltexture/actions/workflows/deploy.yml)

**瞳の色を変えたいだけなのに、元の明るさ・影・透明感まで壊したくない。**

`magicaltexture` は、元テクスチャと白黒maskを使って虹彩だけをrecolorし、**元の陰影を残しながら「どこを・どの程度変えたか」を自分で調整できるWeb tool**です。

- Web app: https://k4fka-magicaltexture.hf.space
- Hugging Face Space: https://huggingface.co/spaces/k4fka/magicaltexture
- Guide: https://kafka2306.github.io/magicaltexture/

## Vision

avatar texture editingを「色を重ねて、Unityで開いて、壊れていたらやり直す」作業から、**ブラウザ上で変更範囲と明度保持を調整し、元の表情を残したまま色だけを試せる体験**へ変えます。

## Design philosophy

- **Mask before effect.** 画像全体へ色を掛けず、変更領域をexplicit maskで限定する。
- **Preserve luminance when possible.** 元textureの陰影・highlightを`keep_value`で残せるようにする。
- **User controls the trade-off.** saturationや明度保持率を自動最適化のblack boxへ隠さない。
- **RGBA in, RGBA out.** avatar textureとして再利用しやすいformatを維持する。
- **Emission is optional.** 発光表現をbase recolorと混ぜず、必要な場合だけmaskを生成する。
- **Local appearance still needs Unity review.** PNG生成成功をavatar上の見た目成功へ読み替えない。
- **Source rights stay with the source.** 購入textureの規約を生成toolが上書きしない。

## Why / 差別化

単純なhue shiftやcolor overlayは速い一方、白目・まつ毛・shadowまで染めたり、元textureの立体感を失わせやすいです。

このtoolの差別化はGradioやcolor paletteではなく、**recolorする場所をmaskで明示し、元のvalueをどこまで残すかを利用者自身が調整できること**です。

「AIがいい感じに変える」のではなく、変えてよい領域と残したい情報を分離します。

## User journey

```text
元Eye Textureを用意
  → iris maskを作る
  → palette / modeを選ぶ
  → keep_value / saturationを調整
  → preview
  → RGBA PNGを出力
  → Unity / lilToonで実avatar上を確認
```

## What you can do

- 元の明るさを残すeye recolor
- pastel palette
- Basic / Gradient / Aurora mode
- saturation / luminance-retention tuning
- optional emission ring mask
- RGBA PNG output
- browser execution

## Inputs

### Eye Texture

元の瞳texture。RGB / RGBA PNGを推奨します。

### Mask

変更範囲を示すgrayscale imageです。

```text
white = recolor
black = preserve source
gray  = partial blend
```

元textureと同じresolution / layoutを推奨します。

## Mask creation

1. Photoshop / GIMP / Clip Studio等で元textureを開く
2. 新layerを作る
3. irisだけwhite
4. sclera / eyelid / eyelash / unwanted shadowはblack
5. 必要ならedgeへ1〜2px程度blur
6. 同canvas sizeの8-bit grayscale PNGとして保存

左右eyeが同texture内なら、両方のirisを対応位置でmaskしてください。

## Modes

### Basic

指定colorへの基本recolor。

### Gradient

中心から外周へcolor variation + highlight。

### Aurora

周期的なhue variation。

主なcontrols:

- `keep_value` — source luminance retention
- `sat_scale` — saturation multiplier
- gradient highlight amount
- aurora variation strength
- emission inner/outer radius + blur

値を大きくすれば良くなるわけではありません。source textureとpreviewを見て判断します。

## Unity / lilToon boundary

1. output PNGをUnityへimport
2. lilToon Main Textureへ設定
3. Material Colorをwhite基準にする
4. eye mesh Rendererへassign
5. Play Modeでleft/right、UV、alpha、lightingを確認

Emission使用時:

1. lilToon Emissionをenable
2. generated emission maskを指定
3. HDR emission color / intensity調整
4. dark / bright / Bloom on/offで確認

lilToon property nameやbehaviorはversionで変わり得るため、使用versionのofficial docsを確認してください。

## Troubleshooting

### 色が薄い

- `sat_scale`を少し上げる
- mask white areaを確認
- Unity Material Colorをwhiteへ戻す

### 暗い

- `keep_value`を調整
- source textureのshadowを確認
- Unity lighting / emissionを確認

### Mask境界が目立つ

- maskへ軽いblur
- texture / maskのresolution・position一致を確認
- alpha boundaryを確認

## Privacy / rights

- source textureの利用規約を確認
- 購入avatar textureを無断公開・共有しない
- Hugging Face Spaceへ送る画像に機密情報を入れない
- generated outputの再配布・商用可否はsource texture規約に従う

## Local run

```bash
python app.py
```

実際のPython version / dependencyはSpace設定とrepositoryのdependency filesを正とします。

## Done

成功指標はpalette数やeffect数ではありません。

**利用者が「どこを変え、何を残すか」を自分で制御し、元の陰影を壊さずに色案を試し、最終的なavatar上の見た目はUnityで別途確認できること**をDoneとします。