"""Word count of the LaTeX report against the course limit of 5,000 words.

Run:
    python -m tennis_networks.wordcount [report/main.tex]

Conservative estimate: comments, commands and table, figure and equation environments are removed
(captions included), body text and the bibliography are kept. Exits with code 1 above the limit.
"""

import re
import sys
from pathlib import Path

from tennis_networks.config import REPORT

LIMIT = 5000


def count(tex):
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    tex = re.sub(r"\\begin\{(table|figure|tabular|equation|align)\*?\}.*?\\end\{\1\*?\}", " ", tex, flags=re.S)
    body = tex.split(r"\begin{document}")[-1].split(r"\end{document}")[0]
    body = re.sub(r"\\(cite|ref|label|url|href)\{[^}]*\}", " ", body)
    body = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", body)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", body))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT / "main.tex"
    n = count(path.read_text(encoding="utf-8"))
    print(f"{n} words out of {LIMIT} ({LIMIT - n} left)")
    sys.exit(0 if n <= LIMIT else 1)


if __name__ == "__main__":
    main()
