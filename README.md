# lom-ssg

A tiny static site generator written in [Lom](https://github.com/lom-lang/lom),
an LLM-repair-native dynamic language with a frozen surface of 20 keywords and
43 builtins. lom-ssg grew naturally out of what Lom is demonstrably good at —
recursive-descent parsing and tree-to-string transformation — so its whole
pipeline (front-matter, block-level markdown, inline markdown, template
substitution) lives in a single 895-line Lom file with zero dependencies
beyond the language's builtin modules.

## Usage

```bash
# from a checkout of this repo, with the Lom toolchain on PATH
lom build.lom -- example/site.json

# output: example/dist/{index,about,markdown-tour}.html
```

- The config path comes from `argv[1]`; with no argument the tool falls back
  to `site.json` in the current directory and says so.
- The output directory must already exist (the Lom `file` module has no
  `mkdir` builtin): `mkdir -p example/dist` before the first build.

## Markdown subset

Block-level:

| Syntax | Output |
|---|---|
| `#` … `######` + space | `<h1>` … `<h6>` |
| blank-line separated text | `<p>` |
| `- item` / `* item` | `<ul><li>` |
| `1. item` (any digit run) | `<ol><li>` |
| ` ```lang ` fenced block | `<pre><code class="language-lang">` |
| `> quoted` lines | `<blockquote>` (contents rendered recursively) |
| `---` / `***` (unbroken run of 3+) | `<hr>` |

Inline: `` `code` ``, `**bold**`, `*italic*`, `[text](url)`, and backslash
escapes (`\_` prints a literal `_`; any `\x` prints a literal `x`).

HTML escaping (`& < > "`) is applied to all text and code output, including
inside code blocks and link URLs — raw markup from page content never reaches
the output unescaped.

## Configuration (`site.json`)

```json
{
  "name": "My Site",
  "src": "content",
  "out": "dist",
  "pages": ["index.md", "about.md"]
}
```

| Key | Meaning | Default when missing |
|---|---|---|
| `name` | site name (`{{ site_name }}`) | `My Site` (with a notice) |
| `src` | page directory, relative to the config file | `content` |
| `out` | output directory, relative to the config file | `dist` |
| `pages` | explicit list of markdown files under `src` | — (nothing is built) |

Missing keys fall back to defaults with a printed notice instead of failing.

Pages may start with a front-matter header delimited by `---` lines holding
`key: value` pairs; recognized keys are `title`, `date`, and `template`.
A page without `title` falls back to its file name.

## Layout / template

Templates live in `layouts/<name>.html` next to the config file. The
front-matter `template` key selects one (`default` if absent). Four variables
are substituted in a single pass: `{{ title }}`, `{{ content }}`,
`{{ site_name }}`, `{{ date }}` — tight `{{title}}` and extra-spaced forms
also work. Substituted values are inserted verbatim: a literal `{{ ... }}`
written in page content or a front-matter title is never re-expanded. If the
layout file is missing the tool prints a notice and falls back to a minimal
built-in template.

## Example

`example/` contains a three-page site (one page in Chinese, exercising the
UTF-8 round trip and HTML escaping):

```bash
mkdir -p example/dist
lom build.lom -- example/site.json
```

## Tests

`tests/assert.py` is the project's local gate: 71 HTML-conformance
assertions covering the full markdown subset (headings, lists, fences,
inline quartet, backslash escapes, HTML escaping), the CJK round trip,
front-matter → template wiring, every config/missing-file fallback path,
the v0.1.1 review fixes (hr variants, paragraph termination, placeholder
non-re-expansion), and a byte-exact reconciliation of the example site
against the golden files in `tests/golden/`.

```bash
python tests/assert.py     # expects the lom toolchain at ../lom/target/release/lom.exe
                           # (override with the LOM env var)
```

All probe fixtures are generated in a system temp dir and cleaned up, so
the run leaves no files behind. There is no CI pipeline for this repo —
the assertion set is the local verification gate; run it before cutting a
release.

## Boundaries

Honest scope limits of this MVP, several of them forced by Lom's frozen
builtin surface:

- **No directory crawling** — the `file` module (4 functions) has no listing
  primitive, so pages are enumerated explicitly in `site.json`.
- **No `mkdir`** — the output directory must exist; the tool checks and tells
  you instead of crashing.
- Markdown subset only: no tables, no nested lists, no images, no autolinks,
  no setext headings, no indented code blocks.
- Fenced code blocks must close with a bare ` ``` ` line (trailing spaces
  break detection); an unterminated fence consumes the rest of the file.
- `hr` recognizes unbroken runs of three or more `-` or `*` (e.g. `-----`);
  spaced or mixed runs like `- - -` or `-*-*` are not `hr` (`- - -` parses as
  a list item).
- Inline parsing is non-nesting-greedy in the CommonMark sense: `**a*b**`
  renders as bold containing an asterisk; emphasis does not span list items.
- Index page generation is not implemented; no `index` key is honored in
  this MVP.
- Config keys are detected by scanning the serialized JSON, so a config value
  that literally contains a quoted key name could confuse the fallback logic.

## License

Apache-2.0 — see [LICENSE](LICENSE). SPDX: `SPDX-License-Identifier: Apache-2.0`
(upstream text: <https://www.apache.org/licenses/LICENSE-2.0>).
