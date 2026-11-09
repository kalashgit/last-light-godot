"""Archive verified editable source ZIPs to a private dedicated R2 bucket.

This is invoked only by owner-authorized workflow_dispatch, never by a PR or
scheduled render. Successful return requires full remote readback and SHA256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path, PurePosixPath

SOURCE_CLASSES = frozenset({"legacy-360", "created-candidates"})
RELEASE_TAG = re.compile(r"(?:foundry-360-source-v1|foundry-created-[0-9]{1,18})\Z")
BUCKET = re.compile(r"last-light-foundry-[a-z0-9-]{3,45}\Z")


def inspect_zip(path: Path, source_class: str) -> dict:
    if source_class not in SOURCE_CLASSES:
        raise ValueError("Unknown source class")
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError("Missing or invalid source ZIP")
    with zipfile.ZipFile(path) as archive:
        entries = [i for i in archive.infolist() if not i.is_dir()]
        if not entries or len(entries) > 20000:
            raise ValueError("Suspicious ZIP file count")
        if sum(i.file_size for i in entries) > 16 * 1024**3:
            raise ValueError("Excessive uncompressed ZIP size")
        names = []
        for entry in entries:
            p = PurePosixPath(entry.filename)
            if (p.is_absolute() or ".." in p.parts or "\\" in entry.filename
                or entry.flag_bits & 0x1 or entry.file_size > 2 * 1024**3):
                raise ValueError("Untrusted ZIP entry path, encryption or size")
            names.append(str(p))
        if len(set(names)) != len(names):
            raise ValueError("Duplicate ZIP member")
        blends = [n for n in names if n.lower().endswith(".blend")]
        glbs = [n for n in names if n.lower().endswith(".glb")]
        required = 360 if source_class == "legacy-360" else 1
        if len(blends) < required or len(glbs) < required:
            raise ValueError("Incomplete editable source and GLB set")
        if archive.testzip() is not None:
            raise ValueError("Source ZIP failed CRC validation")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size,
            "blend_files": len(blends), "glb_files": len(glbs),
            "source_class": source_class, "golden_approved": False}


def _sha_stream(stream) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
        count += len(chunk)
    return digest.hexdigest(), count


def _missing(exc: Exception) -> bool:
    code = getattr(exc, "response", {}).get("Error", {}).get("Code")
    return str(code) in {"404", "NoSuchKey", "NotFound"}


def archive_to_r2(client, path: Path, bucket: str, tag: str, source_class: str) -> dict:
    if not BUCKET.fullmatch(bucket):
        raise ValueError("Refuse to use a non-dedicated Foundry bucket")
    if not RELEASE_TAG.fullmatch(tag):
        raise ValueError("Unrecognized immutable release tag")
    if (source_class == "legacy-360") != (tag == "foundry-360-source-v1"):
        raise ValueError("Source class/release mismatch")
    inventory = inspect_zip(path, source_class)
    key = f"original-sources/{source_class}/{tag}/{inventory['sha256']}.zip"
    metadata = {"sha256": inventory["sha256"], "github-release": tag,
                "art-status": "technical-candidate-not-golden"}
    try:
        remote = client.head_object(Bucket=bucket, Key=key)
    except Exception as exc:
        if not _missing(exc):
            raise
        remote = None
    if remote is None:
        with path.open("rb") as stream:
            client.put_object(Bucket=bucket, Key=key, Body=stream,
                              Metadata=metadata, ContentType="application/zip",
                              IfNoneMatch="*")
    elif remote.get("Metadata", {}).get("sha256") != inventory["sha256"]:
        raise ValueError("Existing object metadata contradicts local source")
    # HEAD/ETag alone is not proof of durable contents: read it back in full.
    response = client.get_object(Bucket=bucket, Key=key)
    try:
        actual_sha, actual_size = _sha_stream(response["Body"])
    finally:
        response["Body"].close()
    if actual_sha != inventory["sha256"] or actual_size != inventory["bytes"]:
        raise ValueError("R2 full readback digest/size mismatch; archive rejected")
    return {**inventory, "bucket": bucket, "key": key,
            "release_tag": tag, "remote_sha256_verified": True,
            "durable_source_archive_count": 1}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--source-class", required=True, choices=sorted(SOURCE_CLASSES))
    p.add_argument("--release-tag", required=True)
    p.add_argument("--report", required=True, type=Path)
    a = p.parse_args()
    keys = ("FOUNDRY_R2_ACCOUNT_ID", "FOUNDRY_R2_ACCESS_KEY_ID",
            "FOUNDRY_R2_SECRET_ACCESS_KEY", "FOUNDRY_R2_BUCKET")
    if any(not os.environ.get(k) for k in keys):
        raise SystemExit("FOUNDRY_R2_BLOCKED: dedicated bucket or S3 credentials missing")
    import boto3
    client = boto3.client("s3", endpoint_url=f"https://{os.environ['FOUNDRY_R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                          aws_access_key_id=os.environ["FOUNDRY_R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["FOUNDRY_R2_SECRET_ACCESS_KEY"],
                          region_name="auto")
    result = archive_to_r2(client, a.source, os.environ["FOUNDRY_R2_BUCKET"],
                           a.release_tag, a.source_class)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"FOUNDRY_R2_VERIFIED source={a.source_class} blends={result['blend_files']} "
          f"glbs={result['glb_files']} bytes={result['bytes']}")


if __name__ == "__main__":
    main()
