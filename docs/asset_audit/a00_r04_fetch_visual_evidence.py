#!/usr/bin/env python3
"""Fetch an explicitly bounded set of public research images for human inspection.

No image is copied to the game repo or approved for reuse.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
import hashlib
import json
import sys

TARGETS = [
    "AlcoholWipes.png", "AlcoholWipes-old.png", "WaterBottle.png",
    "WaterBottle Empty.png", "WaterBottle Full.png", "Candle.png",
    "CandleLit.png", "Candle Model.png", "Duffelbag.png",
    "DuffelBagRed.png", "DuffelBagBlue.png", "DuffelBagWhite.png",
    "Bookcase1.png", "Bookcase2.png", "FilingCabinet2.png",
    "Magazine.png", "MagazineOpen Model.png", "Bucket.png", "Bucket Empty.png",
]


class OriginalLink(HTMLParser):
    def __init__(self):
        super().__init__()
        self.url = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("class", "").find("internal") >= 0 and attrs.get("href", "").startswith("/w/images/"):
            self.url = urljoin("https://pzwiki.net", attrs["href"])
        if tag == "meta" and attrs.get("property") == "og:image" and not self.url:
            self.url = attrs.get("content")


def fetch(title, directory):
    source = "https://pzwiki.net/wiki/File:" + quote(title.replace(" ", "_"))
    result = {"source_title": title, "source_page": source, "image_saved": False}
    try:
        with urlopen(Request(source, headers={"User-Agent": "LAST-LIGHT-A00-research/1.0"}), timeout=30) as stream:
            html = stream.read(2_000_000).decode("utf-8", errors="replace")
        parser = OriginalLink()
        parser.feed(html)
        if not parser.url:
            raise ValueError("No source image linked from the file page")
        with urlopen(Request(parser.url, headers={"User-Agent": "LAST-LIGHT-A00-research/1.0"}), timeout=30) as stream:
            data = stream.read(10_000_000)
        if not data.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8")):
            raise ValueError("Not a supported image")
        dest = directory / title.replace(" ", "_")
        dest.write_bytes(data)
        result.update({"image_saved": True, "source_image_url": parser.url,
                       "file": str(dest), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    except Exception as error:
        result["error"] = str(error)
    return result


def main():
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/a00_visual_r04")
    directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(fetch, title, directory) for title in TARGETS]
        rows = [future.result() for future in as_completed(futures)]
    rows.sort(key=lambda row: row["source_title"])
    (directory / "provenance.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps({"requested": len(rows), "fetched": sum(r["image_saved"] for r in rows),
                      "failed": [r["source_title"] for r in rows if not r["image_saved"]]}, indent=2))


if __name__ == "__main__":
    main()
