#!/usr/bin/env python3
"""Build a non-destructive evidence queue from A00 R02; never approve masters.

All groups are provisional. Source titles alone are not sufficient for a master.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def read_shards(pattern):
    for path in sorted(ROOT.glob(pattern)):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line:
                yield json.loads(line)


def main():
    rows = list(read_shards("a00_r02_review_*.jsonl"))
    assert len(rows) == 6072 and len({r["id"] for r in rows}) == len(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["family"], row["key"])].append(row)
    priority = {"PHYSICAL_MASTER_CANDIDATE": 0, "NEEDS_VISUAL_EVIDENCE": 1,
                "MODEL_VIEW_OF_PARENT": 2, "APPEARANCE_VARIANT": 3,
                "STATE_OF_PARENT": 4, "TILE_OR_ATLAS_COMPONENT": 5,
                "ANIMATION_REFERENCE": 6, "RESEARCH_COMPOSITE": 7,
                "NON_PHYSICAL_RESEARCH": 8}
    output = []
    for (family, key), members in groups.items():
        classes = Counter(m["decision"] for m in members)
        # Evidence priority is about what a reviewer should inspect, not production priority.
        parent_ids = sorted({m["parent_id"] for m in members if m["parent_id"] is not None})
        models = sorted({model for m in members for model in m["model_ids"]})
        master_ids = sorted({m["master"] for m in members if m["master"]})
        score = (25 if models else 0) + (25 if master_ids else 0) + (12 if parent_ids else 0)
        score += min(15, 3 * len(members))
        flags = []
        if len(master_ids) > 1:
            flags.append("MULTIPLE_CANONICAL_IDS_INSPECT")
        if len(parent_ids) > 1:
            flags.append("MULTIPLE_PARENTS_INSPECT")
        if classes["PHYSICAL_MASTER_CANDIDATE"] and (classes["NON_PHYSICAL_RESEARCH"] or classes["RESEARCH_COMPOSITE"]):
            flags.append("MASTER_RESEARCH_ROLE_COLLISION")
        if classes["PHYSICAL_MASTER_CANDIDATE"] and classes["TILE_OR_ATLAS_COMPONENT"]:
            flags.append("MODEL_TILE_ROLE_COLLISION")
        if not models and not master_ids:
            flags.append("NO_EXISTING_GEOMETRY_OR_REGISTRY_LINK")
        group_id = hashlib.sha256((family + "|" + key).encode()).hexdigest()[:16]
        output.append({
            "review_group_id": "a00r03_" + group_id,
            "provisional_root": key, "family": family, "source_count": len(members),
            "source_ids": sorted(m["id"] for m in members),
            "source_titles": [m["title"] for m in sorted(members, key=lambda m: m["id"])],
            "classification_counts": dict(sorted(classes.items())),
            "linked_existing_model_ids": models,
            "linked_existing_canonical_ids": master_ids,
            "parent_source_ids": parent_ids,
            "evidence_priority_score": score,
            "evidence_gaps": flags,
            "next_action": "Inspect actual imagery and game requirement; verify rights, model and Notion ID before master admission",
            "status": "UNVERIFIED_GROUP_NOT_PRODUCTION_AUTHORIZATION",
        })
    output.sort(key=lambda g: (-g["evidence_priority_score"], priority.get(next(iter(g["classification_counts"])), 9), g["family"], g["provisional_root"]))
    # These are bounded, deterministic work packets for human/image review, not 5k jobs.
    path = ROOT / "a00_r03_evidence_groups.jsonl"
    path.write_text("".join(json.dumps(g, ensure_ascii=False, sort_keys=True) + "\n" for g in output), encoding="utf-8")
    counts = Counter(r["decision"] for r in rows)
    report = {
        "schema": "A00_R03_EVIDENCE_QUEUE_V1",
        "source_references": 6072,
        "provisional_groups": len(output),
        "decisions": dict(sorted(counts.items())),
        "groups_with_model_links": sum(bool(g["linked_existing_model_ids"]) for g in output),
        "groups_with_canonical_links": sum(bool(g["linked_existing_canonical_ids"]) for g in output),
        "groups_with_conflicting_master_ids": sum("MULTIPLE_CANONICAL_IDS_INSPECT" in g["evidence_gaps"] for g in output),
        "groups_with_role_collisions": sum(any("COLLISION" in f for f in g["evidence_gaps"]) for g in output),
        "not_individually_verified": 6072,
        "newly_admitted_masters": 0,
        "queue_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "review_policy": "Only visual/source/gameplay/rights/registry corroboration can resolve a group; do not auto-approve.",
    }
    (ROOT / "a00_r03_evidence_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
