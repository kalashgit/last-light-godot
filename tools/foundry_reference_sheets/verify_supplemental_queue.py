"""LAST LIGHT independent supplement intake acceptance.

Checks 250 unresolved *visual reference slots*, not 250 canonical models.
All rights/art/semantic approval flags must remain denied until Notion
recipes and independent original 3D authoring have been reviewed.

Read-only. Accepts an existing generated JSONL snapshot even when the exact
founder JPEGs are preserved in a separate private source archive. The JPEGs
are REQUIRED for independent `--images` verification, not silently waived.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from supplemental_sheet_queue import SHEETS, intake

EXPECTED = sum(v['slot_count'] for v in SHEETS.values())
PINNED_QUEUE_SHA256 = '123df46b168356126bf365e19926eed491aebf8da880d37ad7cad45c093126fe'
REQUIRED_FALSE = ('rights_reviewed', 'source_pixels_reusable',
                  'original_3d_model_built', 'founder_golden_approved')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def verify(queue: Path, report: Path, images: Path | None = None) -> dict[str, Any]:
    entries = [json.loads(l) for l in queue.read_text().splitlines() if l.strip()]
    summary = json.loads(report.read_text())
    if (len(entries) != EXPECTED or summary.get('total_reference_slots') != EXPECTED
            or summary.get('source_sheet_count') != len(SHEETS)
            or summary.get('model_count') != 0
            or summary.get('golden_3d_approved_count') != 0
            or summary.get('status') != 'REFERENCE_ONLY_AWAITING_NOTION'
            or summary.get('visual_slots_not_unique_models') is not True):
        raise ValueError('supplemental intake falsely counted or approved models')
    seen = set()
    expected_ids = set()
    for section, config in SHEETS.items():
        expected_ids |= {f'LL-SUP-20261110-{section}-{i+1:03}' for i in range(config['slot_count'])}
    for entry in entries:
        section = entry.get('sheet_section')
        if section not in SHEETS:
            raise ValueError('unknown or forged founder source section')
        config = SHEETS[section]
        key = entry.get('reference_id')
        if key in seen:
            raise ValueError('duplicate reference key')
        seen.add(key)
        index = int(key.rsplit('-', 1)[-1]) - 1
        cols, rows = config['cols'], config['rows']
        if not 0 <= index < config['slot_count']:
            raise ValueError('reference slot outside sheet')
        x, y = index % cols, index // cols
        expected_box = [1536*x//cols, 1024*y//rows,
                        1536*(x+1)//cols, 1024*(y+1)//rows]
        if (entry.get('schema') != 'last-light.reference-workorder.v1'
                or entry.get('image_sha256') != config['sha256']
                or entry.get('image_path') != ('data/foundry_reference_catalog/supplement_20261110/' + config['filename'])
                or entry.get('cell_row') != y or entry.get('cell_column') != x
                or entry.get('cell_box_xyxy') != expected_box
                or entry.get('numbering_reliability') != config['numbering']
                or entry.get('canonical_notion_id') is not None
                or entry.get('canonical_recipe_status') != 'AWAITING_NOTION'
                or entry.get('physical_unique_model_status') != 'UNVERIFIED_POSSIBLE_VARIANT_OR_DUPLICATE'
                or entry.get('working_label') is not None
                or any(entry.get(field) is not False for field in REQUIRED_FALSE)):
            raise ValueError('unsafe/altered reference admission flags or grid')
        if section == 'DENSE_200':
            if entry.get('proposed_sequence_number') != 401 + index:
                raise ValueError('dense grid sequence mismatch')
        elif entry.get('proposed_sequence_number') is not None:
            raise ValueError('unmapped sheet received fabricated canonical ID')
    if seen != expected_ids:
        raise ValueError('missing reference keys')
    if sha256(queue) != PINNED_QUEUE_SHA256:
        raise ValueError('unreviewed supplemental snapshot content changed')
    image_verified = False
    if images is not None:
        for config in SHEETS.values():
            source = images / config['filename']
            if not source.is_file() or sha256(source) != config['sha256']:
                raise ValueError('original founder JPEG missing or modified: ' + str(source))
        image_verified = True
    result = {
        'status': 'REFERENCE_ONLY_AWAITING_NOTION',
        'reference_slots': len(entries),
        'independent_original_image_verification': image_verified,
        'distinct_model_count': 0,
        'founder_golden_approved': 0,
        'all_canonical_ids_blocked': True,
        'queue_sha256': sha256(queue),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--images', type=Path, default=None)
    args = parser.parse_args()
    result = verify(args.queue, args.report, args.images)
    print('LL_SUPPLEMENTAL_REFERENCE_QA_PASS', json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()