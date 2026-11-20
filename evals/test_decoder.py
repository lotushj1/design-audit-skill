from pathlib import Path
import tempfile
import unittest

from PIL import Image
import zxingcpp

from scripts.decode_qr import decode_image


FIXTURES = Path(__file__).parent / "fixtures"


class TestDecoder(unittest.TestCase):
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
