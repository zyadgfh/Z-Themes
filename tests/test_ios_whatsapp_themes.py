"""Structural checks for the 4 iOS WhatsApp themes (GoldThemes / YoThemes XML + wallpapers + ZIP)."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = [
    "iOS_Classic_Light",
    "iOS_Classic_Dark",
    "iOS_Modern_Light",
    "iOS_Modern_Dark",
]


class IOSWhatsAppThemeTests(unittest.TestCase):
    def test_all_editions_files_and_zip_structure(self):
        for slug in EDITIONS:
            folder = ROOT / "themes" / slug
            xml_path = folder / f"{slug}.xml"
            w_path = folder / f"{slug}_w.jpg"
            home_w_path = folder / f"{slug}_homeW.jpg"
            zip_path = folder / f"{slug}.zip"

            for p in (xml_path, w_path, home_w_path, zip_path):
                self.assertTrue(p.is_file(), f"Missing {p}")

            # Verify SharedPreferences <map> XML structure & required iOS layout keys
            root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
            self.assertEqual(root.tag, "map")
            strings = {el.attrib["name"]: el.text for el in root.findall("string")}
            self.assertEqual(strings.get("ui_home_styleV3"), "ios")
            self.assertEqual(strings.get("ui_bottom_style"), "ios")
            self.assertEqual(strings.get("ConvoEntry"), "28")
            self.assertEqual(strings.get("bubble_style"), "ios11")
            self.assertEqual(strings.get("tick_style"), "rcios11")

            # Verify wallpapers are valid JPEGs
            with Image.open(w_path) as im_w:
                im_w.load()
                self.assertEqual(im_w.format, "JPEG")
                self.assertEqual(im_w.size, (1080, 1920))
            with Image.open(home_w_path) as im_hw:
                im_hw.load()
                self.assertEqual(im_hw.format, "JPEG")
                self.assertEqual(im_hw.size, (720, 1280))

            # Verify ZIP archive has all 3 files directly at archive root
            with ZipFile(zip_path) as zf:
                self.assertIsNone(zf.testzip())
                self.assertEqual(
                    set(zf.namelist()),
                    {f"{slug}.xml", f"{slug}_w.jpg", f"{slug}_homeW.jpg"},
                )


if __name__ == "__main__":
    unittest.main()
