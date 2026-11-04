"""Chequeos estáticos de index.html.

Uso (desde la raíz del proyecto):  python3 -I doc/tools/check.py

1. Balance de etiquetas HTML (parser de la biblioteca estándar).
2. Cada scrolly: el data-s máximo del diagrama no supera la cantidad de pasos.
3. ids duplicados y enlaces internos (#id) rotos.
4. Imágenes referenciadas que no existen en disco.
"""
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "path", "circle", "rect", "line", "ellipse", "polygon", "polyline", "stop", "use"}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.err = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.err.append("línea %d: </%s> no coincide con <%s> abierto en %s" % (
                self.getpos()[0], tag, self.stack[-1][0] if self.stack else "-", self.stack[-1][1] if self.stack else "-"))
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break


p = P()
p.feed(src)
problems = p.err + ["sin cerrar: <%s> línea %d" % s for s in p.stack]

scrollies = re.split(r'<div class="dsc', src)[1:]
n_sc = 0
for i, chunk in enumerate(scrollies):
    fig = chunk.split('<div class="dfig">', 1)
    steps = len(re.findall(r'<div class="dstep"', fig[0]))
    svg = fig[1].split("</svg>", 1)[0] if len(fig) > 1 else ""
    ss = [int(x) for x in re.findall(r'data-s="(\d+)"', svg)]
    n_sc += 1
    if ss and max(ss) > steps:
        lab = re.search(r'aria-label="([^"]+)"', svg)
        problems.append("scrolly #%d (%s): data-s máx %d > %d pasos" % (i, lab.group(1) if lab else "?", max(ss), steps))
    if ss and steps > max(ss) + 1:
        lab = re.search(r'aria-label="([^"]+)"', svg)
        print("aviso: scrolly #%d (%s): %d pasos y data-s máx %d" % (i, lab.group(1) if lab else "?", steps, max(ss)))

ids = re.findall(r'\sid="([^"]+)"', src)
dup = sorted({x for x in ids if ids.count(x) > 1})
if dup:
    problems.append("ids duplicados: " + ", ".join(dup))
for ref in sorted(set(re.findall(r'href="#([^"]+)"', src))):
    if ref not in ids and "'" not in ref:
        problems.append("enlace roto: #" + ref)
for img in sorted(set(re.findall(r'src="(img/[^"]+)"', src))):
    if not os.path.exists(os.path.join(ROOT, img)):
        problems.append("imagen ausente: " + img)

print("%d scrollies, %d diagramas, %d bytes" % (n_sc, len(re.findall(r"<svg viewBox", src)), len(src.encode())))
print("\n".join(problems) if problems else "OK: sin problemas")
