#!/usr/bin/env python3
"""Decode QR codes (and other barcodes) found in image files.

Used by the design-audit skill to verify that QR codes on a design
actually point where the copy says they do. Never guess QR contents
visually — run this script.

Usage:
    python3 decode_qr.py image1.png [image2.jpg ...]

Output: one JSON array (an object per image) printed to stdout.

Run from the skill directory after installing requirements.txt.

If it is missing the script exits with code 2 and prints the install
command, so the caller can install it and retry instead of guessing.
"""

import json
from pathlib import Path
import sys

MAX_UPSCALE_DIM = 4000  # don't upscale beyond this many pixels on a side
MAX_IMAGE_PIXELS = 36_000_000
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_BATCH = 40

INSTALL_CMD = "python -m pip install -r requirements.txt"


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


def _decode(image, scale):
    import zxingcpp
    from PIL import Image

    img = image
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    results = []
    formats = (zxingcpp.QRCode, zxingcpp.MicroQRCode, zxingcpp.RMQRCode)
    for r in zxingcpp.read_barcodes(img, formats=formats):
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
        if Path(path).stat().st_size > MAX_FILE_BYTES:
            return {"status": "error", "qr_codes": [], "error": "file exceeds 32 MiB"}
        with Image.open(path) as img:
            if img.width * img.height > MAX_IMAGE_PIXELS:
                return {"status": "error", "qr_codes": [], "error": "image exceeds 36 megapixels"}
            max_dim = max(img.size)
            image = img.convert("RGB")
    except Exception as e:
        return {"status": "error", "qr_codes": [], "error": f"cannot read image: {e}"}

    scales = [1] + [s for s in (2, 4) if max_dim * s <= MAX_UPSCALE_DIM]
    errors = []
    matches = []
    for scale in scales:
        try:
            results = _decode(image, scale)
        except Exception as e:
            errors.append(str(e))
            continue
        for result in results:
            center = result["center"]
            same_code = any(
                item["data"] == result["data"] and item["format"] == result["format"]
                and abs(item["center"]["x_pct"] - center["x_pct"]) <= 1
                and abs(item["center"]["y_pct"] - center["y_pct"]) <= 1
                for item in matches
            )
            if not same_code:
                matches.append(result)
    if matches:
        return {"status": "decoded", "qr_codes": matches, "error": None}
    if len(errors) == len(scales):
        return {"status": "error", "qr_codes": [], "error": errors[-1]}
    return {"status": "no_code", "qr_codes": [], "error": None}


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    if len(argv) - 1 > MAX_BATCH:
        print(json.dumps({"error": f"process no more than {MAX_BATCH} files per batch"}))
        return 2

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
