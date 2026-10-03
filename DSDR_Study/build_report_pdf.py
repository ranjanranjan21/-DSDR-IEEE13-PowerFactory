"""
Builds the project report as a PDF on this PC - no Overleaf needed.

  1. make_report_latex.py      fills the tables of report_template.tex.in with the current results
                               -> report/main.tex + report/figures/
  2. pdfLaTeX, three passes    (same compiler as Overleaf) -> report/DSDR_Report.pdf
  3. checks the log            errors, missing pictures, undefined references, text running into the margin

Compiler: TinyTeX in %APPDATA%\\TinyTeX (a missing LaTeX package is installed automatically with tlmgr).
Run:  python build_report_pdf.py          (add --open to open the PDF when it is done)
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "report")
OUT_PDF = os.path.join(REPORT, "DSDR_Report.pdf")
TEX_BIN = os.path.join(os.environ.get("APPDATA", ""), "TinyTeX", "bin", "windows")


def find(exe):
    for p in (os.path.join(TEX_BIN, exe + ".exe"), os.path.join(TEX_BIN, exe + ".bat"), shutil.which(exe) or ""):
        if p and os.path.isfile(p):
            return p
    sys.exit("%s not found - TinyTeX is expected in %s" % (exe, TEX_BIN))


def run_latex(work):
    pdflatex = find("pdflatex")
    for n in range(1, 4):
        p = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=work,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = p.stdout.decode("utf-8", "replace")
        if p.returncode:
            return False, log
        print("  pass %d ok" % n)
    return True, log


# ---- 1. LaTeX source from the results --------------------------------------------------------
print("1. Writing report/main.tex from the results", flush=True)
r = subprocess.run([sys.executable, os.path.join(HERE, "make_report_latex.py")], cwd=HERE)
if r.returncode:
    sys.exit("make_report_latex.py failed")

# ---- 2. compile in a scratch folder (keeps the report folder free of .aux/.log files) ------------
print("2. Compiling with pdfLaTeX", flush=True)
work = tempfile.mkdtemp(prefix="dsdr_report_")
shutil.copy(os.path.join(REPORT, "main.tex"), work)
shutil.copytree(os.path.join(REPORT, "figures"), os.path.join(work, "figures"))
ok, log = run_latex(work)
for attempt in range(5):                       # a missing package: install it and try again
    m = re.search(r"File `([^']+)\.(sty|cls)' not found", log)
    if ok or not m:
        break
    print("  installing missing LaTeX package for %s.%s" % m.groups())
    subprocess.run([find("tlmgr"), "install", m.group(1)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    ok, log = run_latex(work)
if not ok:
    err = [l for l in log.splitlines() if l.startswith("!")]
    i = log.find("\n!")
    print("\nCOMPILATION FAILED:\n" + (log[i:i + 1500] if i >= 0 else log[-1500:]))
    sys.exit(1)

# ---- 3. check the log --------------------------------------------------------------------------
full = open(os.path.join(work, "main.log"), encoding="latin-1").read()
issues = {"undefined references": len(re.findall(r"undefined", full)),
          "text into the margin (overfull boxes)": len(re.findall(r"Overfull \\hbox", full)),
          "pictures not found": len(re.findall(r"not uploaded yet|File `[^']+' not found", full))}
pages = re.search(r"Output written on main\.pdf \((\d+) pages", log)
try:
    shutil.copy(os.path.join(work, "main.pdf"), OUT_PDF)
    dest = OUT_PDF
except PermissionError:                         # the PDF is open in a viewer
    dest = OUT_PDF.replace(".pdf", "_new.pdf")
    shutil.copy(os.path.join(work, "main.pdf"), dest)
shutil.rmtree(work, ignore_errors=True)
print("3. Checks: " + ", ".join("%s %d" % kv for kv in issues.items()))
print("\nREPORT: %s (%s pages)%s" % (dest, pages.group(1) if pages else "?",
                                     "" if not any(issues.values()) else "  - see the checks above"))
if "--open" in sys.argv:
    os.startfile(dest)
