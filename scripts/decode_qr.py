#!/usr/bin/env python3
"""Decode QR codes (and other barcodes) found in image files.

Used by the design-audit skill to verify that QR codes on a design
actually point where the copy says they do. Never guess QR contents
visually — run this script.

Usage:
    python3 decode_qr.py image1.png [image2.jpg ...]

Output: one JSON object (see bottom of file) printed to stdout.

Decoding backends are tried in this order, using whichever is installed:
    1. zxing-cpp   (pip install zxing-cpp pillow)   — most robust
    2. pyzbar      (pip install pyzbar pillow; needs system libzbar)
    3. OpenCV      (pip install opencv-python)      — QR codes only

If none is installed the script exits with code 2 and prints install
instructions, so the caller can report "unverified" instead of guessing.
"""

import json
import sys

MAX_UPSCALE_DIM = 4000  # don't upscale beyond this many pixels on a side


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


def _try_zxing(path, scale):
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


def _try_pyzbar(path, scale):
    from PIL import Image
    from pyzbar.pyzbar import decode

    img = Image.open(path).convert("RGB")
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    results = []
    for r in decode(img):
        rect = r.rect
        pts = [
            (rect.left, rect.top),
            (rect.left + rect.width, rect.top + rect.height),
        ]
        results.append({
            "data": r.data.decode("utf-8", errors="replace"),
            "format": r.type,
            "center": _center_pct(pts, img.width, img.height),
        })
    return results


def _try_opencv(path, scale):
    import cv2

    img = cv2.imread(path)
    if img is None:
        raise IOError(f"cannot read image: {path}")
    if scale != 1:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    h, w = img.shape[:2]
    detector = cv2.QRCodeDetector()
    ok, texts, points, _ = detector.detectAndDecodeMulti(img)
    results = []
    if ok:
        for text, quad in zip(texts, points):
            if not text:
                continue
            pts = [(float(p[0]), float(p[1])) for p in quad]
            results.append({
                "data": text,
                "format": "QRCode",
                "center": _center_pct(pts, w, h),
            })
    return results


BACKENDS = [
    ("zxing-cpp", _try_zxing),
    ("pyzbar", _try_pyzbar),
    ("opencv", _try_opencv),
]


def _image_max_dim(path):
    try:
        from PIL import Image
        with Image.open(path) as img:
            return max(img.size)
    except Exception:
        try:
            import cv2
            img = cv2.imread(path)
            if img is not None:
                return max(img.shape[:2])
        except Exception:
            pass
    return None


def decode_image(path, backends):
    """Try each available backend at 1x, then upscaled, until codes are found."""
    max_dim = _image_max_dim(path)
    scales = [1]
    for s in (2, 4):
        if max_dim is None or max_dim * s <= MAX_UPSCALE_DIM:
            scales.append(s)

    last_error = None
    for scale in scales:
        for name, fn in backends:
            try:
                results = fn(path, scale)
            except ImportError:
                continue
            except Exception as e:  # unreadable file, backend bug, etc.
                last_error = f"{name}: {e}"
                continue
            if results:
                return {"qr_codes": results, "backend": name, "error": None}
    return {"qr_codes": [], "backend": None, "error": last_error}


def available_backends():
    usable = []
    for name, fn in BACKENDS:
        mod = {"zxing-cpp": "zxingcpp", "pyzbar": "pyzbar", "opencv": "cv2"}[name]
        try:
            __import__(mod)
            usable.append((name, fn))
        except ImportError:
            continue
    return usable


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1

    backends = available_backends()
    if not backends:
        print(json.dumps({
            "error": "no QR decoding backend installed",
            "fix": "pip install zxing-cpp pillow  (or: pip install pyzbar pillow / opencv-python)",
            "note": "Report QR contents as UNVERIFIED. Do not guess them from the image.",
        }, ensure_ascii=False, indent=2))
        return 2

    out = []
    for path in argv[1:]:
        result = decode_image(path, backends)
        result["image"] = path
        if not result["qr_codes"] and result["error"] is None:
            result["note"] = ("no QR code decoded; if one is visible in the image it may be "
                              "too small, low-contrast, or distorted — flag it as unscannable/unverified")
        out.append(result)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
