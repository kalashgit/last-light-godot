"""Cut the reference sheets into sprites at the darkest valleys between them; run directly for numbered previews."""
import sys, json
from PIL import Image, ImageDraw
def valleys(p, min_gap):
    n = len(p); sm = [sum(p[max(0, i - 2):i + 3]) / len(p[max(0, i - 2):i + 3]) for i in range(n)]
    cuts = [0]
    while True:
        lo = cuts[-1] + min_gap
        hi = min(n - 1, cuts[-1] + int(min_gap * 1.9))
        if lo >= n - 8: break
        if hi <= lo: break
        j = min(range(lo, hi + 1), key=lambda i: sm[i])
        cuts.append(j)
    if n - 1 - cuts[-1] > min_gap * 0.5: cuts.append(n - 1)
    return cuts
def bright(px, x, y): p = px[x, y]; return p[0] + p[1] + p[2]
def sprites(path):
    im = Image.open(path).convert("RGB"); W, H = im.size; px = im.load()
    rowp = [sum(1 for x in range(0, W, 2) if bright(px, x, y) > 150) for y in range(H)]
    rc = valleys(rowp, 34)
    boxes = []
    for r in range(len(rc) - 1):
        y0, y1 = rc[r], rc[r + 1]
        colp = [sum(1 for y in range(y0, y1) if bright(px, x, y) > 150) for x in range(W)]
        cc = valleys(colp, 30)
        for c in range(len(cc) - 1):
            x0, x1 = cc[c], cc[c + 1]
            # trim to content
            xs = [x for x in range(x0, x1) if colp[x] > 0]
            ys = [y for y in range(y0, y1) if any(bright(px, x, y) > 150 for x in range(x0, x1, 2))]
            if len(xs) > 8 and len(ys) > 8:
                boxes.append([xs[0], ys[0], xs[-1], ys[-1], r])
    return im, boxes
if __name__ == "__main__":
    out = {}
    for tag, path in (("a", sys.argv[1]), ("b", sys.argv[2])):
        im, bs = sprites(path)
        out[tag] = bs
        print(tag, len(bs), "rows", max(b[4] for b in bs) + 1)
        lab = im.resize((im.width * 2, im.height * 2), Image.NEAREST); d = ImageDraw.Draw(lab)
        for i, b in enumerate(bs):
            d.rectangle([b[0] * 2, b[1] * 2, b[2] * 2 + 1, b[3] * 2 + 1], outline=(255, 0, 255))
            d.text((b[0] * 2 + 2, b[1] * 2 + 1), str(i), fill=(0, 0, 0)); d.text((b[0] * 2 + 1, b[1] * 2), str(i), fill=(255, 255, 0))
        for q in range(4):
            lab.crop((0, q * 512, 3072, q * 512 + 512)).save(sys.argv[3] + "/lab_%s%d.png" % (tag, q))
    json.dump(out, open(sys.argv[3] + "/boxes.json", "w"))
