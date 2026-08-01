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

# magicaltexture — VRChat向け瞳テクスチャ色変換

**Webアプリ:** https://k4fka-magicaltexture.hf.space

**Hugging Face Space:** https://huggingface.co/spaces/k4fka/magicaltexture

**使い方ガイド:** https://kafka2306.github.io/magicaltexture/

元の瞳テクスチャと白黒マスクを入力し、虹彩部分へパステルカラー、グラデーション、オーロラ風の色変化を適用するGradioアプリです。必要に応じてEmission用のグレースケールマスクも生成します。

## できること

- 瞳テクスチャの明るさを残した色変換
- パステルカラーパレットの選択
- Basic / Gradient / Auroraモード
- 彩度と明度保持率の調整
- 発光用リングマスクの生成
- RGBA PNGでの出力
- ブラウザ上での実行

## 入力

### Eye Texture

元の瞳テクスチャです。PNGのRGBまたはRGBA画像を推奨します。

### Mask

適用範囲を示す白黒画像です。

```text
白 = 色変換する領域
黒 = 元の色を保持する領域
灰色 = 部分的に適用する境界
```

元テクスチャと同じ解像度・配置で作成するのが最も安全です。

## マスクの作り方

1. Photoshop、GIMP、Clip Studio Paintなどで元テクスチャを開く
2. 新しいレイヤーを作る
3. 虹彩だけを白で塗る
4. 白目、まぶた、まつ毛、影などは黒にする
5. 必要に応じて境界へ1〜2px程度のぼかしを加える
6. 元画像と同じキャンバスサイズで8bitグレースケールPNGとして保存する

左右の目が同じテクスチャ内にある場合は、両方の虹彩を同じ位置関係でマスクしてください。

## 使い方

1. Webアプリを開く
2. `Eye Texture`へ元画像をアップロードする
3. `Mask`へ白黒マスクをアップロードする
4. パレットを選ぶ
5. 効果モードを選ぶ
6. `keep_value`と`sat_scale`を調整する
7. 必要な場合はEmissionマスク出力を有効にする
8. 生成を実行する
9. 出力PNGを保存する

## 主な設定

### パレット

```text
pastel_cyan
pink
lavender
mint
peach
lemon
coral
sky
```

### 効果モード

- **Basic** — 指定色への基本変換
- **Gradient** — 中心から外周への色変化とハイライト
- **Aurora** — 色相を周期的に変化させる効果

### 調整値

- `keep_value` — 元画像の明度をどの程度残すか
- `sat_scale` — 彩度の倍率
- Gradientのハイライト量
- Auroraの揺らぎ強度
- Emissionリングの内径・外径・ぼかし

値を大きくすると必ず良くなるわけではありません。元画像とマスクを見ながら調整してください。

## Unity / lilToonで使う

1. 生成したPNGをUnityへインポートする
2. lilToonマテリアルのMain Textureへ設定する
3. マテリアルのColorは白を基準にする
4. 目メッシュのRendererへ割り当てる
5. Play Modeで左右、UV、透明度を確認する

Emissionを使う場合:

1. lilToonのEmissionを有効にする
2. 生成したEmissionマスクを対応スロットへ設定する
3. HDRのEmission Colorと強度を調整する
4. 暗所・明所・Bloom有無で確認する

lilToonの設定名はバージョンによって変わる可能性があるため、使用中の公式ドキュメントを確認してください。

## 仕上がりの調整

### 色が薄い

- `sat_scale`を少し上げる
- マスクの白領域を確認する
- Unity側のMaterial Colorを白へ戻す

### 暗い

- `keep_value`を調整する
- 元テクスチャの陰影が強すぎないか確認する
- Unity側のライティングとEmissionを確認する

### マスク境界が目立つ

- マスクへ軽いぼかしを加える
- 元画像とマスクの解像度・位置を一致させる
- アルファ境界を確認する

## 権利・プライバシー

- アップロードするテクスチャの利用規約を確認してください
- 購入アバターのテクスチャを、許諾なく公開・共有しないでください
- Hugging Face Spaceへ送信する画像に機密情報を含めないでください
- 生成物の再配布・商用利用可否は元テクスチャの規約に従います

## ローカル実行

リポジトリの依存関係を導入し、Gradioアプリを起動します。

```bash
python app.py
```

実際のPython版と依存関係は、Spaceの設定とリポジトリ内の依存ファイルを正としてください。

**README最終監査:** 2026-08-01
