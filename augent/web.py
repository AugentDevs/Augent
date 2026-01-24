"""
Augent Web UI - Gradio interface with live transcription streaming
"""

import json
import os
import re
import gradio as gr
from typing import Generator, Tuple

from .cache import get_model_cache, get_transcription_cache
from .search import KeywordSearcher


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

/* ============================================
   CSS VARIABLES - Override Gradio defaults
   ============================================ */

:root, * {
    --color-accent: #00F060 !important;
    --color-accent-soft: #003020 !important;
    --background-fill-primary: #000 !important;
    --background-fill-secondary: #000 !important;
    --border-color-primary: #00F060 !important;
    --border-color-accent: #00F060 !important;
    --body-text-color: #00F060 !important;
    --block-background-fill: #000 !important;
    --block-border-color: #00F060 !important;
    --input-background-fill: #000 !important;
    --button-primary-background-fill: #00F060 !important;
    --button-primary-text-color: #000 !important;
    --button-secondary-background-fill: #000 !important;
    --button-secondary-text-color: #00F060 !important;
    --neutral-900: #000 !important;
    --neutral-800: #001a0d !important;
    --neutral-700: #002a15 !important;
    --primary-500: #00F060 !important;
    --primary-600: #00D050 !important;
    --secondary-500: #00F060 !important;
}

/* ============================================
   GLOBAL RESET - Force black/green everywhere
   ============================================ */

* {
    font-family: 'Montserrat', sans-serif !important;
    color: #00F060 !important;
    border-color: #00F060 !important;
}

html, body {
    background: #000 !important;
}

/* Every single div, section, container - black background */
div, section, main, aside, header, nav, article,
form, fieldset, label, span, p, h1, h2, h3, h4, h5, h6 {
    background: #000 !important;
    background-color: #000 !important;
}

/* Gradio specific containers */
.gradio-container,
.gradio-container *,
.main,
.wrap,
.contain,
.app,
.block,
.form,
.panel,
[class*="block"],
[class*="container"],
[class*="wrapper"],
[class*="panel"],
[class*="group"],
[class*="box"] {
    background: #000 !important;
    background-color: #000 !important;
}

/* ============================================
   HIDE ALL SCROLLBARS GLOBALLY
   (except explicitly allowed ones)
   ============================================ */

*::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    background: transparent !important;
}

* {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}

/* ============================================
   AUDIO COMPONENT - Kill that scrollbar
   ============================================ */

/* Target by component type */
[data-testid="audio"],
[data-testid="waveform"],
.audio-container,
.waveform-container {
    overflow: hidden !important;
    background: #000 !important;
}

/* WaveSurfer specific elements */
wave,
.wavesurfer-region,
[class*="wavesurfer"],
[class*="waveform"],
[class*="audio"] {
    overflow: hidden !important;
    background: #000 !important;
}

/* Any element inside audio that might scroll */
[data-testid="audio"] *,
[data-testid="waveform"] *,
.audio-container *,
.waveform-container * {
    overflow: hidden !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    background: #000 !important;
}

[data-testid="audio"] *::-webkit-scrollbar,
[data-testid="waveform"] *::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}

/* Canvas elements - green tint */
canvas {
    filter: hue-rotate(85deg) saturate(3) brightness(1.5) !important;
}

/* ============================================
   BUTTONS - Default: black bg with green content
   ============================================ */

button,
.btn,
[role="button"],
input[type="button"],
input[type="submit"] {
    background: #000 !important;
    background-color: #000 !important;
    color: #00F060 !important;
    border: 1px solid #00F060 !important;
}

/* Content inside default buttons - green */
button *,
.btn *,
[role="button"] *,
button span,
button svg,
button path,
button i,
button div {
    color: #00F060 !important;
    fill: #00F060 !important;
    stroke: #00F060 !important;
    background: transparent !important;
}

/* SVG icons - green */
svg {
    fill: #00F060 !important;
    stroke: #00F060 !important;
}

/* PRIMARY BUTTON ONLY - Green bg with black content */
.primary-btn,
button.primary,
[class*="primary"],
.lg[class*="primary"],
button[variant="primary"] {
    background: #00F060 !important;
    background-color: #00F060 !important;
    color: #000 !important;
    border: none !important;
}

.primary-btn *,
button.primary *,
[class*="primary"] *,
[class*="primary"] span,
[class*="primary"] svg {
    color: #000 !important;
    fill: #000 !important;
    stroke: #000 !important;
}

/* Hide undo button in audio player - target parent button */
button:has(svg[aria-label="undo"]),
button:has([aria-label="undo"]) {
    display: none !important;
}

/* Fallback: hide the SVG itself */
svg[aria-label="undo"] {
    display: none !important;
}

/* Audio control buttons - black bg with green icons */
[data-testid="audio"] button,
[data-testid="audio"] [role="button"],
[class*="audio"] button,
[class*="Audio"] button {
    background: #000 !important;
    background-color: #000 !important;
    color: #00F060 !important;
    border: 1px solid #00F060 !important;
}


[data-testid="audio"] button *,
[data-testid="audio"] button svg,
[data-testid="audio"] button svg *,
[data-testid="audio"] [role="button"] *,
[class*="audio"] button *,
[class*="audio"] button svg,
[class*="audio"] button svg *,
[class*="Audio"] button *,
[class*="Audio"] button svg * {
    fill: #00F060 !important;
    stroke: #00F060 !important;
    color: #00F060 !important;
    background: transparent !important;
}

/* Upload/dropzone area */
[data-testid="dropzone"],
[class*="upload"],
[class*="Upload"],
[class*="drop"],
[class*="Drop"] {
    background: #000 !important;
    background-color: #000 !important;
}

/* Everything in upload area - transparent bg, green content */
[data-testid="dropzone"] *,
[class*="upload"] *,
[class*="Upload"] * {
    background: transparent !important;
    background-color: transparent !important;
    color: #00F060 !important;
    fill: #00F060 !important;
    stroke: #00F060 !important;
}

/* Tab buttons - special case: black bg with green text when not selected */
button[role="tab"] {
    background: #000 !important;
    color: #00F060 !important;
    border: 1px solid #00F060 !important;
}

button[role="tab"] * {
    color: #00F060 !important;
    fill: #00F060 !important;
}

button[role="tab"][aria-selected="true"] {
    background: #00F060 !important;
    color: #000 !important;
}

button[role="tab"][aria-selected="true"] * {
    color: #000 !important;
    fill: #000 !important;
}

/* Tab indicator line - remove orange, make green */
[class*="tab"] [class*="indicator"],
[class*="tab"] [class*="selected"],
[class*="Tab"] [class*="indicator"],
[role="tablist"]::after,
[role="tablist"] *::after,
.tabs > div,
[class*="tablist"] > div,
.tab-nav,
.tab-nav * {
    background: #00F060 !important;
    background-color: #00F060 !important;
    border-color: #00F060 !important;
}

/* Specifically target the orange indicator bar */
[role="tablist"] + div,
[role="tablist"] ~ div:not([role="tabpanel"]),
.tabs .tabitem,
.tab-nav .selected,
div[class*="border-b"],
div[class*="border-bottom"] {
    border-color: #00F060 !important;
    border-bottom-color: #00F060 !important;
}

/* Any element with inline orange style */
*[style*="rgb(249"] {
    background: #00F060 !important;
}

*[style*="rgb(251"] {
    background: #00F060 !important;
}

*[style*="#f"] {
    background: #00F060 !important;
}

/* Override any accent/orange colors */
[style*="orange"],
[style*="accent"] {
    background: #00F060 !important;
    border-color: #00F060 !important;
    color: #00F060 !important;
}

/* ============================================
   INPUTS - Black bg, green text/border
   ============================================ */

input,
textarea,
select,
[contenteditable] {
    background: #000 !important;
    background-color: #000 !important;
    color: #00F060 !important;
    border: 1px solid #00F060 !important;
    caret-color: #00F060 !important;
}

input::placeholder,
textarea::placeholder {
    color: #006830 !important;
    opacity: 1 !important;
}

/* Dropdown/Select styling */
select option,
[role="listbox"],
[role="listbox"] *,
[role="option"],
ul[role="listbox"],
ul[role="listbox"] li,
.dropdown,
.dropdown * {
    background: #000 !important;
    background-color: #000 !important;
    color: #00F060 !important;
}

/* ============================================
   LOG OUTPUT - Terminal style with visible scrollbar
   ============================================ */

.log-output textarea {
    background: #000 !important;
    color: #00F060 !important;
    font-family: 'Monaco', 'Menlo', monospace !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    border: 1px solid #00F060 !important;
    overflow-y: scroll !important;
    scrollbar-width: thin !important;
    scrollbar-color: #00F060 #000 !important;
}

.log-output textarea::-webkit-scrollbar {
    display: block !important;
    width: 10px !important;
}

.log-output textarea::-webkit-scrollbar-track {
    background: #001a0d !important;
}

.log-output textarea::-webkit-scrollbar-thumb {
    background: #00F060 !important;
    border-radius: 5px !important;
}

/* ============================================
   CODE BLOCKS
   ============================================ */

pre,
code,
.code,
[class*="code"] {
    background: #000 !important;
    color: #00F060 !important;
    border: 1px solid #00F060 !important;
}

/* ============================================
   LABELS AND TEXT
   ============================================ */

label,
.label,
span,
p,
h1, h2, h3, h4, h5, h6,
.info,
[class*="info"],
[class*="label"] {
    color: #00F060 !important;
    background: transparent !important;
}

/* Subtle/secondary text */
.secondary,
.subtle,
.muted,
small,
.info {
    color: #00A040 !important;
}

/* ============================================
   BORDERS - All green, minimal
   ============================================ */

[class*="border"],
.block,
.panel {
    border-color: #00F060 !important;
}

/* Remove excessive outlines */
*:focus {
    outline: 1px solid #00F060 !important;
    outline-offset: 0 !important;
}

/* ============================================
   MISC CLEANUP
   ============================================ */

/* Hide footer */
footer {
    display: none !important;
}

/* Links */
a {
    color: #00FF60 !important;
}

a:hover {
    color: #00FF90 !important;
}

/* Progress bars */
progress,
.progress,
[role="progressbar"] {
    background: #000 !important;
}

progress::-webkit-progress-bar {
    background: #000 !important;
}

progress::-webkit-progress-value {
    background: #00F060 !important;
}

/* Sliders/Range inputs */
input[type="range"] {
    background: transparent !important;
}

input[type="range"]::-webkit-slider-track {
    background: #003020 !important;
}

input[type="range"]::-webkit-slider-thumb {
    background: #00F060 !important;
}

/* Hover states - subtle highlight */
button:hover,
[role="button"]:hover {
    background: #001a0d !important;
}

/* Primary button hover */
.primary-btn:hover,
[class*="primary"]:hover {
    background: #00D050 !important;
}

button[role="tab"]:hover:not([aria-selected="true"]) {
    background: #001a0d !important;
}

/* Selection highlight */
::selection {
    background: #00F060 !important;
    color: #000 !important;
}

/* KILL THE FADE OVERLAY */
.scroll-fade,
div.scroll-fade,
.gradio-container .scroll-fade,
[class*="scroll-fade"],
[class*="ScrollFade"],
[class*="scrollfade"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    width: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    position: absolute !important;
    z-index: -9999 !important;
}

/* Kill any linear gradient overlays */
*[style*="linear-gradient"] {
    background: none !important;
    background-image: none !important;
}

/* Kill progress/loading animations */
.progress-bar,
.progress,
[class*="progress"],
[class*="loading"],
[class*="spinner"],
.eta-bar,
[class*="eta"] {
    display: none !important;
    opacity: 0 !important;
}
"""


def format_time(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def highlight_keyword_in_snippet(snippet: str, keyword: str) -> str:
    clean_snippet = snippet.replace("...", "").strip()
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f"<strong style='color:#00FF00;'>{keyword}</strong>", clean_snippet)


def search_audio_streaming(
    audio_path: str,
    keywords_str: str,
    model_size: str
) -> Generator[Tuple[str, str, str], None, None]:
    if not audio_path:
        yield "", "{}", "<p style='color:#00F060;'>Upload an audio file to begin</p>"
        return

    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
    if not keywords:
        yield "", "{}", "<p style='color:#00F060;'>Enter keywords separated by commas</p>"
        return

    filename = os.path.basename(audio_path)
    log_lines = []
    log_lines.append("─" * 45)
    log_lines.append(f"  [augent] file: {filename}")
    log_lines.append(f"  [augent] keywords: {', '.join(keywords)}")
    log_lines.append(f"  [augent] model: {model_size}")
    log_lines.append("─" * 45)

    yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Starting...</p>"

    cache = get_transcription_cache()
    cached = cache.get(audio_path, model_size)

    if cached:
        log_lines.append(f"  [cache] loaded from cache")
        log_lines.append(f"  [info] duration: {format_time(cached.duration)}")
        log_lines.append("")
        yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Loaded from cache</p>"

        all_words = cached.words
        duration = cached.duration

    else:
        log_lines.append(f"  [model] loading {model_size}...")
        yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Loading model...</p>"

        model_cache = get_model_cache()
        model = model_cache.get(model_size)

        log_lines.append(f"  [model] ready")
        log_lines.append("")
        yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Transcribing...</p>"

        segments_gen, info = model.transcribe(
            audio_path,
            word_timestamps=True,
            vad_filter=True
        )

        duration = info.duration
        all_words = []
        segments = []

        log_lines.append(f"  [info] duration: {format_time(duration)}")
        log_lines.append(f"  [info] language: {info.language}")
        log_lines.append("")

        for segment in segments_gen:
            segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })

            ts = format_time(segment.start)
            log_lines.append(f"  [{ts}] {segment.text.strip()}")

            if segment.words:
                for word in segment.words:
                    all_words.append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end
                    })
                    clean = word.word.lower().strip(".,!?;:'\"")
                    for kw in keywords:
                        if kw in clean:
                            log_lines.append(f"         >> match: '{kw}' @ {format_time(word.start)}")

            yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Transcribing...</p>"

        cache.set(audio_path, model_size, {
            "text": " ".join(s["text"].strip() for s in segments),
            "language": info.language,
            "duration": duration,
            "segments": segments,
            "words": all_words
        })

    log_lines.append("")
    log_lines.append("  [search] finding matches...")
    yield "\n".join(log_lines), "{}", "<p style='color:#00F060;'>Searching...</p>"

    searcher = KeywordSearcher(context_words=11, enable_fuzzy=False)
    matches = searcher.search(all_words, keywords, include_fuzzy=False)

    grouped = {}
    for m in matches:
        kw = m.keyword
        if kw not in grouped:
            grouped[kw] = []
        grouped[kw].append({
            "timestamp": m.timestamp,
            "timestamp_seconds": m.timestamp_seconds,
            "snippet": m.snippet
        })

    log_lines.append("")
    log_lines.append("─" * 45)
    log_lines.append(f"  [done] {len(matches)} matches found")
    for kw in grouped:
        log_lines.append(f"         {kw}: {len(grouped[kw])}")
    log_lines.append("─" * 45)

    results_json = json.dumps(grouped, indent=2)

    html_parts = []
    html_parts.append("<div style='font-family:Montserrat,sans-serif;color:#00F060;'>")
    html_parts.append(f"<h3 style='color:#00F060;margin-bottom:16px;'>Found {len(matches)} matches</h3>")

    if len(matches) == 0:
        html_parts.append("<p>No matches found.</p>")
    else:
        for kw, kw_matches in grouped.items():
            html_parts.append(f"<h4 style='color:#00FF00;margin:16px 0 8px;'>{kw} ({len(kw_matches)})</h4>")
            html_parts.append("<table style='width:100%;border-collapse:collapse;'>")
            html_parts.append("<tr><th style='text-align:left;padding:8px;border-bottom:1px solid #00F060;width:80px;color:#00F060;'>Time</th>")
            html_parts.append("<th style='text-align:left;padding:8px;border-bottom:1px solid #00F060;color:#00F060;'>Context</th></tr>")

            for m in kw_matches:
                ts = m["timestamp"]
                snippet_html = highlight_keyword_in_snippet(m["snippet"], kw)

                html_parts.append(f"""<tr>
                    <td style='padding:8px;border-bottom:1px solid #002010;color:#00F060;font-family:Monaco,monospace;'>{ts}</td>
                    <td style='padding:8px;border-bottom:1px solid #002010;color:#00F060;'>{snippet_html}</td>
                </tr>""")

            html_parts.append("</table>")

    html_parts.append("</div>")

    yield "\n".join(log_lines), results_json, "\n".join(html_parts)


def create_demo() -> gr.Blocks:
    with gr.Blocks(
        title="Augent Web UI",
        analytics_enabled=False
    ) as demo:
        gr.Markdown("# Augent")

        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(
                    type="filepath",
                    label="Audio File",
                    sources=["upload"],
                    waveform_options=gr.WaveformOptions(
                        waveform_color="#00F060",
                        waveform_progress_color="#00FF90"
                    )
                )

                keywords_input = gr.Textbox(
                    label="Keywords",
                    placeholder="wormhole, hourglass, CLI",
                    info="Comma-separated"
                )

                model_dropdown = gr.Dropdown(
                    choices=["tiny", "base", "small", "medium", "large"],
                    value="tiny",
                    label="Model",
                    info="Larger = slower but more accurate"
                )

                search_btn = gr.Button("SEARCH", variant="primary", size="lg", elem_classes=["primary-btn"])

                gr.Markdown("""
---
**Tips:**
- Larger models = more accurate
- Results cached for repeat searches
                """)

            with gr.Column(scale=2):
                log_output = gr.Textbox(
                    label="Live Log",
                    lines=25,
                    max_lines=25,
                    autoscroll=True,
                    elem_classes=["log-output"]
                )

                # ALWAYS force scroll to bottom
                gr.HTML("""<script>
setInterval(function() {
    var ta = document.querySelector('.log-output textarea');
    if (ta) ta.scrollTop = ta.scrollHeight;
}, 50);
</script>""")


                with gr.Tabs():
                    with gr.TabItem("Results"):
                        results_html = gr.HTML(
                            value="<p style='color:#00F060;'>Upload audio and enter keywords</p>"
                        )
                    with gr.TabItem("JSON"):
                        results_json = gr.Code(language="json", lines=15)

        search_btn.click(
            fn=search_audio_streaming,
            inputs=[audio_input, keywords_input, model_dropdown],
            outputs=[log_output, results_json, results_html],
            show_progress="hidden"
        )

        gr.Markdown("---\n**Augent**")

    return demo


demo = create_demo()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Augent Web UI")
    parser.add_argument("--port", "-p", type=int, default=8888, help="Port to run on (default: 8888)")
    parser.add_argument("--share", action="store_true", help="Create public Gradio link")
    args = parser.parse_args()

    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        css=CUSTOM_CSS
    )


if __name__ == "__main__":
    main()
