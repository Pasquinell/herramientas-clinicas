"""Genera páginas de prueba con todos los diagramas SVG de index.html en su estado final.

Uso (desde la raíz del proyecto):
    python3 -I doc/tools/figs_preview.py
    google-chrome --headless=new --no-sandbox --hide-scrollbars --window-size=1360,1600 \
        --virtual-time-budget=3000 --screenshot=figs_0.png "file://$PWD/doc/tools/out/figs_0.html"

Sirve para revisar solapamientos de texto en los diagramas sin tener que scrollear.
Con el argumento «dark» genera las páginas en modo oscuro.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "doc", "tools", "out")
os.makedirs(OUT, exist_ok=True)
dark = "dark" in sys.argv[1:]

s = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
head = s[: s.index('<header class="topbar"')]
# estilos con alcance que traen los bloques del P2 (#p2-...): se agregan y se envuelve cada svg en un contenedor con su id
body_styles = "".join(re.findall(r"<style>.*?</style>", s[s.index('<header class="topbar"'):], flags=re.S))
head += body_styles
if dark:
    head = head.replace('<html lang="es">', '<html lang="es" data-theme="dark">')
svgs = []
for m in re.finditer(r"<svg[^>]*viewBox=.*?</svg>", s, flags=re.S):
    if "aria-label" not in m.group(0) or "${" in m.group(0):
        continue
    sec = re.findall(r'<section[^>]*id="([^"]+)"', s[: m.start()])
    sid = sec[-1] if sec else ""
    svgs.append('<div id="%s">%s</div>' % (sid, m.group(0)) if sid.startswith("p2-") else m.group(0))
print(len(svgs), "diagramas")

for f in os.listdir(OUT):
    if f.startswith("figs_"):
        os.remove(os.path.join(OUT, f))
for part in range(0, len(svgs), 6):
    body = "".join(
        '<div class="panel dsc" style="margin:8px;width:640px;display:inline-block;vertical-align:top">'
        '<div class="mono" style="font-size:11px">#%d</div>%s</div>' % (i, svgs[i])
        for i in range(part, min(part + 6, len(svgs)))
    )
    html = (head + '<div style="width:1340px;padding:10px">' + body + "</div>"
            '<script>document.querySelectorAll("svg [data-s]").forEach(e=>e.classList.add("on"))</script></body></html>')
    open(os.path.join(OUT, "figs_%d.html" % (part // 6)), "w", encoding="utf-8").write(html)
