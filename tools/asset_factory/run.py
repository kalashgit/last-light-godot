"""Checked Blender entrypoint, packing and validation. Python 3 + Pillow + Blender."""
import argparse, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True); p.add_argument('--representatives',action='store_true'); p.add_argument('--resume',action='store_true'); p.add_argument('--output',type=Path,default=Path('assets/generated/factory')); p.add_argument('--sheets',type=Path,default=Path('docs/asset-factory')); a=p.parse_args()
base=Path(__file__).resolve().parent
command=['blender','-b','--python',str(base/'render_batch.py'),'--','--output',str(a.raw)]
if a.representatives: command+=['--representatives']
if a.resume: command+=['--resume']
a.raw.mkdir(parents=True,exist_ok=True)
# Blender can return exit 0 after a Python exception; reject its diagnostic explicitly.
with (a.raw/'blender.log').open('w') as log:
 result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
text=(a.raw/'blender.log').read_text()
if result.returncode or 'Traceback (most recent call last)' in text or 'FACTORY DONE' not in text:
 print(text[-5000:]); raise SystemExit('Blender batch failed; not packing partial output')
print(text[text.rfind('FACTORY DONE'):].strip())
subprocess.run([sys.executable,str(base/'pack.py'),str(a.raw),'--output',str(a.output),'--sheets',str(a.sheets)],check=True)
subprocess.run([sys.executable,str(base/'validate.py'),str(a.output),'--count','20' if a.representatives else '300'],check=True)
