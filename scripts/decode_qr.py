#!/usr/bin/env python3
"""Inspect raster images and optionally decode their QR codes.

Used by the design-audit skill to verify that QR codes on a design
actually point where the copy says they do. Never guess QR contents
visually — run this script.

Usage:
    python3 decode_qr.py [--inspect-only] image1.png [image2.jpg ...]

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


def decode_image(path, *, inspect_only=False):
    """Read file facts, then scan the display-oriented first frame if requested."""
    try:
        from PIL import Image, ImageOps
        if Path(path).stat().st_size > MAX_FILE_BYTES:
            return {"status": "error", "qr_codes": [], "error": "file exceeds 32 MiB"}
        with Image.open(path) as img:
            if img.width * img.height > MAX_IMAGE_PIXELS:
                return {"status": "error", "qr_codes": [], "error": "image exceeds 36 megapixels"}
            orientation = img.getexif().get(274, 1)
            width, height = img.size[::-1] if orientation in (5, 6, 7, 8) else img.size
            frames = getattr(img, "n_frames", 1)
            bands = img.getbands()
            if "A" in bands:
                alpha_min = img.getchannel("A").getextrema()[0]
            elif "a" in bands or img.has_transparency_data:
                alpha_min = img.convert("RGBA").getchannel("A").getextrema()[0]
            else:
                img.load()
                alpha_min = 255
            facts = {
                "format": img.format,
                "width": width,
                "height": height,
                "frames": frames,
                "first_frame_has_transparency": alpha_min < 255,
            }
            if inspect_only:
                return {"status": "inspected", "facts": facts, "qr_codes": [], "error": None}
            ImageOps.exif_transpose(img, in_place=True)
            image = img.convert("RGB")
    except Exception as e:
        return {"status": "error", "qr_codes": [], "error": f"cannot read image: {e}"}

    max_dim = max(image.size)
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
    if len(errors) == len(scales):
        return {"status": "error", "facts": facts, "qr_codes": [], "error": errors[-1]}
    return {"status": "decoded" if matches else "no_code", "facts": facts, "qr_codes": matches, "error": None}


def main(argv):
    args = argv[1:]
    inspect_only = args[:1] == ["--inspect-only"]
    files = args[1:] if inspect_only else args
    if not files:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    if len(files) > MAX_BATCH:
        print(json.dumps({"error": f"process no more than {MAX_BATCH} files per batch"}))
        return 2

    try:
        import PIL  # noqa: F401
        if not inspect_only:
            import zxingcpp  # noqa: F401
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
    for path in files:
        result = decode_image(path, inspect_only=inspect_only)
        result["image"] = path
        if result["status"] == "no_code":
            result["note"] = ("no QR code decoded; if one is visible in the image it may be "
                              "too small, low-contrast, or distorted — flag it as unscannable/unverified")
        out.append(result)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
