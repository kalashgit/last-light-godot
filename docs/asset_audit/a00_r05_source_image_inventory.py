#!/usr/bin/env python3
"""Resolve original-image metadata for every R02 reference, without licensing or approval.

Uses bounded MediaWiki API batches, retries, and resumable immutable checkpoints.
Image binary is never added to the repository.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import time

ROOT=Path(__file__).resolve().parent
CHECKPOINT=ROOT/'_r05_remote_evidence_cache'
CHECKPOINT.mkdir(exist_ok=True)

def get_batch(batch, entries):
    dest=CHECKPOINT/f'{batch:04d}.json'
    if dest.exists():
        data=json.loads(dest.read_text())
        if len(data['source_ids'])==len(entries):return data
    titles='|'.join(e['title'] for e in entries)
    url='https://pzwiki.net/w/api.php?'+urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|size|sha1|mime','titles':titles})
    last_error=''
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'LAST-LIGHT-A00-asset-research/1.0 (source-census)'}),timeout=30) as response:
                doc=json.load(response)
            pages={int(k):v for k,v in doc['query']['pages'].items()}
            out=[]
            for e in entries:
                page=pages.get(e['id'],{})
                info=(page.get('imageinfo') or [{}])[0]
                out.append({'source_page_id':e['id'],'source_title':e['title'],'image_url':info.get('url'),
                            'file_sha1':info.get('sha1'),'width':info.get('width'),'height':info.get('height'),
                            'bytes':info.get('size'),'mime':info.get('mime'),'missing':not bool(info.get('url'))})
            data={'source_ids':[e['id'] for e in entries],'records':out}
            dest.write_text(json.dumps(data,separators=(',',':'))+'\n')
            return data
        except Exception as err:
            last_error=str(err)
            time.sleep(2*(attempt+1))
    return {'source_ids':[e['id'] for e in entries], 'error':last_error, 'records':[]}

def main():
    source=[]
    for p in sorted(ROOT.glob('a00_r02_review_*.jsonl')):
        source.extend(json.loads(line) for line in p.read_text().splitlines())
    assert len(source)==6072 and len({r['id'] for r in source})==6072
    batches=[source[i:i+50] for i in range(0,len(source),50)]
    all_rows=[];errors=[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures={pool.submit(get_batch,i,b):i for i,b in enumerate(batches)}
        for fut in as_completed(futures):
            result=fut.result()
            if 'error' in result:errors.append({'batch':futures[fut],'error':result['error']})
            all_rows.extend(result['records'])
    all_rows.sort(key=lambda r:r['source_page_id'])
    path=ROOT/'a00_r05_image_metadata_6072.jsonl'
    path.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in all_rows))
    summary={'requested':6072,'resolved':sum(bool(r['image_url']) for r in all_rows),
             'missing_from_source':sum(r['missing'] for r in all_rows),'api_failed_batches':errors,
             'distinct_remote_sha1':len({r['file_sha1'] for r in all_rows if r['file_sha1']}),
             'image_records':len(all_rows),'scope':'remote image metadata only; not visual semantic verification or rights clearance'}
    (ROOT/'a00_r05_image_metadata_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
