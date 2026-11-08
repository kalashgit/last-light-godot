#!/usr/bin/env python3
import datetime as dt
import json
import tempfile
from pathlib import Path
from validate_decisions import source_catalog,validate

cat=source_catalog()
assert len(cat['records'])==21025
assert sum(r['r02'] for r in cat['records'])==6072
assert len({r['id'] for r in cat['records']})==21025
assert len({r['sig'] for r in cat['records']})==21025
sample=cat['records'][0]
row={
    'schema':'A00_CLASSIFICATION_REVIEW_V1',
    'catalog_snapshot':cat['snapshot'],
    'source_page_id':sample['id'],
    'source_signature':sample['sig'],
    'base_classification':sample['proposal'],
    'proposed_classification':'NEEDS_VISUAL_EVIDENCE',
    'decision':'needs_evidence',
    'reviewer':'catalog-test',
    'notes':'Visual reference needs inspection',
    'reviewed_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'production_approval':False,
    'rights_approval':False,
}
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'test.jsonl'
    p.write_text(json.dumps(row)+'\n',encoding='utf-8')
    assert len(validate(p))==1
    row['rights_approval']=True
    p.write_text(json.dumps(row)+'\n',encoding='utf-8')
    try:validate(p)
    except ValueError:pass
    else:raise AssertionError('Unauthorized rights approval accepted')
print('PASS: 21,025/6,072 catalog integrity and reviewed decision validator')
