# 失敗一覧・手作業一覧・解決策（Pastel Eye Colorizer デプロイ)

## 1) 失敗した事象一覧

- デプロイ失敗（古い CLI の非互換）
  - huggingface-cli login は非推奨警告
  - huggingface-cli upload が --repo-id "spaces/..." を受け付けず exit 2
- Space 側の設定エラー（README メタデータ不足）
  - 「Missing configuration in README」エラー（フロントマター未記載）
- Space 側の設定エラー（README メタデータ不正）
  - colorFrom: cyan が許容外で 400 Bad Request（許容: red, yellow, green, blue, indigo, purple, pink, gray）

- Hugging Face Spaces が「Your Space is using an old version of Gradio (4.0.0)…」と警告しているのは、README の sdk_version が 4.0.0 に固定されているためです。requirements.txt の「gradio>=4.0.0」だけでは最新にならず、sdk_version の固定が優先されます。

## 2) 手作業が必要な作業一覧

- GitHub Secrets 設定
  - HF_TOKEN（Write 権限付き）
  - HF_SPACE_ID（例: username/space-name）
- README.md の修正
  - 先頭にフロントマターを追加
  - colorFrom を許容色に変更（例: blue）または colorFrom/colorTo を削除
- ワークフロー修正反映
  - deploy.yml をコミット＆プッシュ（HfApi 方式）
  - アップロード対象に README.md を含める（allow_patterns に追加）
- Space 側の確認・運用
  - デプロイ後のビルド/ログ確認（エラーが出ないか）
  - 必要に応じて Space を手動で Restart
  - 初回アクセス時の起動確認（UI 表示、各モード/Emission の動作）
- オプション（体験最適化）
  - requirements.txt から ruff/black を外す（ビルド時間短縮）
  - demo.queue().launch() の有効化（同時実行の安定性）
  - Hardware/休止設定の見直し（負荷/起動時間に応じて）

## 3) 解決策一覧（推奨手順）

- デプロイ経路の刷新（非互換回避）
  - GitHub Actions の deploy ジョブで Python API（HfApi.upload_folder, restart_space）を使用
  - 代替として新 CLI（hf auth login / hf upload）を利用しても可
- README メタデータの整備
  - フロントマター例
    - title/emoji/sdk/app_file/sd_version を記述
    - colorFrom は許容値のいずれか（例: blue）、colorTo も許容値（例: pink）
    - もしくは colorFrom/colorTo を省略してバリデーション回避
- CI 設計の実践ポイント
  - test ジョブ（pip install → flake8 → import のスモークテスト）
  - deploy ジョブ（huggingface_hub を pip で導入 → HfApi で upload/restart）
  - concurrency で連続プッシュの競合を抑制（任意）
- 秘密情報の正当性確認
  - HF_TOKEN が Write 権限か
  - HF_SPACE_ID の形式（username/space-name）に誤りがないか
- 運用上の注意
  - README フロントマターは Space の検証対象。許容値・必須項目を守る
  - アップロード対象から .git/.github 等は除外し、README.md は含める

## 付録：最小フロントマター例（動作確認済みの形）

```markdown
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
```

## 付録：確認チェックリスト

- [ ] HF_TOKEN（Write）/ HF_SPACE_ID を Secrets に設定済み
- [ ] README.md のフロントマターが有効（許容色を使用 or 色指定を削除）
- [ ] deploy.yml は HfApi 方式で README.md を含めてアップロード
- [ ] Actions が成功し、Space Logs にエラーなし
- [ ] UI 表示、Basic/Gradient/Aurora と Emission の出力確認済み
- [ ] 必要なら requirements.txt から ruff/black を外してビルド短縮（任意）