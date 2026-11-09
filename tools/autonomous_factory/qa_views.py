"""Image/texture technical gate for diagnostic F12 multi-angle output."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops


def validate(path):
    root = Path(path)
    metadata = json.loads((root / "views.json").read_text())
    assert metadata["status"] == "F12_DIAGNOSTIC_NOT_WORLD_SCALE_APPROVED"
    assert metadata["founder_approved"] is False
    assert [row["degrees"] for row in metadata["frames"]] == [0, 90, 180, 270]
    images = []
    for frame in metadata["frames"]:
        with Image.open(root / frame["file"]) as source:
            assert source.mode == "RGBA"
            im = source.copy()
        alpha = im.getchannel("A")
        bbox = alpha.getbbox()
        assert bbox is not None, "empty frame"
        assert min(bbox[0], bbox[1], im.width-bbox[2], im.height-bbox[3]) >= 4, "clipped view"
        images.append(im)
    assert any(ImageChops.difference(images[0].convert("RGB"), other.convert("RGB")).getbbox()
               or ImageChops.difference(images[0].getchannel("A"), other.getchannel("A")).getbbox()
               for other in images[1:]), "identical views"
    return len(images)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("directory")
    a = p.parse_args()
    print("F12_DIAGNOSTIC_VIEWS_PASS", validate(a.directory))
