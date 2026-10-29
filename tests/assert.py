# lom-ssg behavior lock: 71 HTML-conformance assertions (stdlib-only, single file).
#
# What it locks:
#   - the themes the v0.1.0 release notes advertised (heading levels, lists,
#     fenced code, inline quartet, escapes, CJK round trip, front-matter ->
#     template wiring),
#   - regressions fixed in the v0.1.1 review (hr variants, paragraph
#     termination by hr, template placeholder values never re-expanded),
#   - behaviors the original set never locked (unclosed fence, trailing spaces
#     on a closing fence, filename title fallback, missing-page skip, config
#     fallbacks with notices, missing-layout fallback, missing output dir,
#     no-pages config, missing config),
#   - plus a byte-exact golden reconciliation of the example site against
#     tests/golden/.
#
# How to run (from anywhere; all probe fixtures are generated in a system temp
# dir and removed afterwards, so the script leaves no files behind):
#
#   python tests/assert.py
#
# Toolchain resolution: ../lom/target/release/lom.exe relative to this repo
# (sibling checkout of the lom compiler), overridable via the LOM environment
# variable. The script creates example/dist if missing and builds the example
# site itself.

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOM = os.environ.get("LOM") or os.path.join(ROOT, os.pardir, "lom",
                                            "target", "release", "lom.exe")
LOM = os.path.normpath(LOM)
GOLDEN = os.path.join(ROOT, "tests", "golden")
EXAMPLE_DIST = os.path.join(ROOT, "example", "dist")
RESULTS = []


def check(name, cond):
    RESULTS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL") + "  " + name)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build(cfg):
    p = subprocess.run([LOM, "build.lom", "--", cfg], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


def main():
    TMP = tempfile.mkdtemp(prefix="lom-ssg-assert-")
    try:
        run(TMP)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)

    fails = [n for n, ok in RESULTS if not ok]
    print()
    print("总计 %d 项断言：PASS %d / FAIL %d"
          % (len(RESULTS), len(RESULTS) - len(fails), len(fails)))
    if fails:
        print("失败项：", fails)
        raise SystemExit(1)
    print("ALL ASSERTIONS PASSED")


def run(TMP):
    # ---------- probe A: full markdown subset + review-fix regressions ----------
    PA = os.path.join(TMP, "probeA")
    os.makedirs(os.path.join(PA, "dist"), exist_ok=True)
    write(os.path.join(PA, "site.json"),
          '{"name": "ProbeA", "src": "content", "out": "dist", "pages": ["tour.md"]}')
    write(os.path.join(PA, "layouts", "probe.html"),
          "T1={{title}}|T2={{ title }}|S={{ site_name }}|D={{  date  }}\n<body>\n{{ content }}</body>\n")
    tour_lines = [
        "---",
        "title: Tour 标题",
        "date: 2026-10-29",
        "template: probe",
        "---",
        "",
        "# 一级 H1",
        "",
        "## 二级 **粗体** 标题",
        "",
        "###### 六级",
        "",
        "####### 七个井号不是标题",
        "",
        "段落一第一行",
        "第二行软换行。",
        "",
        "段落二。",
        "",
        "- 列表甲",
        "- 列表乙 *斜体项*",
        "",
        "* 星号列表一项",
        "* 星号列表二项",
        "",
        "1. 第一",
        "2. 第二",
        "22. 两位数字",
        "",
        "> 引用一 **粗**",
        "> 引用二 `code`",
        "",
        "```lom",
        "fn x() -> Int",
        '    1 < 2 && "s"',
        "```",
        "",
        "行内四件套：`<code 原样>`、**粗**、*斜*、[文本](https://e.com/a?b=1&c=2)。",
        "",
        "转义：\\*字面星\\*、\\_字面下划线\\_、行尾反斜杠 \\",
        "",
        "hr 变体：",
        "",
        "---",
        "",
        "***",
        "",
        "-----",
        "",
        "****",
        "",
        "段落紧跟横线",
        "----",
        "",
        "横线后段落",
        "",
        "字面占位符 {{ site_name }} 不展开。",
        "",
        "{ 单花括号 }、{{ 未知 }} 不动。",
        "",
        'HTML 转义：<em>x</em>、a & b、"q"、<script>alert("x")</script>',
    ]
    write(os.path.join(PA, "content", "tour.md"), "\n".join(tour_lines) + "\n")
    rc, out = build(os.path.join(PA, "site.json"))
    A = read(os.path.join(PA, "dist", "tour.html"))

    check("A00 构建退出码 0", rc == 0)
    check("A01 h1 级别", "<h1>一级 H1</h1>" in A)
    check("A02 h2 级别+行内递归", "<h2>二级 <strong>粗体</strong> 标题</h2>" in A)
    check("A03 h6 级别", "<h6>六级</h6>" in A)
    check("A04 七个井号非标题成段落", "<p>####### 七个井号不是标题</p>" in A)
    check("A05 多行段落软换行保留", "<p>段落一第一行\n第二行软换行。</p>" in A)
    check("A06 段落间空行分隔", "<p>段落二。</p>" in A)
    check("A07 无序列表 - 前缀", "<ul>\n<li>列表甲</li>\n<li>列表乙 <em>斜体项</em></li>\n</ul>" in A)
    check("A08 无序列表 * 前缀", "<ul>\n<li>星号列表一项</li>\n<li>星号列表二项</li>\n</ul>" in A)
    check("A09 有序列表+多位序号", "<ol>\n<li>第一</li>\n<li>第二</li>\n<li>两位数字</li>\n</ol>" in A)
    check("A10 引用块+内部行内递归", "<blockquote>\n<p>引用一 <strong>粗</strong>\n引用二 <code>code</code></p>\n</blockquote>" in A)
    check("A11 围栏代码块 language class",
          '<pre><code class="language-lom">fn x() -&gt; Int\n    1 &lt; 2 &amp;&amp; &quot;s&quot;</code></pre>' in A)
    check("A12 行内 code 转义", "<code>&lt;code 原样&gt;</code>" in A)
    check("A13 行内粗体", "<strong>粗</strong>" in A)
    check("A14 行内斜体", "<em>斜</em>" in A)
    check("A15 链接文本递归+URL 转义", '<a href="https://e.com/a?b=1&amp;c=2">文本</a>' in A)
    check("A16 反斜杠转义星与下划线", "<p>转义：*字面星*、_字面下划线_、行尾反斜杠 \\</p>" in A)
    check("A17 hr 三横线", "<hr>" in A)
    check("A18 hr 五横线（v0.1.1 修复）", "<p>-----</p>" not in A)
    check("A19 hr 计数=5（---/***/-----/****/----）", A.count("<hr>") == 5)
    check("A20 hr 终止段落（v0.1.1 修复）", "<p>段落紧跟横线</p>" in A and "段落紧跟横线\n----" not in A)
    check("A21 hr 后段落照常渲染", "<hr>\n<p>横线后段落</p>" in A)
    check("A22 内容字面 {{ site_name }} 不二次展开（v0.1.1 修复）",
          "<p>字面占位符 {{ site_name }} 不展开。</p>" in A)
    check("A23 单花括号与未知变量不动", "<p>{ 单花括号 }、{{ 未知 }} 不动。</p>" in A)
    check("A24 正文全量 HTML 转义",
          '<p>HTML 转义：&lt;em&gt;x&lt;/em&gt;、a &amp; b、&quot;q&quot;、&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;</p>' in A)
    check("A25 模板紧凑形式 {{title}}", "T1=Tour 标题|" in A)
    check("A26 模板标准形式 {{ title }}", "T2=Tour 标题|" in A)
    check("A27 模板 site_name 接线", "S=ProbeA|" in A)
    check("A28 模板多余内侧空格 {{  date  }}", "D=2026-10-29" in A)
    check("A29 title 多处出现都替换且不重复", A.count("Tour 标题") == 2)

    # ---------- probe B: config defaults / missing page / no title /
    # unclosed fence / trailing-space fence / layout fallback ----------
    PB = os.path.join(TMP, "probeB")
    os.makedirs(os.path.join(PB, "dist"), exist_ok=True)
    write(os.path.join(PB, "site.json"),
          '{"pages": ["noTitle.md", "missing.md", "unclosed.md", "trail.md"]}')
    write(os.path.join(PB, "content", "noTitle.md"), "# 无标题页\n\n正文。\n")
    unclosed = ["---", "title: U", "date: 2021-02-03", "---", "", "开头段", "",
                "```lom", "fn a()", "    未闭合 <x>"]
    write(os.path.join(PB, "content", "unclosed.md"), "\n".join(unclosed) + "\n")
    trail = ["开头", "", "```js", "code line", "``` ", "after"]
    write(os.path.join(PB, "content", "trail.md"), "\n".join(trail) + "\n")
    rc, out = build(os.path.join(PB, "site.json"))
    NT = read(os.path.join(PB, "dist", "noTitle.html"))
    UC = read(os.path.join(PB, "dist", "unclosed.html"))
    TR = read(os.path.join(PB, "dist", "trail.html"))

    check("B00 构建退出码 0", rc == 0)
    check("B01 缺 name 提示+默认", "[ssg] name missing, using default" in out)
    check("B02 缺 src 默认 content", "[ssg] src missing, using default" in out and os.path.exists(os.path.join(PB, "dist", "noTitle.html")))
    check("B03 缺 out 默认 dist", "[ssg] out missing, using default" in out)
    check("B04 缺源页跳过", "[ssg] skip (missing source): " in out)
    check("B05 实建页数=3", "[ssg] done: 3 page(s)" in out)
    check("B06 无 title 文件名回落+默认站名", "<title>noTitle - My Site</title>" in NT)
    check("B07 无 date 页脚为空", "<footer></footer>" in NT)
    check("B08 模板缺失回落内建+提示", "[ssg] layout not found, fallback to builtin" in out and "<!DOCTYPE html>" in NT)
    check("B09 未闭合围栏取到文件尾（含末行换行）",
          '<pre><code class="language-lom">fn a()\n    未闭合 &lt;x&gt;\n</code></pre>' in UC)
    check("B10 未闭合围栏前正文照常", "<p>开头段</p>" in UC)
    check("B11 闭围栏尾随空格不被识别（吞到文件尾）",
          '<pre><code class="language-js">code line\n``` \nafter\n</code></pre>' in TR)

    # ---------- probes C/D/E: error paths ----------
    cfg_c = os.path.join(TMP, "probeC", "site.json")
    write(cfg_c, '{"name": "X"}')
    rc, out = build(cfg_c)
    check("C01 无 pages 数组不构建并说明", '[ssg] config has no "pages" array — nothing to build' in out and rc == 0)
    check("C02 无 pages 提示显式清单原因", "no directory listing" in out)
    cfg_d = os.path.join(TMP, "probeD", "none.json")
    rc, out = build(cfg_d)
    check("D01 配置缺失提示+用法", "[ssg] config not found: " + cfg_d in out and "[ssg] usage: lom build.lom -- <site.json>" in out)
    write(os.path.join(TMP, "probeE", "content", "x.md"), "# X\n")
    write(os.path.join(TMP, "probeE", "site.json"),
          '{"name": "E", "src": "content", "out": "noout", "pages": ["x.md"]}')
    rc, out = build(os.path.join(TMP, "probeE", "site.json"))
    check("E01 输出目录缺失不炸并给 mkdir 提示", "[ssg] output directory does not exist" in out and "mkdir -p" in out and rc == 0)

    # ---------- example site: content assertions + golden reconciliation ----------
    os.makedirs(EXAMPLE_DIST, exist_ok=True)
    rc, out = build(os.path.join("example", "site.json"))
    MT = read(os.path.join(EXAMPLE_DIST, "markdown-tour.html"))
    IX = read(os.path.join(EXAMPLE_DIST, "index.html"))
    AB = read(os.path.join(EXAMPLE_DIST, "about.html"))

    check("X00 example 构建退出码 0 且 3 页", rc == 0 and "[ssg] done: 3 page(s)" in out)
    check("X01 中文标题 front-matter→模板接线", "<title>Markdown 子集导览 - Lom SSG Example</title>" in MT)
    check("X02 CJK 逐字往返（生僻字+直角引号+全角标点）",
          "仓颉、熵、燚、「直角引号」与全角标点——逐字保留" in MT)
    check("X03 中文粗体", "<strong>粗体</strong>" in MT)
    check("X04 中文斜体", "<em>斜体</em>" in MT)
    check("X05 中文链接", '<a href="https://example.com/zh">链接</a>' in MT)
    check("X06 中文行内 code", "<code>code</code>" in MT)
    check("X07 反斜杠转义输出字面星", "*不斜体* 与 _下划线_" in MT)
    check("X08 中文围栏代码块转义",
          '<pre><code class="language-lom">fn main() -&gt; Unit\n    println(&quot;你好，世界&quot;)\nend</code></pre>' in MT)
    check("X09 水平线", "<hr>" in MT)
    check("X10 中文引用块", "<blockquote>" in MT and "第二行引用。" in MT)
    check("X11 中文无序列表", "<li>第一项</li>" in MT and "<li>第二项</li>" in MT)
    check("X12 中文有序列表", "<li>步骤一</li>" in MT and "<li>步骤三</li>" in MT)
    check("X13 script 标签转义", '<code>&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;</code>' in MT)
    check("X14 伪标签转义", "&lt;em&gt;伪标签&lt;/em&gt;" in MT)
    check("X15 amp 转义", "a &amp; b" in MT)
    check("X16 date→页脚接线", "<footer>2026-10-28</footer>" in MT and "<footer>2026-10-20</footer>" in AB)
    check("X17 布局 site_name 接线", '<header><a href="index.html">Lom SSG Example</a></header>' in MT)
    check("X18 index 页标题与正文", "<title>Home - Lom SSG Example</title>" in IX and "<h1>Welcome</h1>" in IX)
    check("X19 index 页相对链接", '<a href="markdown-tour.html">markdown tour</a>' in IX)
    check("X20 about 页有序+无序列表", "<ol>" in AB and "<ul>" in AB and "<li>no JavaScript</li>" in AB)
    check("X21 about 页行内 code", "<code>lom build.lom -- site.json</code>" in AB)
    for name in ("index", "about", "markdown-tour"):
        same = (read(os.path.join(GOLDEN, name + ".html"))
                == read(os.path.join(EXAMPLE_DIST, name + ".html")))
        check("G-" + name + " 修复前后逐字节一致（golden 对账）", same)


if __name__ == "__main__":
    if not os.path.exists(LOM):
        sys.exit("[assert] lom executable not found: %s\n"
                 "[assert] build it first or point the LOM env var at it" % LOM)
    main()
