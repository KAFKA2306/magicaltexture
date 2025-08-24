# requirements.md

パステル瞳テクスチャ生成アプリ（Pastel Eye Colorizer）再現実装のための要求仕様書

## 1. 目的

- 画像（瞳テクスチャ）に対し、マスク領域のみをパステルカラーへ変換する軽量なブラウザアプリを提供する。
- 高度な学習モデルを使わず、NumPy/Pillow による決定論的な色変換で、安定・高速・再現性の高い結果を返す。
- ローカル実行と Hugging Face Spaces で同一コードを利用可能にする。

## 2. 対象ユーザー

- 3D/2D アバター開発者、ゲーム開発者、VTuber/イラスト制作者。
- 画像ツールに詳しくないユーザーでも直感的に使える UI を想定。

## 3. 用語定義

- Eye Texture（瞳テクスチャ）: 加工対象の画像。RGB/RGBA を許容。
- Mask（マスク）: 変換の適用範囲を示す画像。白=適用、黒=非適用の2値またはグレースケール。
- Emission マスク: 発光に使うリング状の輝度マスク L（8bit）。

## 4. スコープ

- 入力画像2枚（テクスチャ、マスク）
- パステル色プリセット（HSV）：cyan, pink, lavender, mint, peach, lemon, coral, sky
- 効果モード：Basic / Gradient / Aurora
- 調整パラメータ：明度保持率、彩度スケール、ハイライト量、オーロラ強度
- Emission リングマスクの任意生成（パラメータ：内半径、外半径、ぼかし）
- 出力：変換画像（RGBA PNG）と任意の Emission マスク（L PNG）

## 5. 機能要件（FR）

- 画像入出力
  - テクスチャ入力: RGB/RGBA（任意解像度）
  - マスク入力: L/RGB（自動リサイズ）、白系=適用領域
  - 出力画像: RGBA PNG（アルファ保持）
  - Emission マスク: L PNG（生成がオンのときのみ）

- マスク処理
  - マスク画像を L に変換
  - しきい値 > 32 を 1（適用）、それ以外 0（非適用）
  - テクスチャのサイズにリサンプル（Lanczos）

- 色変換
  - RGB↔HSV を NumPy ベースで実装
  - Basic: hue=プリセット、saturation=プリセット×スケール、value=元とプリセットを keep_value でブレンド
  - Gradient: 中心から外周に向けて sat/value を段階的に変化、上部にわずかなハイライト
  - Aurora: 正弦波合成による hue の微小オフセット（揺らぎ）

- Emission マスク
  - マスクの重心と近似半径から同心リング（ドーナツ）を合成
  - 内/外半径とソフトネスでフェザーを制御
  - マスク外は 0

- UI（Gradio）
  - 画像2枚のアップロード
  - ドロップダウン：色プリセット
  - ラジオ：効果モード（Basic/Gradient/Aurora）
  - アコーディオン：詳細調整
  - アコーディオン：Emission マスクの生成（任意）
  - 実行ボタンと結果プレビュー
  - エラー通知（画像未入力時など）

## 6. 非機能要件（NFR）

- 性能
  - 2048×2048 程度まで実用的な応答（数秒）を目標
  - 計算はベクトル化（NumPy）で実装
- 再現性
  - 乱数不使用（正弦波を使うが決定論）
- 可搬性
  - Python 3.11 を推奨
  - 依存は gradio, pillow, numpy に限定
- セキュリティ
  - ユーザーアップロード画像はプロセス内でのみ利用
  - 外部送信なし
- アクセシビリティ/UX
  - 日本語 UI テキスト
  - コントロールは適切な初期値と範囲・ステップ
- 国際化
  - ソース側で英語リソース化しやすい構造（必要に応じて）

## 7. 入出力仕様（詳細）

- 入力
  - Eye Texture: PIL.Image（RGB/RGBA）
  - Mask: PIL.Image（L/RGB）。自動で Eye Texture と同じサイズへリサイズ
- 内部表現
  - RGBA: uint8（0–255）
  - RGB/HSV: float32（0–1）
  - マスク: uint8（0/1）
- 出力
  - 変換画像（RGBA PNG）
  - Emission（L PNG、任意）

## 8. アルゴリズム仕様（要点）

- rgb_to_hsv_np / hsv_to_rgb_np
  - 0除算回避のため分母に 1e-12 を加算
  - hue は [0,1) の範囲へ正規化
- Basic
  - H=hue_preset
  - S=clip(sat_preset×sat_scale, 0..1)
  - V=clip(V_src×keep_value + val_preset×(1-keep_value), 0..1)
- Gradient
  - マスク重心からの距離 dist をマスク内で 0..1 に正規化
  - local_sat = sat × (0.85 + 0.3×(1 - d))
  - local_val = val × (0.90 + 0.2×(1 - d))
  - 上部（y < cy - 0.05*h）に対して V を + highlight×0.15
- Aurora
  - wave = sin((x+y)*0.02)*0.4 + cos(x*0.015)*0.3 + sin(y*0.02)*0.3
  - hue_offset = clip(wave×strength, -0.15..0.15)
  - S を最大 0.6 にクリップ
- Emission
  - r ≒ hypot((xs.max()-xs.min())/2, (ys.max()-ys.min())/2)
  - d = dist / r
  - ring = clamp(outerフェザー) × clamp(1 - innerフェザー) × mask

## 9. UI 仕様（コントロール定義）

- パレット: Dropdown
  - 値: pastel_cyan, pastel_pink, pastel_lavender, pastel_mint, pastel_peach, pastel_lemon, pastel_coral, pastel_sky
- 効果モード: Radio
  - 値: Basic, Gradient, Aurora
- 調整（Basic/Aurora 共通）
  - keep_value: Slider [0.0, 1.0], step 0.05, default 0.7
  - sat_scale: Slider [0.5, 2.0], step 0.05, default 1.0
- 調整（Gradient）
  - highlight: Slider [0.0, 1.0], step 0.05, default 0.4
- 調整（Aurora）
  - aurora_strength: Slider [0.0, 0.6], step 0.02, default 0.3
- Emission（任意）
  - make_emission: Checkbox default False
  - ring_inner: Slider [0.02, 0.30], step 0.01, default 0.07
  - ring_outer: Slider [0.05, 0.50], step 0.01, default 0.14
  - ring_soft:  Slider [0.01, 0.30], step 0.01, default 0.06

## 10. エラーハンドリング

- 入力未指定の場合：UI 上でメッセージ表示（gr.Error）
- マスク内に白画素が無い：元画像を返すか、メッセージ提示（実装では早期 return）

## 11. 依存関係

- Python >= 3.11
- gradio >= 4.0.0
- Pillow >= 10.0.0
- numpy >= 1.24.0

requirements.txt
```
gradio>=4.0.0
Pillow>=10.0.0
numpy>=1.24.0
```

## 12. ビルド/実行

- ローカル
  - pip で依存をインストール後、python app.py
- Spaces
  - app.py と requirements.txt を配置
  - README のフロントマターを定義（title/emoji/color/sdk/app_file など）
  - 起動は自動ビルド

## 13. CI/CD

- Lint（flake8）
- Smoke Test（import app）
- アーティファクト作成（任意）
- HfApi で Space へアップロード、再起動トリガー
- Secrets
  - HF_TOKEN（Write）
  - HF_SPACE_ID（username/space-name）

## 14. 受け入れ条件（サンプル）

- 画像とマスクをアップロードし、各モードで PNG が出力されること
- Emission をオンで L PNG が出力されること
- 主要プリセット 8 色で表示が破綻しないこと
- スライダの上下で効果が視覚的に変化すること
- 2048×2048 でタイムアウトしないこと（環境依存のため目安）

## 15. 制約・既知の限界

- マスクしきい値/輪郭に依存した品質
- 極端な露出/陰影の源画像ではパステルの再現性に限界
- Aurora の彩度上限 0.6 に制限（彩度暴走抑制）

## 16. 将来拡張

- ツートン（内外 2 色）対応
- 反射/ハイライトの別マスク対応
- ZIP 一括変換とドラッグ&ドロップ
- 自動マスク推定（学習モデル導入）


eye_color_pastel_lavender_aurora.png
eye_color_pastel_cyan_aurora.png
