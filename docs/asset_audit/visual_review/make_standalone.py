#!/usr/bin/env python3
"""Build one HTML file that opens without a web server or bundler."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parent
html=(root/'index.html').read_text(encoding='utf-8')
html=html.replace('<link rel="stylesheet" href="styles.css">','<style>\n'+(root/'styles.css').read_text(encoding='utf-8')+'\n</style>')
for name in ('catalog_embed.js','app.js'):
    html=html.replace(f'<script src="{name}" defer></script>','<script>\n'+(root/name).read_text(encoding='utf-8')+'\n</script>')
path=root/'LAST_LIGHT_A00_Visual_Review.html'
path.write_text(html,encoding='utf-8')
with zipfile.ZipFile(root/'LAST_LIGHT_A00_Visual_Review.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
    for name in ('index.html','app.js','styles.css','catalog_embed.js','README.md','catalog_manifest.json','validate_decisions.py'):
        bundle.write(root/name,arcname=name)
print(f'Standalone HTML: {path.stat().st_size:,} bytes')
