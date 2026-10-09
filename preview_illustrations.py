"""Render every illustration into a preview sheet: out/illus.png"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import illustrations as I
from playwright.sync_api import sync_playwright

root = Path(__file__).parent
font = (root / "assets/fonts/Onest-wght.woff2").resolve().as_uri()
cells = "".join(f'<figure>{fn()}<figcaption>{name}</figcaption></figure>' for name, fn in I.ALL)
cols = int(sys.argv[1]) if len(sys.argv) > 1 else 7
html = f'''<html><head><meta charset="utf-8"><style>@font-face{{font-family:Onest;src:url("{font}")}}
body{{margin:0;padding:28px;font-family:Onest;background:#fff;color:#212121}}
.g{{display:grid;grid-template-columns:repeat({cols},190px);gap:18px}}
figure{{margin:0;background:#eaeff5;border-radius:12px;padding:15px;text-align:center}}
figure svg{{width:160px;height:160px}} figcaption{{font-size:13px;margin-top:6px}}</style></head>
<body><div class="g">{cells}</div></body></html>'''
(root / "out/illus.html").write_text(html)
rows = (len(I.ALL) + cols - 1) // cols
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 56 + cols * 208, "height": 56 + rows * 246}, device_scale_factor=2)
    pg.goto((root / "out/illus.html").resolve().as_uri())
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(root / "out/illus.png"))
    b.close()
print("out/illus.png")
