#!/usr/bin/env python3
"""Render docs/*.md into a static HTML site for GitHub Pages.

Usage: render_docs.py DOCS_DIR OUT_DIR [--base /iamavirus/docs/]

Each Markdown page becomes OUT_DIR/<name>.html wrapped in a shared template with a
navigation sidebar. The page order and titles come from docs/_nav.txt (one
"name: Title" per line). Fenced ```mermaid blocks render with mermaid.js.
Requires the `markdown` package (pip install markdown).
"""
import argparse
import html
import os
import re
import sys

import markdown

EXTENSIONS = ["tables", "fenced_code", "toc", "attr_list", "md_in_html", "sane_lists"]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{description}">
<title>{title} — IAmAVirus docs</title>
<style>
:root{{--bg:#ffffff;--ink:#242424;--muted:#5f5d58;--line:#e6e5e1;--side:#fafaf9;--soft:#f3f2ef;--accent:#2d5be3;--code:#f6f5f2;--serif:Georgia,"Times New Roman",serif;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161615;--ink:#e8e6e1;--muted:#b3b0a8;--line:#2e2d2b;--side:#1c1c1b;--soft:#262523;--accent:#8fb0ff;--code:#202020;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#161615;--ink:#e8e6e1;--muted:#b3b0a8;--line:#2e2d2b;--side:#1c1c1b;--soft:#262523;--accent:#8fb0ff;--code:#202020;color-scheme:dark}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.sidebar{{position:fixed;inset:0 auto 0 0;width:240px;background:var(--side);border-right:1px solid var(--line);padding:26px 18px;overflow:auto}}
.sidebar .brand{{font-family:var(--serif);font-size:19px;margin:0 0 4px}}
.sidebar .sub{{color:var(--muted);font-size:12px;margin:0 0 18px}}
.sidebar a{{display:block;color:var(--ink);text-decoration:none;padding:6px 8px;border-radius:8px;font-size:14px}}
.sidebar a:hover{{background:var(--soft)}}.sidebar a.current{{background:var(--soft);font-weight:600}}
.sidebar .ext{{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}}
.sidebar .ext a{{color:var(--muted);font-size:13px}}
main{{margin-left:240px;padding:40px 48px 80px;max-width:980px}}
h1{{font-family:var(--serif);font-weight:400;font-size:34px;line-height:1.15;margin:0 0 6px;text-wrap:balance}}
h2{{font-family:var(--serif);font-weight:400;font-size:24px;margin:40px 0 10px;padding-top:8px;border-top:1px solid var(--line)}}
h3{{font-size:17px;margin:26px 0 8px}}
p,li{{max-width:72ch}}
a{{color:var(--accent)}}
code{{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code);padding:1px 5px;border-radius:5px}}
pre{{background:var(--code);padding:14px 16px;border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.5}}
pre code{{background:none;padding:0}}
table{{border-collapse:collapse;margin:14px 0;font-size:13.5px;display:block;overflow-x:auto;max-width:100%}}
th,td{{border:1px solid var(--line);padding:6px 10px;vertical-align:top;text-align:left}}
th{{background:var(--soft)}}
blockquote{{margin:14px 0;padding:4px 16px;border-left:3px solid var(--line);color:var(--muted)}}
.toc{{background:var(--soft);border-radius:10px;padding:12px 18px;font-size:14px;margin:18px 0}}
.toc ul{{margin:4px 0;padding-left:18px}}
.meta{{color:var(--muted);font-size:13px;margin:0 0 26px}}
.mermaid{{background:none}}
.mobile-toggle{{display:none}}
@media (max-width:860px){{.sidebar{{position:static;width:auto;border-right:0;border-bottom:1px solid var(--line)}}main{{margin:0;padding:24px 16px 60px}}h1{{font-size:28px}}}}
</style>
</head>
<body>
<nav class="sidebar" aria-label="Documentation">
<p class="brand">IAmAVirus</p>
<p class="sub">Fog of War chess bot · MIT 6.7980</p>
{nav}
<div class="ext">
<a href="{base}../">Interactive system notebook ↗</a>
<a href="https://github.com/htansetiawan/iamavirus">Repository ↗</a>
<a href="https://github.com/htansetiawan/mist-c">mist-c engine ↗</a>
</div>
</nav>
<main>
{body}
</main>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
mermaid.initialize({{startOnLoad:true,theme:window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"neutral"}});
</script>
</body>
</html>
"""


def read_nav(docs_dir):
    nav = []
    path = os.path.join(docs_dir, "_nav.txt")
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, title = line.split(":", 1)
        nav.append((name.strip(), title.strip()))
    return nav


def mermaid_fences(text):
    """Turn ```mermaid fences into <pre class="mermaid"> blocks before Markdown runs.

    The diagram text is left raw, which is what mermaid.js expects inside the element
    (arrows like --> and <br/> in labels); it must not contain a literal "</pre>".
    """
    def repl(m):
        return '<pre class="mermaid">\n' + m.group(1).replace("&", "&amp;") + "\n</pre>\n"
    return re.sub(r"```mermaid\n(.*?)\n```", repl, text, flags=re.S)


def first_paragraph(text):
    for para in text.split("\n\n"):
        p = para.strip()
        if p and not p.startswith("#") and not p.startswith("<") and not p.startswith("```") and not p.startswith("|"):
            return re.sub(r"[*_`\[\]]", "", p)[:200]
    return ""


def render(docs_dir, out_dir, base):
    nav = read_nav(docs_dir)
    os.makedirs(out_dir, exist_ok=True)
    for name, title in nav:
        src = os.path.join(docs_dir, name + ".md")
        text = open(src, encoding="utf-8").read()
        md = markdown.Markdown(extensions=EXTENSIONS, extension_configs={"toc": {"toc_depth": "2-3"}})
        body = md.convert(mermaid_fences(text))
        links = "\n".join(
            f'<a href="{base}{n}.html"{" class=\"current\"" if n == name else ""}>{html.escape(t)}</a>' for n, t in nav
        )
        page = TEMPLATE.format(title=html.escape(title), description=html.escape(first_paragraph(text)), nav=links, body=body, base=base)
        out = os.path.join(out_dir, name + ".html")
        open(out, "w", encoding="utf-8").write(page)
        print("wrote", out, len(page), "bytes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--base", default="./", help="URL prefix for links between pages")
    args = ap.parse_args()
    render(args.docs_dir, args.out_dir, args.base)


if __name__ == "__main__":
    sys.exit(main())
