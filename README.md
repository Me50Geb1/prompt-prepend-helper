# Prompt Prepend Helper

A prompt utility extension for **sd-webui-forge-neo**.

既存のPositive Promptとは独立した追加Prompt欄と、Prompt管理用の補助機能を追加します。

## Features

- 既存Positive Promptの上に追加Prompt欄を表示
- 生成時に追加Promptを既存Positive Promptへ前置きして送信
- 追加Promptの送信ON/OFF
- 既存Positive Promptのみをクリア
- Negative Promptは維持
- 既存Positive PromptをStyleとして登録
- Style登録時はNegative Promptを空欄として保存
- 追加Promptと既存Positive Promptの重複タグをチェック
- 重複タグは既存Positive Prompt側から削除
- アンダースコア、スペース、重み付きタグを考慮した重複判定
- LoRA直後にカンマなしで続くタグも重複判定
- 自然言語と思われる文章は重複タグ処理から除外
- txt2img / img2img対応

## Purpose

Z-TipoなどのPrompt加工拡張には従来のPositive Promptだけを処理させつつ、
固定タグや共通Promptなどを別欄で管理するための拡張です。

追加Promptは生成直前に既存Positive Promptへ前置きされます。

これにより、他のPrompt加工拡張の処理対象と追加Promptを分離できます。

## Installation

以下のリポジトリを `sd-webui-forge-neo/extensions/` にCloneします。

    git clone https://github.com/Me50Geb1/prompt-prepend-helper.git

配置例:

    sd-webui-forge-neo/
    └─ extensions/
       └─ prompt-prepend-helper/
          ├─ javascript/
          ├─ scripts/
          ├─ README.md
          └─ style.css

インストール後、Forge Neoを再起動してください。

## Usage

### Additional Prompt

追加Prompt欄に、生成時に常に前置きしたいPromptを入力します。

例:

    masterpiece, best quality

既存Positive Prompt:

    1girl, outdoors, smile

生成時:

    masterpiece, best quality, 1girl, outdoors, smile

### Enable / Disable

追加Promptを生成時に使用するかON/OFFできます。

OFFにした場合、追加Prompt欄の内容は保持したまま生成Promptには追加されません。

### Duplicate Tag Check

追加Promptと既存Positive Promptを比較し、重複するタグを整理できます。

以下のような表記差も重複として扱います。

    blue_hair
    blue hair
    (blue hair:1.2)

重複した場合は追加Prompt側を維持し、既存Positive Prompt側から重複タグを削除します。

### Style Registration

現在の既存Positive PromptをForge NeoのStyleとして登録できます。

Negative Promptは登録しません。

既に同じ名前のStyleが存在する場合は上書きしません。

登録に成功すると、Forge Neoのtxt2img / img2imgのStyle候補を更新します。
Styles Editor Neoを併用している場合は、Style Editorの一覧も自動で再読み込みされます。

## Compatibility

Main target:

- sd-webui-forge-neo

Designed to coexist with prompt-related extensions such as:

- Z-Tipo
- Civitai Helper
- LoRA Prompt Tool
- Forge Neo Styles

## Notes

This extension changes prompt handling only.

It does not modify model files, LoRA files, or generation models.

This extension was created with the assistance of ChatGPT.

The repository owner may not be able to answer technical questions, provide support, or respond to implementation-related inquiries.

この拡張はChatGPTの支援により作成されています。

リポジトリ所有者は技術的な質問、サポート、実装に関する問い合わせには対応できない場合があります。

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
