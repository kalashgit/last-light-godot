"""Validate A00's complete saved reference ledger against the archived census.

One source reference per input ID is required; semantic model certification
is deliberately *not* implied by metadata classification completeness.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
ARCHIVE = ROOT/'archive_a00/complete_source_file_registry.jsonl'
FILES = [
    'a00_batch_0001_300.jsonl', 'a00_batch_0002_300.jsonl',
    'a00_batch_0003_500.jsonl', 'a00_batch_0004_1000.jsonl',
    'a00_batch_0005_3000.jsonl', 'a00_batch_0006_3000.jsonl',
    'a00_batch_0007_8000.jsonl', 'a00_batch_0008_4925.jsonl',
]
SHARD_SIZE = 1000
archive = [json.loads(x) for x in ARCHIVE.open(encoding='utf8')]
assert len(archive) == 21025

all_rows, batches = [], []
for filename in FILES:
    path = ROOT/filename
    data = path.read_bytes()
    lines = [json.loads(x) for x in data.decode('utf8').splitlines()]
    assert lines and len({x['source_page_id'] for x in lines}) == len(lines)
    offset = len(all_rows)
    batches.append({
        'batch_id':lines[0]['batch_id'], 'filename':filename,
        'archive_offset_start':offset, 'archive_offset_end_exclusive':offset+len(lines),
        'row_count':len(lines), 'source_first':lines[0]['source_page_id'],
        'source_last':lines[-1]['source_page_id'],
        'sha256':hashlib.sha256(data).hexdigest(),
    })
    all_rows.extend(lines)

assert len(all_rows) == len(archive)
assert len({x['source_page_id'] for x in all_rows}) == len(all_rows)
for n,(source,ledger) in enumerate(zip(archive,all_rows)):
    assert source['mediawiki_page_id'] == ledger['source_page_id'], f'Page ID mismatch at {n}'
    assert source['title'] == ledger['source_title'], f'Title mismatch at {n}'
    assert source['file_page'] == ledger['source_url'], f'URL mismatch at {n}'
    assert source['rights'] == ledger['rights'], f'Rights mismatch at {n}'
    assert ledger.get('primary_class') and ledger.get('reason'), f'Missing classification at {n}'

verified_statuses = {
    'CANONICAL_SEMANTIC_IDENTITY_VERIFIED',
    'RECONCILED_CANONICAL_MASTER_SOURCE',
    'LINKED_VERIFIED_MASTER_REFERENCE',
}
verified_ids = sorted({x['master_id'] for x in all_rows if x.get('master_id') and x.get('semantic_status') in verified_statuses})
linked_ids = sorted({x['master_id'] for x in all_rows if x.get('master_id')})
class_counts = Counter(x['primary_class'] for x in all_rows)
assert sum(class_counts.values()) == 21025
assert len(verified_ids) == 22
assert all(x['rights'] == 'source_research_only' for x in all_rows)

final_batch_lines = (ROOT/FILES[-1]).read_text(encoding='utf8').splitlines(keepends=True)
last_shards = []
for i in range(0,len(final_batch_lines),SHARD_SIZE):
    block = final_batch_lines[i:i+SHARD_SIZE]
    part = chr(ord('a')+i//SHARD_SIZE)
    last_shards.append({
        'part':part,'path':f'docs/asset_audit/a00_20261108_b008_4925_part_{part}.jsonl',
        'row_count':len(block),
        'source_first':json.loads(block[0])['source_page_id'],
        'source_last':json.loads(block[-1])['source_page_id'],
        'bytes':len(''.join(block).encode()),
        'sha256':hashlib.sha256(''.join(block).encode()).hexdigest(),
    })
assert len(last_shards) == 5 and sum(x['row_count'] for x in last_shards) == 4925

result = {
    'report_id':'A00-20261108-ALL-21025',
    'conclusion':'FULL_METADATA_REFERENCE_CLASSIFICATION_COMPLETE_SEMANTIC_VISUAL_REVIEW_NOT_COMPLETE',
    'archive_count':len(archive), 'classified_count':len(all_rows),
    'unique_source_page_ids':len({x['source_page_id'] for x in all_rows}),
    'missing_archive_records':0,'duplicate_source_record_ids':0,
    'source_id_title_url_rights_alignment_verified':True,
    'classification_and_reason_nonempty_for_every_reference':True,
    'source_archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
    'global_concat_ledger_sha256':hashlib.sha256(b''.join((ROOT/x).read_bytes() for x in FILES)).hexdigest(),
    'primary_class_counts':dict(sorted(class_counts.items())),
    'verified_semantic_identities_to_date':len(verified_ids),
    'verified_semantic_master_ids':verified_ids,
    'source_linked_master_ids_including_historical_links':len(linked_ids),
    'candidate_source_rows_not_unique_masters':class_counts['CANONICAL_MASTER_CANDIDATE'],
    'manual_review_required_rows':class_counts['NEEDS_MANUAL_REVIEW'],
    'all_source_art_research_only':True,
    'visual_asset_approvals_from_this_audit':0,
    'notion_master_rows_post_batch_008':60,
    'a00_new_notion_rows_cumulative':19,
    'a00_preexisting_notion_rows_reconciled':3,
    'github_branch':'codex/a00-asset-audit-b001-20261108',
    'no_game_changes_merge_or_deploy':True,
    'next_archive_offset':None,'remaining_archive_rows':0,
    'batch_provenance':batches,
    'final_batch_shards':last_shards,
    'caveats':[
        'A label of CANONICAL_MASTER_CANDIDATE is a source-image lead, not a unique or approved Blender master.',
        'Provisional parent references, UI tiles, animation frames and redirects still require semantic/visual reconciliation where ambiguous.',
        'Indie Stone/PZwiki content is retained only as reference evidence; no game use rights have been granted.',
        'The 360 source GLBs are first-pass geometry, not Golden-standard art or engine-tested content.',
    ],
}
out = ROOT/'a00_20261108_complete_census_integrity.json'
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('batch_provenance','final_batch_shards','verified_semantic_master_ids','caveats')},indent=2))
