#!/usr/bin/env python3
"""Decode QR codes (and other barcodes) found in image files.

Used by the design-audit skill to verify that QR codes on a design
actually point where the copy says they do. Never guess QR contents
visually — run this script.

Usage:
    python3 decode_qr.py image1.png [image2.jpg ...]

Output: one JSON array (an object per image) printed to stdout.

Requires zxing-cpp — the only decoder reliable enough for design images
(small codes, styled backgrounds). Install it before running:

    pip install zxing-cpp pillow

If it is missing the script exits with code 2 and prints the install
command, so the caller can install it and retry instead of guessing.
"""

import json
import sys

MAX_UPSCALE_DIM = 4000  # don't upscale beyond this many pixels on a side

INSTALL_CMD = "pip install zxing-cpp pillow"


def _center_pct(points, width, height):
    """Rough center of a code as percentages of image size, for locating
    which QR code we're talking about in multi-code images."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if not xs or not width or not height:
        return None
    return {
        "x_pct": round(sum(xs) / len(xs) / width * 100, 1),
        "y_pct": round(sum(ys) / len(ys) / height * 100, 1),
    }


def _decode(path, scale):
    import zxingcpp
    from PIL import Image

    img = Image.open(path).convert("RGB")
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    results = []
    for r in zxingcpp.read_barcodes(img):
        pos = r.position
        pts = [
            (pos.top_left.x, pos.top_left.y),
            (pos.top_right.x, pos.top_right.y),
            (pos.bottom_right.x, pos.bottom_right.y),
            (pos.bottom_left.x, pos.bottom_left.y),
        ]
        results.append({
            "data": r.text,
            "format": str(r.format).split(".")[-1],
            "center": _center_pct(pts, img.width, img.height),
        })
    return results


def decode_image(path):
    """Try decoding at 1x, then upscaled — small QR codes on large canvases
    often only decode after enlargement."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            max_dim = max(img.size)
    except Exception as e:
        return {"qr_codes": [], "error": f"cannot read image: {e}"}

    scales = [1] + [s for s in (2, 4) if max_dim * s <= MAX_UPSCALE_DIM]
    last_error = None
    for scale in scales:
        try:
            results = _decode(path, scale)
        except Exception as e:
            last_error = str(e)
            continue
        if results:
            return {"qr_codes": results, "error": None}
    return {"qr_codes": [], "error": last_error}


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1

    try:
        import zxingcpp  # noqa: F401
        import PIL  # noqa: F401
    except ImportError as e:
        print(json.dumps({
            "error": f"required decoding library not installed: {e.name}",
            "fix": f"run `{INSTALL_CMD}` and retry",
            "note": ("zxing-cpp is required — do not fall back to weaker decoders "
                     "and do not guess QR contents from the image. If installation is "
                     "impossible, report QR contents as UNVERIFIED."),
        }, ensure_ascii=False, indent=2))
        return 2

    out = []
    for path in argv[1:]:
        result = decode_image(path)
        result["image"] = path
        if not result["qr_codes"] and result["error"] is None:
            result["note"] = ("no QR code decoded; if one is visible in the image it may be "
                              "too small, low-contrast, or distorted — flag it as unscannable/unverified")
        out.append(result)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
