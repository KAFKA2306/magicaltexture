

# design.md

パステル瞳テクスチャ生成アプリ 設計書

## 1. 全体構成

- フロント/バック一体の Gradio アプリ（サーバ/クライアント分割なし）
- 画像処理は NumPy（ベクトル化）＋ Pillow（I/O）のみ
- 状態はメモリ上に限定（永続化なし）

ディレクトリ例
```
.
├─ app.py
├─ requirements.txt
├─ README.md
└─ .github/workflows/deploy.yml
```

## 2. コンポーネント

- UI レイヤ（Gradio）
  - 入力: 画像コンポーネント（Image）
  - 選択: Dropdown/Radio
  - 調整: Slider/Checkbox
  - 出力: Image（2枚）
  - ハンドラ: run_btn.click → generate()
- 画像処理レイヤ
  - load_rgba, load_mask
  - rgb_to_hsv_np, hsv_to_rgb_np
  - apply_basic, apply_gradient, apply_aurora
  - build_emission
- 設定/定数
  - PASTELS（HSV プリセット）

## 3. データフロー

1) ユーザーがテクスチャとマスクをアップロード
2) generate() が PIL → ndarray に変換
3) マスクをリサイズ→2値化→0/1 ndarray へ
4) 選択モードに応じて apply_* を実行
5) 変換結果を RGBA uint8 へ戻し、PIL Image 化
6) Emission 指定時は build_emission で L Image を生成
7) Gradio に返却、UI に表示

## 4. アルゴリズム詳細

- rgb_to_hsv_np
  - 入力: float32 RGB（0..1）
  - max/min, s=(max-min)/max、h はチャネルごとの最大値で分岐
  - 分母が 0 近傍の領域で 1e-12 を加算し安定化
- hsv_to_rgb_np
  - h×6 を 0..6 へ折り返し、6セグメントで条件分岐
  - 中間値 x, m=v-c を用いて RGB を復元

- apply_basic
  - 既存明度をある割合で残し、プリセットの value とブレンド
  - マスク内のみ recolor、外は base を合成

- apply_gradient
  - マスクの重心 (cx, cy) を計算
  - dist をマスク領域内で 0..1 へ正規化（min/max はマスク領域のみ）
  - sat/value を内側ほど高く外側ほど低く
  - 上側帯（yy < cy - 0.05*h）に微ハイライト

- apply_aurora
  - wave フィールドで hue を揺らす（±0.15 にクリップ）
  - S は 0.6 を上限に抑制
  - 明度は basic と同様のブレンド

- build_emission
  - マスクの外接楕円半径を r ≒ hypot(rx, ry) で近似
  - d=dist/r から inner/outter の二つのフェザーを合成しドーナツ化
  - マスク外は 0

## 5. 精度・性能・メモリ

- すべてベクトル演算。ループ不使用
- 中間アレイは float32。入出力のみ uint8
- 2048×2048 の RGBA 処理で数百 MB 程度の一時配列が発生しうるため、同時実行は queue() で制御

## 6. エッジケース設計

- マスクが全黒（白無し）
  - Gradient: 早期 return rgb（処理スキップ）
  - Emission: マスク×255 を返す（全部 0）
- 入力が RGB（アルファなし）
  - RGBA に昇格。アルファは 255（不透明）
- 非常に小さい画像
  - 正弦波やハイライトの効果が目視しづらいが破綻はしない
- ハイライトやオーロラ強度が過大
  - クリップで上限を保証

## 7. UI 設計

- レイアウト
  - Row1: 入力画像（テクスチャ・マスク）
  - Row2: パレット（Dropdown）、モード（Radio）
  - Acc1: 調整（keep_value, sat_scale, highlight, aurora_strength）
  - Acc2: Emission（make_emission, ring_*）
  - 下段: 実行ボタン、出力プレビュー 2 枚

- 初期値
  - pastel_cyan / Basic / keep_value=0.7 / sat_scale=1.0 / highlight=0.4 / aurora_strength=0.3
  - Emission はオフ

- 文言
  - 日本語表記、説明は短く具体的に

## 8. 例外・バリデーション

- 入力未指定時: gr.Error で明確に通知
- スライダの範囲外入力は Gradio が UI レベルで防止
- 内外半径の論理整合（inner < outer）が UI 値の範囲で担保されるよう設計

## 9. ロギング・デバッグ

- 初期は標準出力ログ最小限
- 必要に応じて時間計測（処理時間）を追加可能

## 10. デプロイ設計（Spaces）

- README 先頭にフロントマター（title, emoji, sdk, app_file 等）
- requirements.txt のみでビルド可能
- app.py は if __name__ == "__main__": demo.queue().launch()
- スリープ復帰を考慮し、初回アクセスに余裕をもたせる運用

## 11. CI/CD 設計

- test ジョブ
  - pip install
  - flake8（--max-line-length 120）
  - import によるスモークテスト
- deploy ジョブ
  - huggingface_hub をインストール
  - HfApi.upload_folder で Space へ反映
  - HfApi.restart_space でビルド再起動
- 並列実行制御
  - concurrency で ref ごとに直列化（任意）
- Secrets
  - HF_TOKEN（Write）
  - HF_SPACE_ID（username/space-name）

## 12. テスト方針

- 単体（軽量）
  - app.py の import 成功（構文エラー検出）
  - 主要関数の呼び出し（小さなダミー配列）で例外が出ないこと
- 手動 E2E
  - 代表 8 プリセット×3 モードで視覚確認
  - Emission 生成のリング位置・ソフトネス確認
  - 境界の硬いマスク/ぼかしたマスク比較

## 13. コード規約

- PEP8 準拠（一部実用的に 120 桁許容）
- 命名: snake_case
- 型ヒント: 主要関数に付与
- 例外: ユーザ入力系は明確なメッセージで通知

## 14. メンテナンス指針

- プリセット拡張
  - PASTELS に HSV タプルを追加
- パラメータチューニング
  - 実運用のフィードバックでデフォルト値を調整
- 互換性
  - 依存ライブラリのメジャーアップデート時に確認

## 15. リスクと対策

- 画像サイズ肥大によるメモリ圧迫
  - 説明文で実用解像度の目安を提示
  - 必要に応じて最大サイズの制限を UI で設ける
- CLI 仕様変更（デプロイ）
  - 旧 CLI 依存を避け、HfApi を利用

## 16. 将来設計メモ

- サーバレス/マイクロサービス化の必要性は低い（計算軽量）
- 需要に応じてバックエンドとフロントを分離し、非同期キューやバッチ処理を導入可能
- 自動マスク推定を加える場合は別エンドポイント/別 Space と連携し、現行機能の軽量さを維持