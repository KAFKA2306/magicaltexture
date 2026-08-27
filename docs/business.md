# 制作者向け制作相談

`magicaltexture` の無料生成結果を基準に、VRChatアバター制作者・改変受託者向けの調整済み納品を相談できます。

## 対象

- 自分のアバター用に複数色の瞳差分を作りたい人
- 販売アバターへ同梱するカラーバリエーションを作りたい制作者
- 改変依頼で瞳・Emission差分を納品したい受託者

## 無料生成と制作相談の違い

無料Webアプリでは、元テクスチャとマスクから色・mode・明度保持・saturation・highlight・Aurora・Emission設定を自分で調整してPNG/ZIPを生成できます。

制作相談では、用途に合わせて次のような納品範囲を個別に決めます。

- アバター別の瞳色・Emission調整
- 販売アバター同梱向けの複数色セット
- ブランドカラーに合わせた専用パレット
- マスク作成を含む個別調整
- lilToon導入時に必要な設定情報

実際に公開されていない商品、販売件数、受注実績は表示しません。

## 依頼時に用意するもの

- 対象アバターまたは用途
- 元の瞳テクスチャ
- 変更したい範囲が分かるマスクまたは説明
- 希望する色、mode、Emissionの有無
- 希望する納品形式と時期（任意）

元テクスチャを継続保存することを前提にしません。依頼に必要な受け渡し方法は案件ごとに確認します。

## 権利条件

依頼者が、加工・納品・利用に必要な権利または許諾を持つ素材のみ対象です。購入アバターや購入テクスチャの利用規約は、`magicaltexture` の生成物や制作依頼によって上書きされません。再配布・販売・商用利用の可否は必ず元素材の規約に従ってください。

## 標準納品構成

案件に応じて不要な項目は省きます。

```text
main_texture.png
emission_mask.png      # 必要な場合のみ
preview.png
preset_manifest.json
liltoon-settings.md
LICENSE-or-TERMS.txt
```

Batch生成ZIPでは `preset_manifest.json` にpalette、mode、調整値、generator revision、入力SHA-256、出力SHA-256/sizeを記録します。

## 制作相談を始める

GitHub Issueで、対象アバター/用途、希望納品物、希望時期を記載してください。

https://github.com/KAFKA2306/magicaltexture/issues/new?title=%E5%88%B6%E4%BD%9C%E7%9B%B8%E8%AB%87

WebアプリのSingle/Batch生成後に表示されるリンクを使うと、generation type、mode、paletteも問い合わせ本文へ引き継がれます。
