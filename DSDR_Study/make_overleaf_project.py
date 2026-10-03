"""
Overleaf project for editing the report by hand: report/main.tex split into one file per chapter.

  OVERLEAF_PROJECT/
    main.tex                 preamble, title page, lists, and \\input of every part (the file to compile)
    frontmatter/*.tex        acknowledgement, abstract, abbreviations, symbols
    chapters/ch1_... .tex    one file per chapter
    appendices/*.tex         appendices A-E (E = comparison with the reference paper)
    references.tex
    figures/*.png            the pictures
  OVERLEAF_PROJECT.zip       the same, for Overleaf: New Project -> Upload Project

After the project is in Overleaf the text there is yours; running make_report_latex.py does not touch it.
"""

import os
import re
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "report", "main.tex")
OUT = os.path.join(os.path.dirname(HERE), "OVERLEAF_PROJECT")
tex = open(SRC, encoding="utf-8").read()

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
for d in ("frontmatter", "chapters", "appendices", "figures"):
    os.makedirs(os.path.join(OUT, d))

# split points: every \fronthead{..}, \chapterhead{..}{..}, \appendixhead{..}{..} and the references
pat = re.compile(r"^(?:% =+\n)?\\(fronthead|chapterhead|appendixhead)\{([^}]*)\}(?:\{([^}]*)\})?|^\\clearpage\n\\phantomsection\\addcontentsline\{toc\}\{section\}\{REFERENCES\}",
                 re.M)
marks = list(pat.finditer(tex))
end_doc = tex.index("\\end{document}")


def slug(t):
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:40]


parts, head = [], None
lists_start = tex.index("\\clearpage\n\\begin{spacing}")           # the lists stay in main.tex
nums = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8}
for k, m in enumerate(marks):
    start = m.start()
    stop = marks[k + 1].start() if k + 1 < len(marks) else end_doc
    if start < lists_start < stop:                                   # the lists sit between abstract and abbreviations
        stop = lists_start
    kind = m.group(1) or "references"
    if kind == "fronthead":
        name = "frontmatter/%s.tex" % slug(m.group(2))
    elif kind == "chapterhead":
        name = "chapters/ch%d_%s.tex" % (nums[m.group(2)], slug(m.group(3)))
    elif kind == "appendixhead":
        name = "appendices/app%s_%s.tex" % (m.group(2).lower(), slug(m.group(3)))
    else:
        name = "references.tex"
    body = tex[start:stop].rstrip() + "\n"
    arabic = "\\clearpage\n\\pagenumbering{arabic}"          # belongs in main.tex, before chapter one
    if arabic in body:
        body = body[:body.index(arabic)].rstrip().rstrip("%= \n") + "\n"
    open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(body)
    parts.append((start, stop, name))

# main.tex: everything that is not in a part, with \input lines in their place
main, pos = [], 0
for start, stop, name in parts:
    main.append(tex[pos:start])
    if name.startswith("chapters/ch1_"):
        main.append("\\clearpage\n\\pagenumbering{arabic}                      % page 1 = Introduction\n")
    main.append("\\input{%s}\n\n" % name[:-4])
    pos = stop
main.append(tex[pos:])
main_tex = "".join(main).replace("\\graphicspath{{figures/}{./}}", "\\graphicspath{{figures/}}")
open(os.path.join(OUT, "main.tex"), "w", encoding="utf-8", newline="\n").write(main_tex)

for f in os.listdir(os.path.join(HERE, "report", "figures")):
    shutil.copy(os.path.join(HERE, "report", "figures", f), os.path.join(OUT, "figures", f))

zpath = OUT + ".zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for d, _, fs in os.walk(OUT):
        for f in fs:
            p = os.path.join(d, f)
            z.write(p, os.path.relpath(p, OUT).replace("\\", "/"))
print("written", OUT)
for _, _, n in parts:
    print("  ", n)
print("zip:", zpath)
