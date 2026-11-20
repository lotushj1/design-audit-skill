from pathlib import Path
import tempfile
import unittest

from PIL import Image
import zxingcpp

from scripts.decode_qr import decode_image


FIXTURES = Path(__file__).parent / "fixtures"


class TestDecoder(unittest.TestCase):
    def test_reports_real_export_facts_and_decodes_both_revision_outputs(self):
        first = decode_image(FIXTURES / "wcag-poster" / "v1.png")
        revised = decode_image(FIXTURES / "wcag-poster" / "v2.png")
        self.assertEqual(first["facts"], {
            "format": "PNG", "width": 1080, "height": 1280,
            "frames": 1, "first_frame_has_transparency": True,
            "first_frame_transparency_bounds": (0, 905, 18, 1280),
        })
        self.assertEqual(revised["facts"], {
            "format": "PNG", "width": 1080, "height": 1350,
            "frames": 1, "first_frame_has_transparency": False,
            "first_frame_transparency_bounds": None,
        })
        self.assertEqual([code["data"] for code in first["qr_codes"]], ["https://www.w3.org/TR/SVG2/"])
        self.assertEqual([code["data"] for code in revised["qr_codes"]], ["https://w3.org/TR/WCAG22/"])

    def test_inspect_only_uses_file_contents_and_checks_pixel_opacity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "misnamed.jpeg"
            Image.new("RGBA", (100, 200), (255, 244, 231, 255)).save(path, format="PNG")
            result = decode_image(path, inspect_only=True)
            self.assertEqual(result["status"], "inspected")
            self.assertEqual(result["facts"]["format"], "PNG")
            self.assertFalse(result["facts"]["first_frame_has_transparency"])
            self.assertEqual(result["qr_codes"], [])

    def test_uses_display_orientation_for_dimensions_and_qr_location(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotated.jpg"
            barcode = zxingcpp.create_barcode("rotate", zxingcpp.QRCode)
            tile = Image.fromarray(zxingcpp.write_barcode_to_image(barcode, scale=5)).convert("RGB")
            canvas = Image.new("RGB", (900, 540), "white")
            canvas.paste(tile, (35, 45))
            exif = Image.Exif()
            exif[274] = 6
            canvas.save(path, quality=94, exif=exif)
            result = decode_image(path)
            self.assertEqual((result["facts"]["width"], result["facts"]["height"]), (540, 900))
            code, = result["qr_codes"]
            self.assertEqual(code["data"], "rotate")
            self.assertGreater(code["center"]["x_pct"], 65)
            self.assertLess(code["center"]["y_pct"], 30)

    def test_reports_both_codes(self):
        result = decode_image(FIXTURES / "two-qr-codes.png")
        self.assertEqual(result["status"], "decoded")
        self.assertEqual(
            {code["data"] for code in result["qr_codes"]},
            {"https://example.invalid/registration", "https://example.invalid/location"},
        )

    def test_reports_clean_and_missing_images_separately(self):
        self.assertEqual(decode_image(FIXTURES / "clean-poster.png")["status"], "no_code")
        self.assertEqual(decode_image(FIXTURES / "absent.png")["status"], "error")

    def test_ignores_linear_barcodes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "linear.png"
            code = zxingcpp.create_barcode("linear-only", zxingcpp.Code128)
            Image.fromarray(zxingcpp.write_barcode_to_image(code, scale=3)).save(path)
            self.assertEqual(decode_image(path)["status"], "no_code")
