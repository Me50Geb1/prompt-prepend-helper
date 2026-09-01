# Prompt Prepend Helper v6

Forge Neo向け独立拡張。

- 既存Positive Promptの上に「追加Prompt」欄を表示
- Generate時だけ「追加Prompt + 既存Positive」で生成
- 追加Prompt送信 ON/OFF
- 既存Positiveのみクリア（Negativeは維持）
- 既存PositiveのみをStyle登録（Negativeは空欄）
- 追加Prompt＋既存Positiveを対象にした「重複タグを削除」
  - 重複時は既存Positive側から優先して削除
  - `blue_hair` / `blue hair` / `(blue hair:1.2)` は同一タグとして比較
  - 自然言語らしい文章は重複判定から除外
  - 単語の部分一致は行わない
- 操作系はGenerateボタン右側カラム下部へ配置


## v7 Style registration safety
- Registering a style reloads the WebUI style database from disk first.
- It does not auto-refresh txt2img/img2img style UI.
- Existing style names are not overwritten.
- Only Positive is saved; Negative is empty.
