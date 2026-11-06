#!/usr/bin/env python3
"""Package metadata evidence only. Original art and source research pixels excluded."""
import base64,hashlib,json,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=r'''"""LAST LIGHT official-source checks — offline evidence snapshot, not sprite generation.
Run in CodePad. Python standard library only. Existing V4 art processing is unchanged.
"""
import base64, csv, hashlib, io, json, os, sqlite3, tempfile, zlib
from pathlib import Path
CUSTOM_WORK_FOLDER = ''  # Optional persistent Documents/Files destination.
SNAPSHOT_SHA256 = '@SHA@'
SNAPSHOT = '@PAYLOAD@'
EXPECTED_RECORDS = 4347

def choose_folder(explicit=''):
    configured = explicit or CUSTOM_WORK_FOLDER
    choices = [Path(configured).expanduser()] if configured else [Path.home()/'Documents'/'LAST_LIGHT_CATALOG_CHECKS',Path.home()/'LAST_LIGHT_CATALOG_CHECKS',Path.cwd()/'LAST_LIGHT_CATALOG_CHECKS']
    for p in choices:
        try:
            p.mkdir(parents=True,exist_ok=True)
            fd,test=tempfile.mkstemp(dir=p);os.close(fd);os.unlink(test)
            return p.resolve()
        except OSError:
            pass
    raise OSError('Set CUSTOM_WORK_FOLDER to a writable persistent CodePad Documents folder.')

def lines():
    # Stream decompression rather than loading the expanded full catalog into memory.
    decoder=zlib.decompressobj();pending=b''
    data=base64.b64decode(SNAPSHOT)
    for i in range(0,len(data),2048):
        pending+=decoder.decompress(data[i:i+2048])
        while b'\n' in pending:
            line,pending=pending.split(b'\n',1)
            if line:yield line
    pending+=decoder.flush()
    if pending.strip():yield pending

def run(output='',stop_after=None):
    base=choose_folder(output)
    database=sqlite3.connect(str(base/'source_checks.sqlite3'))
    database.execute('CREATE TABLE IF NOT EXISTS records (reference_id TEXT PRIMARY KEY, catalog_index INTEGER UNIQUE, record_sha256 TEXT NOT NULL, record_json TEXT NOT NULL)')
    checked=resumed=0;sha=hashlib.sha256();seen=set();indices=set()
    print('Persistent folder:',base)
    print('Checking official-source evidence snapshot. This program generates no sprite artwork.')
    try:
        for raw in lines():
            sha.update(raw+b'\n');row=json.loads(raw)
            ref=row['reference_id'];index=row['catalog_index']
            if ref in seen or index in indices:raise ValueError('Duplicate source identity/index')
            seen.add(ref);indices.add(index)
            original=row['authoritative_source_record']
            if original['reference_id']!=ref or original['catalog_index']!=index or original['source_filename']!=row['official_icon_filename']:
                raise ValueError('Official source identity/name was altered')
            if row.get('factory_render_ready') or row.get('new_art_generated') or row.get('actual_visual_approval'):
                raise ValueError('Metadata snapshot must not grant art production or visual approval')
            digest=hashlib.sha256(raw).hexdigest()
            prior=database.execute('SELECT record_sha256,record_json FROM records WHERE reference_id=?',(ref,)).fetchone()
            if prior and prior[0]==digest and hashlib.sha256(prior[1].encode()).hexdigest()==digest:
                resumed+=1
            else:
                with database:
                    database.execute('INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(reference_id) DO UPDATE SET catalog_index=excluded.catalog_index,record_sha256=excluded.record_sha256,record_json=excluded.record_json',(ref,index,digest,raw.decode()))
            checked+=1
            if checked%500==0:print('Checked',checked,'/',EXPECTED_RECORDS)
            if stop_after is not None and checked>=stop_after:
                print('CHECKPOINT SAVED. Run again to resume.')
                return {'checked':checked,'resumed':resumed,'interrupted':True}
        if sha.hexdigest()!=SNAPSHOT_SHA256 or len(seen)!=EXPECTED_RECORDS or indices!=set(range(1,EXPECTED_RECORDS+1)):
            raise ValueError('Snapshot integrity/accounting failed')
        # Export through atomic replacements; interruption never publishes a half file.
        drafts=exceptions=remaining=remaining_drafts=remaining_exceptions=0
        fd,temp=tempfile.mkstemp(dir=base,prefix='.catalog-')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                for (value,) in database.execute('SELECT record_json FROM records ORDER BY catalog_index'):
                    row=json.loads(value)
                    drafts+=bool(row['ready_for_brief_draft']);exceptions+=bool(row['blocking_reasons'])
                    if row['source_identity_status']!='previously_visually_and_context_verified':
                        remaining+=1;remaining_drafts+=bool(row['ready_for_brief_draft']);remaining_exceptions+=bool(row['blocking_reasons'])
                    stream.write(value+'\n')
                stream.flush();os.fsync(stream.fileno())
            os.replace(temp,base/'source_readiness.jsonl')
        finally:
            if os.path.exists(temp):os.unlink(temp)
        fd,temp=tempfile.mkstemp(dir=base,prefix='.review-table-')
        try:
            with os.fdopen(fd,'w',newline='',encoding='utf-8-sig') as stream:
                writer=csv.writer(stream)
                writer.writerow(['catalog_index','reference_id','official_source_filename','official_item_names','official_item_ids','source_page_url','official_article_urls','identity_bound_brief_draft','blocking_reasons','factory_render_ready'])
                for (value,) in database.execute('SELECT record_json FROM records ORDER BY catalog_index'):
                    row=json.loads(value);bs=row['official_bindings']
                    writer.writerow([row['catalog_index'],row['reference_id'],row['official_icon_filename'],'; '.join(sorted({b['official_item_name'] for b in bs})),'; '.join(sorted({v for b in bs for v in b['source_item_ids']})),row['source_page_url'],'; '.join(sorted({b['source_article_url'] for b in bs})),row['ready_for_brief_draft'],'; '.join(row['blocking_reasons']),False])
                stream.flush();os.fsync(stream.fileno())
            os.replace(temp,base/'source_review.csv')
        finally:
            if os.path.exists(temp):os.unlink(temp)
        result={'requested_remaining_records_checked':remaining,'remaining_identity_bound_brief_drafts':remaining_drafts,'remaining_source_exceptions':remaining_exceptions,'checked':checked,'resumed':resumed,'interrupted':False,'identity_bound_brief_drafts':drafts,'source_exceptions':exceptions,'new_factory_render_ready_records':0,'sprites_generated':0,'source_snapshot_sha256':SNAPSHOT_SHA256,'device_note':'Successful execution verifies this checker on this device, not source visual review or Godot.'}
        fd,temp=tempfile.mkstemp(dir=base,prefix='.summary-')
        with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
        os.replace(temp,base/'summary.json')
        print('SUMMARY',json.dumps(result,sort_keys=True))
        print('Original artwork/geometry and visual identity review are still required for new objects. Keep using the approved V4 art process.')
        return result
    finally:database.close()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='')
    args=parser.parse_args()
    run(args.output)
'''

def build():
 path=ROOT/'production/catalog_readiness/readiness_manifest.jsonl';data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
 payload=base64.b64encode(zlib.compress(data,9)).decode()
 code=TEMPLATE.replace('@SHA@',sha).replace('@PAYLOAD@',payload)
 output=ROOT/'LAST_LIGHT_CATALOG_CHECKS.py';output.write_text(code)
 return output
if __name__=='__main__':print(build())
