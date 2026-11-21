"""Structural checks, not a substitute for testing on a physical EMUI device."""
import hashlib
import io
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'releases/Z-Aurora-EMUI12-v1.0.hwt'
        cls.theme = ZipFile(cls.path)
        cls.items = json.loads((ROOT / 'assets/icons.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.theme.close()

    def test_archive_integrity_and_paths(self):
        self.assertIsNone(self.theme.testzip())
        names = self.theme.namelist()
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertFalse(name.startswith('/'))
            self.assertNotIn('..', Path(name).parts)
        self.assertNotIn('unlock', names)  # Retain stock lockscreen engine.
        self.assertNotIn('com.android.systemui', names)

    def test_metadata(self):
        xml = ET.fromstring(self.theme.read('description.xml'))
        self.assertEqual(xml.tag, 'HwTheme')
        self.assertEqual(xml.findtext('title'), 'Z Aurora')
        for tag in ['author', 'designer', 'version', 'screen', 'font']:
            self.assertTrue(xml.findtext(tag))

    def test_icon_mappings(self):
        expected = [p + '.png' for i in self.items for p in i['packages']]
        self.assertEqual(len(expected), len(set(expected)))
        with ZipFile(io.BytesIO(self.theme.read('icons'))) as icons:
            self.assertIsNone(icons.testzip())
            self.assertEqual(set(icons.namelist()), set(expected))
            for name in icons.namelist():
                with Image.open(io.BytesIO(icons.read(name))) as image:
                    image.load()
                    self.assertEqual(image.size, (192, 192))
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertEqual(image.getpixel((0, 0))[3], 0)
                    self.assertEqual(image.getpixel((96, 96))[3], 255)

    def test_wallpapers_and_previews(self):
        for name in self.theme.namelist():
            if name.endswith('.jpg'):
                with Image.open(io.BytesIO(self.theme.read(name))) as image:
                    image.load()
                    self.assertEqual(image.format, 'JPEG')
                    if name.startswith('wallpaper/'):
                        self.assertEqual(image.size, (1080, 2240))
        self.assertIn('preview/preview_icons_0.jpg', self.theme.namelist())
        self.assertIn('preview/preview_unlock_0.jpg', self.theme.namelist())

    def test_license_embedded(self):
        notice = self.theme.read('NOTICE.txt').decode()
        self.assertIn('Copyright (c) 2016 Vladimir Kharlampidi', notice)
        self.assertIn('Permission is hereby granted', notice)

    def test_checksums(self):
        lines = (ROOT / 'releases/SHA256SUMS.txt').read_text().splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            digest, name = line.split('  ')
            self.assertEqual(hashlib.sha256((ROOT / 'releases' / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
