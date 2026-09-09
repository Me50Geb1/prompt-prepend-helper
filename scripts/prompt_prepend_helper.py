import inspect
import re

import gradio as gr
from modules import scripts
from modules.scripts import OnComponent


class PromptPrependHelper(scripts.Script):
    # Run after ordinary always-on prompt scripts (TIPO etc.).
    sorting_priority = 9999

    def __init__(self):
        super().__init__()
        self.prompt_area = [None, None]
        self.on_after_component_elem_id = [
            ("txt2img_prompt", lambda x: self._set_prompt_area(0, x)),
            ("img2img_prompt", lambda x: self._set_prompt_area(1, x)),
        ]

    def _set_prompt_area(self, idx: int, component: OnComponent):
        self.prompt_area[idx] = component.component

    def title(self):
        return "Prompt Prepend Helper"

    def show(self, _):
        return scripts.AlwaysVisible

    @staticmethod
    def _merge(extra: str, original: str) -> str:
        extra = (extra or "").strip().strip(",")
        original = (original or "").strip()
        if not extra:
            return original
        if not original:
            return extra
        return f"{extra}, {original}"


    @staticmethod
    def _split_top_level_commas(text: str):
        """Split comma-separated prompt tags while respecting (), [], {} and <> blocks."""
        text = text or ""
        parts = []
        buf = []
        depth = {"(": 0, "[": 0, "{": 0, "<": 0}
        pairs = {")": "(", "]": "[", "}": "{", ">": "<"}
        for ch in text:
            if ch in depth:
                depth[ch] += 1
            elif ch in pairs and depth[pairs[ch]] > 0:
                depth[pairs[ch]] -= 1
            if ch == "," and not any(depth.values()):
                part = "".join(buf).strip()
                if part:
                    parts.append(part)
                buf = []
            else:
                buf.append(ch)
        part = "".join(buf).strip()
        if part:
            parts.append(part)
        return parts

    @staticmethod
    def _looks_like_natural_language(segment: str) -> bool:
        """Conservative heuristic: do not dedupe sentence-like chunks."""
        s = (segment or "").strip()
        if not s:
            return False
        # Explicit sentence punctuation strongly suggests prose.
        if re.search(r"[.!?。！？]", s):
            return True
        # Line breaks often indicate prose paragraphs rather than Danbooru-style tags.
        if "\n" in s or "\r" in s:
            return True
        # Long space-separated phrases are likely natural language.
        words = [w for w in re.split(r"\s+", s) if w]
        if len(words) >= 8:
            return True
        return False

    @staticmethod
    def _normalize_tag(segment: str) -> str:
        """Normalize exact tag spellings only; never perform substring matching."""
        s = (segment or "").strip()
        if not s:
            return ""

        # Strip common A1111 attention wrappers while preserving the tag itself.
        weighted = re.compile(r"^\((.*?):\s*[-+]?\d*\.?\d+\)$")
        m = weighted.match(s)
        while m:
            s = m.group(1).strip()
            m = weighted.match(s)

        # Simple unmatched emphasis parentheses/brackets are also ignored for comparison.
        if len(s) >= 2 and ((s[0], s[-1]) in (("(", ")"), ("[", "]"))):
            s = s[1:-1].strip()

        s = s.replace("\\(", "(").replace("\\)", ")")
        s = s.replace("_", " ")
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    @classmethod
    def _dedupe_prompts(cls, extra_prompt: str, native_prompt: str):
        """Remove exact duplicate tags, deleting from native prompt first.

        Natural-language-like chunks are deliberately ignored.
        """
        extra_parts = cls._split_top_level_commas(extra_prompt)
        native_parts = cls._split_top_level_commas(native_prompt)

        removed_extra = 0
        removed_native = 0

        # First dedupe within the extra field itself, keeping the earliest tag.
        extra_seen = set()
        extra_kept = []
        for part in extra_parts:
            if cls._looks_like_natural_language(part):
                extra_kept.append(part)
                continue
            key = cls._normalize_tag(part)
            if key and key in extra_seen:
                removed_extra += 1
                continue
            if key:
                extra_seen.add(key)
            extra_kept.append(part)

        # Native/initial prompt loses cross-field duplicates first, per user preference.
        native_seen = set()
        native_kept = []
        for part in native_parts:
            if cls._looks_like_natural_language(part):
                native_kept.append(part)
                continue
            key = cls._normalize_tag(part)
            if key and key in extra_seen:
                removed_native += 1
                continue
            if key and key in native_seen:
                removed_native += 1
                continue
            if key:
                native_seen.add(key)
            native_kept.append(part)

        new_extra = ", ".join(extra_kept)
        new_native = ", ".join(native_kept)
        total = removed_extra + removed_native
        if total:
            status = (
                f"重複タグを {total} 件削除しました "
                f"（追加Prompt: {removed_extra} / 既存Positive: {removed_native}）。"
            )
        else:
            status = "重複タグは見つかりませんでした。"
        return new_extra, new_native, status

    @staticmethod
    def _clear_positive():
        return ""

    @staticmethod
    def _save_positive_as_style(style_name: str, prompt: str):
        """Save only the current positive prompt as a WebUI style."""
        name = (style_name or "").strip()
        positive = (prompt or "").strip()

        if not name:
            return "Style名を入力してください。"
        if not positive:
            return "既存Positive Promptが空なので登録しませんでした。"

        try:
            import modules.shared as shared
            from modules import styles

            db = getattr(shared, "prompt_styles", None)
            if db is None:
                return "Styleデータベースがまだ初期化されていません。"

            # Reload from disk immediately before registration so a stale
            # in-memory style database cannot overwrite edits made by Styles Editor
            # or another extension.
            reload_fn = getattr(db, "reload", None)
            if callable(reload_fn):
                reload_fn()

            existing = getattr(db, "styles", {}).get(name)
            if existing is not None:
                return f"Style「{name}」は既に存在します。別の名前を指定してください。"

            # Save Positive only. Negative stays empty. Forge Neo supports
            # multiple style files, so assign the same authoritative default
            # path that its StyleDatabase uses for newly created styles.
            default_path = getattr(db, "default_path", None)
            style_path = str(default_path) if default_path is not None else None
            try:
                style = styles.PromptStyle(name, positive, "", style_path)
            except TypeError:
                style = styles.PromptStyle(name, positive, "")

            db.styles[name] = style
            db.save_styles()

            # Confirm the persisted file can be read back before reporting
            # success. This also keeps the live Neo database synchronized.
            if callable(reload_fn):
                reload_fn()
            if getattr(db, "styles", {}).get(name) is None:
                return f"Style「{name}」を保存しましたが、再読み込みで確認できませんでした。"
            return f"Style「{name}」を登録しました（Positiveのみ / Negativeは空欄）。"
        except Exception as e:
            return f"Style登録に失敗しました: {e}"

    def ui(self, is_img2img):
        tab = "img2img" if is_img2img else "txt2img"
        native_prompt = self.prompt_area[is_img2img]

        # Extra Prompt stays in the main prompt column.
        with gr.Group(
            elem_id=f"{tab}_prompt_prepend_extra_panel",
            elem_classes=["prompt-prepend-extra-panel"],
        ):
            extra_prompt = gr.Textbox(
                label="追加Prompt",
                lines=2,
                placeholder="生成時だけ既存Positive Promptの先頭に追加されます",
                elem_id=f"{tab}_prompt_prepend_text",
                elem_classes=["prompt-prepend-text"],
            )

        # Operation controls are moved by JavaScript to the right-side Generate column.
        with gr.Group(
            elem_id=f"{tab}_prompt_prepend_controls",
            elem_classes=["prompt-prepend-controls"],
        ):
            send_enabled = gr.Checkbox(
                label="追加Promptを生成へ送信",
                value=True,
                elem_id=f"{tab}_prompt_prepend_enabled",
            )
            clear_positive_btn = gr.Button(
                value="既存Positiveをクリア",
                elem_id=f"{tab}_prompt_prepend_clear_positive",
                size="sm",
            )
            dedupe_btn = gr.Button(
                value="重複タグを削除",
                elem_id=f"{tab}_prompt_prepend_dedupe",
                size="sm",
            )
            dedupe_status = gr.Markdown(
                "",
                elem_id=f"{tab}_prompt_prepend_dedupe_status",
            )
            style_name = gr.Textbox(
                label="Style名",
                placeholder="名前を入力",
                elem_id=f"{tab}_prompt_prepend_style_name",
                lines=1,
            )
            save_style_btn = gr.Button(
                value="既存PositiveをStyle登録",
                elem_id=f"{tab}_prompt_prepend_save_style",
                size="sm",
            )
            style_status = gr.Markdown(
                "",
                elem_id=f"{tab}_prompt_prepend_style_status",
            )

        if native_prompt is not None:
            clear_positive_btn.click(
                fn=self._clear_positive,
                inputs=[],
                outputs=[native_prompt],
                show_progress=False,
            )

            dedupe_btn.click(
                fn=self._dedupe_prompts,
                inputs=[extra_prompt, native_prompt],
                outputs=[extra_prompt, native_prompt, dedupe_status],
                show_progress=False,
            )

            save_style_event = save_style_btn.click(
                fn=self._save_positive_as_style,
                inputs=[style_name, native_prompt],
                outputs=[style_status],
                show_progress=False,
            )
            save_style_event.then(
                fn=None,
                inputs=[style_status],
                outputs=[style_status],
                js="promptPrependHelperAfterStyleSave",
                show_progress=False,
            )
        else:
            style_status.value = "既存Positive Promptコンポーネントを取得できませんでした。"

        return [extra_prompt, send_enabled]

    def process(self, p, extra_prompt: str, send_enabled: bool):
        """Add the independent prompt after ordinary prompt extensions ran."""
        if not send_enabled:
            return
        if not extra_prompt or not extra_prompt.strip():
            return

        current_prompt = getattr(p, "prompt", "")
        current_all_prompts = list(getattr(p, "all_prompts", []) or [])
        current_hr_prompt = getattr(p, "hr_prompt", None)
        current_all_hr_prompts = list(getattr(p, "all_hr_prompts", []) or [])

        p.prompt = self._merge(extra_prompt, current_prompt)

        if current_all_prompts:
            p.all_prompts = [
                self._merge(extra_prompt, prompt) for prompt in current_all_prompts
            ]

        if current_hr_prompt is not None:
            p.hr_prompt = self._merge(extra_prompt, current_hr_prompt)

        if current_all_hr_prompts:
            p.all_hr_prompts = [
                self._merge(extra_prompt, prompt) for prompt in current_all_hr_prompts
            ]

        try:
            p.extra_generation_params["Additional Prompt"] = extra_prompt.strip()
        except Exception:
            pass
