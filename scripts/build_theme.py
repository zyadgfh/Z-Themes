#!/usr/bin/env python3
"""Build an offline, reproducible Huawei icons-and-wallpapers theme."""
from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import resvg_py
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OUT = ROOT / 'releases'
NAME = 'Z-Aurora-EMUI12-v1.0'
SIZE = (1080, 2240)  # Huawei P20 Pro portrait resolution


def rgb(value):
    return tuple(bytes.fromhex(value.lstrip('#')))


def blend(a, b, t):
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(a, b))


def encode(image, fmt='PNG'):
    stream = io.BytesIO()
    image.save(stream, format=fmt, **({'quality': 94, 'subsampling': 0} if fmt == 'JPEG' else {}))
    return stream.getvalue()


def wallpaper():
    """Original folded-light artwork, not an Apple wallpaper."""
    w, h = 360, 747
    image = Image.new('RGB', (w, h))
    pixels = image.load()
    for y in range(h):
        v = y / h
        for x in range(w):
            u = x / w
            base = blend((9, 14, 45), (30, 27, 78), v)
            # Diagonal luminous ribbons separated by deep indigo negative space.
            ribbon = u + 0.32 * math.sin(v * 4.4 - 0.7) - 0.54
            for center, width, color in [(-0.25, .19, (34, 154, 230)),
                                          (.08, .12, (104, 80, 228)),
                                          (.31, .10, (243, 112, 161))]:
                glow = math.exp(-((ribbon - center) / width) ** 2)
                strength = glow * (.48 + .5 * math.sin(v * 2.8 + .2) ** 2)
                base = blend(base, color, strength)
            pixels[x, y] = base
    return image.resize(SIZE, Image.Resampling.LANCZOS)


def make_icon(item):
    n = 192
    bg = Image.new('RGBA', (n, n))
    top, bottom = rgb(item['colors'][0]), rgb(item['colors'][1])
    draw = ImageDraw.Draw(bg)
    for y in range(n):
        draw.line((0, y, n, y), fill=blend(top, bottom, y / (n - 1)) + (255,))
    mask = Image.new('L', (n, n))
    ImageDraw.Draw(mask).rounded_rectangle((1, 1, n - 2, n - 2), radius=43, fill=255)
    bg.putalpha(mask)
    source = (ASSETS / 'framework7' / f"{item['glyph']}.svg").read_text()
    source = source.replace('<path ', f'<path fill="{item.get("ink", "#ffffff")}" ')
    glyph = Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_string=source, width=122, height=122, skip_system_fonts=True))).convert('RGBA')
    bg.alpha_composite(glyph, (35, 35))
    # Fine highlight on the tile edge; no bitmap copied from iOS.
    ImageDraw.Draw(bg).rounded_rectangle((2, 2, n - 3, n - 3), radius=42, outline=(255, 255, 255, 50), width=1)
    return bg


def font(size):
    # Fonts are used only for the illustrative preview, never installed on device.
    path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def home_preview(wall, items, icons):
    """Illustrative arrangement; HWT does not enforce launcher layout or widgets."""
    image = wall.copy().convert('RGBA')
    draw = ImageDraw.Draw(image)
    draw.text((72, 105), 'Z / AURORA', font=font(34), fill='white')
    draw.text((72, 159), 'iOS-inspired • EMUI 12', font=font(25), fill='#d5dafa')
    for i, item in enumerate(items[:24]):
        x = 78 + (i % 4) * 250
        y = 300 + (i // 4) * 245
        image.alpha_composite(icons[item['id']].resize((170, 170), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 85, y + 182), item['label'], font=font(25), fill='white', anchor='mt', stroke_width=1, stroke_fill='#30304a')
    dock = Image.new('RGBA', SIZE)
    ImageDraw.Draw(dock).rounded_rectangle((42, 1900, 1038, 2140), radius=65, fill=(225, 229, 255, 40), outline=(255, 255, 255, 55), width=2)
    image.alpha_composite(dock)
    for col, key in enumerate(['phone', 'messages', 'browser', 'music']):
        image.alpha_composite(icons[key].resize((170, 170)), (78 + col * 250, 1935))
    return image.convert('RGB')


def archive(files):
    stream = io.BytesIO()
    with ZipFile(stream, 'w', compression=ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            entry = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, data)
    return stream.getvalue()


def main():
    OUT.mkdir(exist_ok=True)
    items = json.loads((ASSETS / 'icons.json').read_text())
    icons = {item['id']: make_icon(item) for item in items}
    icon_files = {}
    for item in items:
        for package in item['packages']:
            name = f'{package}.png'
            if name in icon_files:
                raise ValueError(f'Duplicate package: {package}')
            icon_files[name] = encode(icons[item['id']])
    wall = wallpaper()
    home = home_preview(wall, items, icons)
    description = '''<?xml version="1.0" encoding="UTF-8"?>
<HwTheme>
  <title>Z Aurora</title>
  <title-cn>Z Aurora</title-cn>
  <author>Z-Themes</author>
  <designer>Z-Themes / Framework7 Icons</designer>
  <screen>FHD</screen>
  <version>1.0</version>
  <font>Default</font>
  <font-cn>Default</font-cn>
  <briefinfo>iOS-inspired icons and original wallpaper. Targets EMUI 12; device testing required. Stock lock screen and system UI retained.</briefinfo>
</HwTheme>
'''
    notice = (ROOT / 'THIRD_PARTY_NOTICES.md').read_bytes() + b'\n\n' + (ASSETS / 'framework7' / 'LICENSE').read_bytes()
    files = {
        'description.xml': description.encode(),
        'icons': archive(icon_files),
        'wallpaper/home_wallpaper_0.jpg': encode(wall, 'JPEG'),
        'wallpaper/unlock_wallpaper_0.jpg': encode(wall, 'JPEG'),
        'preview/preview_icons_0.jpg': encode(home.resize((540, 1120)), 'JPEG'),
        'preview/preview_unlock_0.jpg': encode(wall.resize((540, 1120)), 'JPEG'),
        'preview/cover.jpg': encode(home.resize((540, 1120)), 'JPEG'),
        'preview/icon_small.jpg': encode(home.resize((180, 373)), 'JPEG'),
        'NOTICE.txt': notice,
    }
    data = archive(files)
    target = OUT / f'{NAME}.hwt'
    target.write_bytes(data)
    (OUT / 'Z-Aurora-preview.jpg').write_bytes(encode(home.resize((540, 1120)), 'JPEG'))
    (OUT / 'Z-Aurora-wallpaper.jpg').write_bytes(encode(wall, 'JPEG'))
    (OUT / 'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.suffix in ('.hwt', '.jpg')))
    print(f'Built {target.name}: {len(items)} designs, {len(icon_files)} package mappings; {len(data):,} bytes')


if __name__ == '__main__':
    main()
