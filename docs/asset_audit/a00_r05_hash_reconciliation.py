#!/usr/bin/env python3
"""Join remote-file hashes to R02 classifications; exact duplicate evidence only."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    metadata=[json.loads(x) for x in (ROOT/'a00_r05_image_metadata_6072.jsonl').read_text().splitlines()]
    assert len(metadata)==6072 and len({r['source_page_id'] for r in metadata})==6072
    original={}
    for p in sorted(ROOT.glob('a00_r02_review_*.jsonl')):
        for line in p.read_text().splitlines():
            r=json.loads(line);original[r['id']]=r
    by_sha=collections.defaultdict(list)
    for r in metadata:
        if r['file_sha1']:
            by_sha[r['file_sha1']].append(r)
    duplicates=[]
    for sha,records in by_sha.items():
        if len(records)<2:continue
        decisions={original[r['source_page_id']]['decision'] for r in records}
        roots={original[r['source_page_id']]['key'] for r in records}
        duplicates.append({
            'file_sha1':sha,'source_page_ids':sorted(r['source_page_id'] for r in records),
            'source_titles':[original[r['source_page_id']]['title'] for r in records],
            'semantic_roots':sorted(roots),'r02_decisions':sorted(decisions),
            'cross_root_duplicate':len(roots)>1,
            'decision':'EXACT_BINARY_MATCH_ONLY_NOT_ASSET_APPROVAL',
        })
    duplicates.sort(key=lambda r:(-len(r['source_page_ids']),r['file_sha1']))
    dest=ROOT/'a00_r05_exact_binary_duplicates.jsonl'
    dest.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in duplicates))
    report={
        'image_metadata_records':len(metadata),
        'resolved_images':sum(bool(r['image_url']) for r in metadata),
        'unique_image_hashes':len(by_sha),
        'exact_binary_duplicate_groups':len(duplicates),
        'duplicate_references_beyond_one_per_group':sum(len(r['source_page_ids'])-1 for r in duplicates),
        'cross_semantic_root_hash_groups':sum(r['cross_root_duplicate'] for r in duplicates),
        'candidate_master_admissions':0,
        'policy':'Identical source bytes prove the same image, not the same game object. Preserve all aliases and verify semantic roles.',
        'ledger_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
    }
    (ROOT/'a00_r05_hash_reconciliation_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
