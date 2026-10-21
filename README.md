# pixel-measure-design-coding

> Tiếng Việt: [README.vi.md](README.vi.md)

Claude Code 用スキル。デザイン画像（PC＋SP）から HTML/SCSS をコーディングし、**デザインとほぼ 100% 一致**
させたうえで、**目視ではなく数値で検証**します。

Claude がスクリプトでピクセルを計測し（font-size、line-height、余白、色、角丸）、プロジェクトの規約に沿って
コーディング → Chrome で実装結果をキャプチャ → デザインと自動比較 → ズレが 3px 以内になるまで修正します。
最後に HTML/CSS・レスポンシブ・リンクのチェックを行います。

## インストール（初回のみ）

```bash
# 1. スキルフォルダを Claude Code のスキル置き場へ配置
cp -R pixel-measure-design-coding ~/.claude/skills/

# 2. Python ライブラリ
pip3 install pillow numpy playwright
python3 -m playwright install chromium   # Google Chrome がインストール済みなら不要
```

確認：Claude Code で `/` を入力し、一覧に `pixel-measure-design-coding` が表示されれば OK です。

## 使い方

**デザインから新規コーディング**：VS Code でプロジェクトを開き、PC・SP のデザイン画像を添付してスキルを呼び出します。

```
/pixel-measure-design-coding 添付デザインの通りに index.html をコーディングしてください（PC 1440 / SP 375）
```

上記のようにスキル名を明示してください。「この画像をコーディングして」だけだと、検証工程のない別スキルが
選ばれることがあります。

**コーディング済みページのチェック**：

```
/pixel-measure-design-coding index.html をこのデザインと比較して、ズレている箇所を一覧にしてください
```

**修正依頼**：具体的なほど修正回数が減ります。

```
[ページ] index.html  [画面幅] SP 375  [セクション] お知らせ
[現状] 見出し → リスト ~40px   [デザイン] 24px
[範囲] SP のみ。PC は変更しない
```

Claude は結果を数値の表（セクションごとのズレ、audit のエラー数）で報告します。数値が出ていなければ完了とみなさないでください。

## デザイン画像の準備

- XD/Figma から書き出したフルページ PNG（**@1x / @2x どちらでも可**、スクリプトが自動判定）。
- PC・SP の両方。調整依頼書などで修正がある場合は**最新版**を渡してください。
- hover・アニメーション・スライダーがある場合は、画像または指示メモを添付してください。

## 構成

| ファイル | 役割 |
|---|---|
| `SKILL.md` | Claude が従う手順（8 ステップ） |
| `references/measurement-rules.md` | ピクセルから font-size / line-height / 余白を算出する計算式 |
| `references/lessons.md` | **実案件のミスから作ったルール集**（ID `L-xxx-nn`、随時追加） |
| `scripts/measure.py`, `sections.py`, `colors.py`, `radius.py`, `slice.py`, `crop_assets.py` | デザインの計測・画像切り出し |
| `scripts/shot.py` | 実装ページのキャプチャ（スクロールしてフェードインを表示、フォント読み込み待ち、スライダー停止） |
| `scripts/pixeldiff.py` | デザイン ↔ 実装の自動比較、ヒートマップ出力 |
| `scripts/audit.py` | HTML・レスポンシブ（横スクロール）・リンク切れ／画像切れ・フォント・JS エラーのチェック |
| `scripts/metrics.py` | 作業時間・修正ループ回数・修正依頼回数の記録（データは各自の PC にのみ保存） |
| `scripts/rects.py`, `rowcmp.py` | ブロックごとの座標・テキスト行ごとのデザイン比較（共通ヘッダー・KV がデザインと異なる場合） |
| `CHANGELOG.md`, `scripts/changelog.py` | スキルの更新履歴：変更内容・理由・更新前後の比較（本文はベトナム語） |

スクリプトは単体でも使えます。例：ページのエラーチェックだけ行う場合

```bash
python3 ~/.claude/skills/pixel-measure-design-coding/scripts/audit.py index.html
```

注：`SKILL.md`・`lessons.md` およびスクリプトの出力メッセージはベトナム語です。Claude はそのまま理解するため、
利用時に問題はありません。

## フィードバック・ルールの追加

Claude が同じミスを繰り返す場合や、スキルで検出できないミスがあった場合は、**メンテナーへ連絡**してください
（ミスの内容、スクリーンショット、正しい修正方法を添えて）。共有版を直接編集しないでください。
内容に応じて、次のバージョンで `lessons.md` に追加するか、`audit.py` の自動チェックに組み込みます。

スキルに含めないもの：クライアント名、デザイン画像、プロジェクトのパス、ページの内容。
案件ごとのルールは、その案件の memory / CLAUDE.md に記載してください。

- メンテナー：ロン
- バージョンと各更新の内容：`CHANGELOG.md` を参照
