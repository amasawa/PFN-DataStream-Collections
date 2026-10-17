"""arXiv preprint of MICE from the TKDE source (../overleaf/tkde): a neutral single-column article without venue marks,
comments stripped (arXiv publishes the source), the same text, tables and figures. Writes ../overleaf/arxiv/ (refuses
to overwrite unless --force) and, after compiling there, arxiv_source.tar.gz with main.tex, main.bbl and the inputs.

Usage: python make_arxiv.py [--force]"""
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
SRC, DST = HERE.parent / 'overleaf/tkde', HERE.parent / 'overleaf/arxiv'

AUTHORS = r"""\author{%
  Zhangkai Wu \and Xu Zhang \and Zhihong Cui \and Kaize Shi\\[4pt]
  \normalsize AFFILIATIONS\\
  \normalsize\texttt{EMAIL}
}"""
FIT = r'\resizebox{\ifdim\width>\textwidth\textwidth\else\width\fi}{!}{'   # shrink to the text width, never enlarge


def strip_comments(text):
    """Drops comment-only lines and the text after an unescaped %, keeping the % (it suppresses the line-end space)."""
    out = []
    for line in text.splitlines():
        m = re.search(r'(?<!\\)%', line)
        if m is None:
            out.append(line)
        elif line[:m.start()].strip():
            out.append(line[:m.start() + 1])
        # comment-only line: dropped
    return '\n'.join(out) + '\n'


def expand_strings(bib):
    """Writes @string venues out as braced literals: Tectonic's BibTeX drops the spaces inside @string values
    ("ACM Comput. Surv." became "ACMComput.Surv." in the .bbl), and arXiv uses the shipped .bbl as is."""
    macros = dict(re.findall(r'@string\{(\w+)\s*=\s*"([^"]*)"\}', bib))
    bib = re.sub(r'@string\{\w+\s*=\s*"[^"]*"\}\n', '', bib)
    for k, v in macros.items():
        bib = re.sub(r'(=\s*)' + k + r'(\s*,)', lambda m: m.group(1) + '{' + v + '}' + m.group(2), bib)
    assert not re.search(r'(journal|booktitle)\s*=\s*[A-Za-z]', bib), 'unexpanded venue macro'
    return bib


def convert(tex):
    tex = strip_comments(tex)
    tex = tex.replace(r'\documentclass[10pt,journal,compsoc]{IEEEtran}',
                      '\\documentclass[11pt]{article}\n\\usepackage[margin=1in]{geometry}\n'
                      '\\usepackage[T1]{fontenc}\n\\usepackage{lmodern}\n\\setlength{\\emergencystretch}{1em}')
    tex = re.sub(r'\\usepackage\[textsize=tiny\]\{todonotes\}\n', '', tex)
    tex = re.sub(r'\\author\{Anonymous Authors%\n\}', lambda m: AUTHORS, tex)
    head = tex.index(r'\IEEEtitleabstractindextext{%')
    a0, a1 = tex.index(r'\begin{abstract}', head), tex.index(r'\end{abstract}', head) + len(r'\end{abstract}')
    k0 = tex.index(r'\begin{IEEEkeywords}', a1) + len(r'\begin{IEEEkeywords}')
    k1 = tex.index(r'\end{IEEEkeywords}}', k0)
    tail = tex.index(r'\IEEEdisplaynontitleabstractindextext', k1) + len(r'\IEEEdisplaynontitleabstractindextext')
    tex = (tex[:head] + '\\maketitle\n' + tex[a0:a1] + '\n\\noindent\\textbf{Keywords:} ' + tex[k0:k1].strip()
           + '\n' + tex[tail:])
    tex = tex.replace(r'\resizebox{\columnwidth}{!}{\input{fig_method.tex}}',
                      r'\resizebox{0.8\textwidth}{!}{\input{fig_method.tex}}')
    tex = tex.replace(r'\includegraphics[width=\columnwidth]{fig_recall.pdf}',
                      r'\includegraphics[width=0.65\textwidth]{fig_recall.pdf}')
    tex = tex.replace(r'\resizebox{\columnwidth}{!}{', FIT).replace(r'\resizebox{\textwidth}{!}{', FIT)
    def fit_wide(m):   # double-column tables without a resizebox: shrink to the single-column text width if needed
        block = m.group(0)
        if 'resizebox' in block:
            return block
        return block.replace(r'\begin{tabular}', FIT + r'\begin{tabular}').replace(r'\end{tabular}', r'\end{tabular}}')
    tex = re.sub(r'\\begin\{table\*\}.*?\\end\{table\*\}', fit_wide, tex, flags=re.S)
    # internal review rounds are not peer review, and the code is not yet public
    tex = tex.replace('added in response to review', 'added later')
    tex = tex.replace('a review-added control', 'a control added later')
    tex = tex.replace('in the released code', 'in the code')
    assert 'IEEE' not in tex.replace('IEEEtranN', ''), [l for l in tex.splitlines() if 'IEEE' in l][:3]
    return tex


def main():
    if DST.exists():
        assert '--force' in sys.argv, f'{DST} exists'
        shutil.rmtree(DST)
    DST.mkdir()
    (DST / 'main.tex').write_text(convert((SRC / 'main.tex').read_text()))
    for p in SRC.iterdir():
        if p.name.startswith('tab_') and p.suffix == '.tex' or p.name in ('math.tex', 'fig_method.tex'):
            (DST / p.name).write_text(strip_comments(p.read_text()))
        elif p.name == 'refs.bib':
            (DST / p.name).write_text(expand_strings(p.read_text()))
        elif p.name in ('fig_recall.pdf', 'algorithm.sty', 'algorithmic.sty'):
            shutil.copy(p, DST / p.name)
    print('written', DST)


if __name__ == '__main__':
    main()
