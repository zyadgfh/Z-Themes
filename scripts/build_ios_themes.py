#!/usr/bin/env python3
"""
Z-Themes — Authentic iOS WhatsApp Theme Builder
Generates GoldThemes / YoThemes / FouadMods / GBWhatsApp / FMWhatsApp compatible
theme bundles in the exact 3-file + ZIP format:
  - <ThemeName>.xml         (Android SharedPreferences <map> XML)
  - <ThemeName>_w.jpg       (Chat Doodle Wallpaper)
  - <ThemeName>_homeW.jpg   (Home Screen Background Wallpaper)
  - <ThemeName>.zip         (One-tap loadable archive containing all 3 files at root)
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
THEMES_DIR = ROOT_DIR / "themes"
DOODLE_MASK_PATH = ASSETS_DIR / "ios_doodle_mask.png"


def argb_int(hex_color: str) -> int:
    """Convert #RRGGBB or #AARRGGBB hex string to signed 32-bit Android Color int."""
    clean = hex_color.strip().lstrip("#")
    if len(clean) == 6:
        clean = "FF" + clean
    if len(clean) != 8:
        raise ValueError(f"Invalid hex color: {hex_color}")
    unsigned = int(clean, 16)
    return unsigned - 0x100000000 if unsigned >= 0x80000000 else unsigned


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    clean = hex_color.strip().lstrip("#")
    if len(clean) == 8:
        clean = clean[2:]
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


# Sanity-check signed 32-bit two's complement conversion
assert argb_int("#FFFFFF") == -1
assert argb_int("#000000") == -16777216
assert argb_int("#007AFF") == -16745729
assert argb_int("#0A84FF") == -16087809


@dataclass(frozen=True)
class IOSThemeSpec:
    slug: str
    title_en: str
    title_ar: str
    is_dark: bool
    accent_hex: str
    # System & Navigation Bars
    top_bar_bg: str
    status_bar_bg: str
    bottom_bar_bg: str
    nav_bar_bg: str
    header_text_icons: str
    tab_unselected: str
    tab_selected: str
    tab_badge_bg: str
    tab_badge_text: str
    # Home Screen & Rows
    home_bg: str
    row_title: str
    row_subtitle: str
    row_divider: str
    unread_badge_bg: str
    unread_badge_text: str
    online_color: str
    # Status / Updates Screen
    status_section_bg: str
    status_section_text: str
    status_seen_ring: str
    status_unseen_ring: str
    # Chat / Conversation Screen
    chat_top_bar_bg: str
    chat_bg_fallback: str
    chat_doodle_stroke: str
    right_bubble_bg: str
    right_bubble_text: str
    right_bubble_time: str
    left_bubble_bg: str
    left_bubble_text: str
    left_bubble_time: str
    link_color: str
    quote_bar_color: str
    quote_name_color: str
    quote_text_color: str
    quote_bg_color: str
    date_pill_bg: str
    date_pill_text: str
    # Chat Bottom Composer (iOS 14+ Pill Entry)
    composer_bar_bg: str
    composer_pill_bg: str
    composer_input_text: str
    composer_icon_color: str
    composer_send_circle_bg: str
    # Emoji Popup & Widget
    emoji_header_bg: str
    emoji_body_bg: str
    widget_bg: str


THEMES: Tuple[IOSThemeSpec, ...] = (
    IOSThemeSpec(
        slug="iOS_Classic_Light",
        title_en="iOS Classic Light (Blue)",
        title_ar="آيفون كلاسيك فاتح (أزرق iOS)",
        is_dark=False,
        accent_hex="#007AFF",
        top_bar_bg="#F6F6F6",
        status_bar_bg="#F6F6F6",
        bottom_bar_bg="#F6F6F6",
        nav_bar_bg="#F6F6F6",
        header_text_icons="#007AFF",
        tab_unselected="#8E8E93",
        tab_selected="#007AFF",
        tab_badge_bg="#FF3B30",
        tab_badge_text="#FFFFFF",
        home_bg="#FFFFFF",
        row_title="#000000",
        row_subtitle="#8E8E93",
        row_divider="#E5E5EA",
        unread_badge_bg="#007AFF",
        unread_badge_text="#FFFFFF",
        online_color="#007AFF",
        status_section_bg="#F2F2F7",
        status_section_text="#6C6C70",
        status_seen_ring="#C7C7CC",
        status_unseen_ring="#007AFF",
        chat_top_bar_bg="#F6F6F6",
        chat_bg_fallback="#EFEAE2",
        chat_doodle_stroke="#DDD5C9",
        right_bubble_bg="#DCF8C6",
        right_bubble_text="#000000",
        right_bubble_time="#5A7A52",
        left_bubble_bg="#FFFFFF",
        left_bubble_text="#000000",
        left_bubble_time="#8E8E93",
        link_color="#007AFF",
        quote_bar_color="#007AFF",
        quote_name_color="#007AFF",
        quote_text_color="#3C3C43",
        quote_bg_color="#14000000",
        date_pill_bg="#E9E4DC",
        date_pill_text="#3C3C43",
        composer_bar_bg="#F6F6F6",
        composer_pill_bg="#FFFFFF",
        composer_input_text="#000000",
        composer_icon_color="#007AFF",
        composer_send_circle_bg="#E1F0FF",
        emoji_header_bg="#F6F6F6",
        emoji_body_bg="#F2F2F7",
        widget_bg="#FFFFFF",
    ),
    IOSThemeSpec(
        slug="iOS_Classic_Dark",
        title_en="iOS Classic Dark (OLED Blue)",
        title_ar="آيفون كلاسيك داكن (OLED أزرق)",
        is_dark=True,
        accent_hex="#0A84FF",
        top_bar_bg="#161618",
        status_bar_bg="#161618",
        bottom_bar_bg="#161618",
        nav_bar_bg="#161618",
        header_text_icons="#0A84FF",
        tab_unselected="#8E8E93",
        tab_selected="#0A84FF",
        tab_badge_bg="#FF453A",
        tab_badge_text="#FFFFFF",
        home_bg="#000000",
        row_title="#FFFFFF",
        row_subtitle="#8E8E93",
        row_divider="#262629",
        unread_badge_bg="#0A84FF",
        unread_badge_text="#FFFFFF",
        online_color="#0A84FF",
        status_section_bg="#1C1C1E",
        status_section_text="#8E8E93",
        status_seen_ring="#48484A",
        status_unseen_ring="#0A84FF",
        chat_top_bar_bg="#161618",
        chat_bg_fallback="#0A1014",
        chat_doodle_stroke="#18232A",
        right_bubble_bg="#005C4B",
        right_bubble_text="#FFFFFF",
        right_bubble_time="#99BEB7",
        left_bubble_bg="#262628",
        left_bubble_text="#FFFFFF",
        left_bubble_time="#8E8E93",
        link_color="#53BDEB",
        quote_bar_color="#0A84FF",
        quote_name_color="#53BDEB",
        quote_text_color="#EBEBF5",
        quote_bg_color="#26000000",
        date_pill_bg="#1C1C1E",
        date_pill_text="#98989D",
        composer_bar_bg="#161618",
        composer_pill_bg="#2C2C2E",
        composer_input_text="#FFFFFF",
        composer_icon_color="#0A84FF",
        composer_send_circle_bg="#152A42",
        emoji_header_bg="#161618",
        emoji_body_bg="#1C1C1E",
        widget_bg="#1C1C1E",
    ),
    IOSThemeSpec(
        slug="iOS_Modern_Light",
        title_en="iOS Modern Light (New Green)",
        title_ar="آيفون حديث فاتح (أخضر iOS الجديد)",
        is_dark=False,
        accent_hex="#1DAB61",
        top_bar_bg="#FFFFFF",
        status_bar_bg="#FFFFFF",
        bottom_bar_bg="#F8F8F8",
        nav_bar_bg="#F8F8F8",
        header_text_icons="#0A0A0A",
        tab_unselected="#8E8E93",
        tab_selected="#1DAB61",
        tab_badge_bg="#FF3B30",
        tab_badge_text="#FFFFFF",
        home_bg="#FFFFFF",
        row_title="#0A0A0A",
        row_subtitle="#8E8E93",
        row_divider="#E5E5EA",
        unread_badge_bg="#1DAB61",
        unread_badge_text="#FFFFFF",
        online_color="#1DAB61",
        status_section_bg="#F2F2F7",
        status_section_text="#6C6C70",
        status_seen_ring="#C7C7CC",
        status_unseen_ring="#1DAB61",
        chat_top_bar_bg="#F8F8F8",
        chat_bg_fallback="#EFEAE2",
        chat_doodle_stroke="#DDD5C9",
        right_bubble_bg="#D9FDD3",
        right_bubble_text="#0A0A0A",
        right_bubble_time="#557552",
        left_bubble_bg="#FFFFFF",
        left_bubble_text="#0A0A0A",
        left_bubble_time="#8E8E93",
        link_color="#007AFF",
        quote_bar_color="#1DAB61",
        quote_name_color="#1DAB61",
        quote_text_color="#3C3C43",
        quote_bg_color="#14000000",
        date_pill_bg="#E9E4DC",
        date_pill_text="#3C3C43",
        composer_bar_bg="#F8F8F8",
        composer_pill_bg="#FFFFFF",
        composer_input_text="#0A0A0A",
        composer_icon_color="#1DAB61",
        composer_send_circle_bg="#DCF7E7",
        emoji_header_bg="#F8F8F8",
        emoji_body_bg="#F2F2F7",
        widget_bg="#FFFFFF",
    ),
    IOSThemeSpec(
        slug="iOS_Modern_Dark",
        title_en="iOS Modern Dark (OLED Green)",
        title_ar="آيفون حديث داكن (OLED أخضر)",
        is_dark=True,
        accent_hex="#21C063",
        top_bar_bg="#0B0B0C",
        status_bar_bg="#0B0B0C",
        bottom_bar_bg="#121214",
        nav_bar_bg="#121214",
        header_text_icons="#FFFFFF",
        tab_unselected="#8E8E93",
        tab_selected="#21C063",
        tab_badge_bg="#FF453A",
        tab_badge_text="#FFFFFF",
        home_bg="#000000",
        row_title="#FFFFFF",
        row_subtitle="#8E8E93",
        row_divider="#232326",
        unread_badge_bg="#21C063",
        unread_badge_text="#000000",
        online_color="#21C063",
        status_section_bg="#1C1C1E",
        status_section_text="#8E8E93",
        status_seen_ring="#48484A",
        status_unseen_ring="#21C063",
        chat_top_bar_bg="#121214",
        chat_bg_fallback="#0A1014",
        chat_doodle_stroke="#18232A",
        right_bubble_bg="#144D37",
        right_bubble_text="#FFFFFF",
        right_bubble_time="#97BDB0",
        left_bubble_bg="#262628",
        left_bubble_text="#FFFFFF",
        left_bubble_time="#8E8E93",
        link_color="#53BDEB",
        quote_bar_color="#21C063",
        quote_name_color="#21C063",
        quote_text_color="#EBEBF5",
        quote_bg_color="#26000000",
        date_pill_bg="#1C1C1E",
        date_pill_text="#98989D",
        composer_bar_bg="#121214",
        composer_pill_bg="#2C2C2E",
        composer_input_text="#FFFFFF",
        composer_icon_color="#21C063",
        composer_send_circle_bg="#143322",
        emoji_header_bg="#121214",
        emoji_body_bg="#1C1C1E",
        widget_bg="#1C1C1E",
    ),
)


def build_xml_content(spec: IOSThemeSpec) -> str:
    """Build verified YoThemes / GoldThemes / FouadMods SharedPreferences <map> XML."""
    color_prefs: Dict[str, str] = {
        # Universal & System Bars
        "ModConPickColor": spec.top_bar_bg,
        "ModDarkConPickColor": spec.status_bar_bg,
        "ModDarkConPickColorNav": spec.nav_bar_bg,
        "HomeBarText": spec.header_text_icons,
        "ModConBackColor": spec.home_bg,
        "list_bg_color": spec.home_bg,
        # Home Navigation / iOS Bottom Tab Bar
        "ModConColor": spec.bottom_bar_bg,
        "pagetitle_picker": spec.tab_unselected,
        "pagetitle_sel_picker": spec.tab_selected,
        "tabindicator": spec.accent_hex,
        "tabadgeBKColor": spec.tab_badge_bg,
        "tabadgeTextColor": spec.tab_badge_text,
        # Home Rows
        "ModContactNameColor": spec.row_title,
        "ModConTextColor": spec.row_subtitle,
        "chats_row_divider_picker": spec.row_divider,
        "HomeCounterBK": spec.unread_badge_bg,
        "HomeCounterText": spec.unread_badge_text,
        "ModOnlineColor": spec.online_color,
        "ModlastseenColor": spec.row_subtitle,
        "onlineDotchatColor": spec.online_color,
        "ModHomeMentionIndBackground": spec.unread_badge_bg,
        "ModHomeMentionIconColor": spec.unread_badge_text,
        # Status / Stories
        "statuses_bar_bg_picker": spec.status_section_bg,
        "statuses_bar_text_picker": spec.status_section_text,
        "SeenColor": spec.status_seen_ring,
        "UnSeenColor": spec.status_unseen_ring,
        "key_name_stories": spec.row_title,
        "key_counter_bg": spec.unread_badge_bg,
        "key_counter_tx": spec.unread_badge_text,
        # FAB fallback colors (FAB itself is hidden on iOS via hide_fab=true)
        "ModFabNormalColor": spec.accent_hex,
        "ModFabPressedColor": spec.accent_hex,
        "ModFabTextColor": "#FFFFFF",
        # Conversation Header & Bubbles
        "ModChatColor": spec.chat_top_bar_bg,
        "ModChatGStatusB": spec.chat_top_bar_bg,
        "ModChatGStatusT": spec.row_subtitle,
        "ConvoBack": spec.chat_bg_fallback,
        "ModChatRightBubble": spec.right_bubble_bg,
        "ModChatBubbleText": spec.right_bubble_text,
        "date_right_color": spec.right_bubble_time,
        "ModChatLeftBubble": spec.left_bubble_bg,
        "ModChatBubbleTextLeft": spec.left_bubble_text,
        "date_left_color": spec.left_bubble_time,
        "ModChatBubbleHyperlinks": spec.link_color,
        "rvkdmsg_icon_color": spec.row_subtitle,
        "quoted_divider_picker": spec.quote_bar_color,
        "quoted_name_picker": spec.quote_name_color,
        "quoted_text_picker": spec.quote_text_color,
        "quoted_bg_picker": spec.quote_bg_color,
        "date_bubble_color_picker": spec.date_pill_bg,
        "date_divider_color_picker": spec.date_pill_text,
        "participant_name_color_picker": spec.accent_hex,
        "seekbar_color_chat_picker": spec.accent_hex,
        "btn_voice_color_chat_picker": spec.accent_hex,
        # Conversation iOS 14+ Pill Entry Bar
        "BGColor": spec.composer_bar_bg,
        "ModChatEntry": spec.composer_pill_bg,
        "ModChatTextColor": spec.composer_input_text,
        "ModChatBtnColor": spec.composer_icon_color,
        "ModChatEmojiColor": spec.composer_icon_color,
        "ModChaSendColor": spec.composer_icon_color,
        "ModChaSendBKColor": spec.composer_send_circle_bg,
        # Emoji Popup & Widget
        "emojipopup_header": spec.emoji_header_bg,
        "emojipopup_icons": spec.accent_hex,
        "emojipopup_body": spec.emoji_body_bg,
        "ModWdgBKColor": spec.widget_bg,
        "ModWdgTitleColor": spec.row_title,
        "ModWdgStatusColor": spec.row_subtitle,
    }

    int_prefs: Dict[str, int] = {
        "main_text": 16,
        "text_size_pick": 16,
        "square_photo_ratio_picker": 100,
        "pic_chat_size_pickerV2": 36,
    }

    bool_prefs: Dict[str, bool] = {
        # Home UI & iOS Layout switches
        "home_imgBK": False,
        "hide_fab": True,
        "hide_action_a": False,
        "hide_action_b": False,
        "hide_action_l": False,
        "hide_action_m": False,
        "isSwipeEnabledV2": True,
        "Hide_div": False,
        "enable_ig_stories": False,
        "enable_grp_separation": False,
        "enable_grp_separationV2": False,
        "my_name": False,
        "my_statusd": True,
        "yo_want_airplanemode": False,
        "yo_want_nightmode": False,
        "disable_hiddenchat_access": False,
        "onlinechat": True,       # Disable Android-mod online text on home list
        "onlineDotchat": True,    # Disable Android-mod online dot overlay on avatars
        "elapsed_time": False,
        "chats_show_contact_online_toast_check": False,
        "imsHideMStatus": False,
        "imsHideVStatus": False,
        "imsHideRStatus": False,
        "enable_fivminstatus": False,
        "key_with_thumb": False,
        "status_wantsendconfirmation": False,
        # Conversation / Chat switches
        "PicProf": False,         # Keep contact avatar visible in chat top bar
        "NameProf": False,        # Keep contact name visible in chat top bar
        "Conv_call_btn": False,   # Keep Video & Audio call icons visible in chat top bar
        "statuschat": True,       # Hide Android-mod floating bio banner below chat top bar
        "newAttach_BottomDesign": True,  # Enable iOS-style bottom sheet when tapping '+'
        "custom_wall": False,     # Use default wallpaper.jpg populated from <Theme>_w.jpg
        "custom_wall_profilepic": False,
        "chat_contactpicV2": False,
        "chat_mypicV2": False,
        "group_participants_picV2": True,  # Show sender avatars in group chats like iOS
        "group_mypicV2": False,
        "pic_inside": False,
        "read_more": False,
        "disableDTTL": False,
        "Audio_sensor": True,
        "Audio_ears": False,
        "yo_hideinfo": True,
        "TxtSelect": True,
        "log_show_name_check": True,
        "multiChats": False,
        "Hide_contact_picker_section_frequent_chats": False,
        "Hide_contact_picker_section_other_contacts": False,
        "Hide_contact_picker_section_recent_chats": False,
    }

    string_prefs: Dict[str, str] = {
        "ui_home_styleV3": "ios",
        "ui_bottom_style": "ios",
        "HomeEntry": "yousef",
        "convostyle": "0",
        "ConvoEntry": "28",       # 21- iOS 14+ ('+' on left, rounded pill, sticker inside, cam + mic on right)
        "bubble_style": "ios11",  # Authentic rounded iOS WhatsApp bubble with curved corner tail
        "tick_style": "rcios11",  # Authentic iOS double checkmarks (grey sent/delivered, blue read)
        "font": "Default",
        "key_story_view": "0",
        "pic_startlocation": "1",
    }

    lines = ["<?xml version='1.0' encoding='utf-8' standalone='yes' ?>", "<map>"]

    for key, hex_val in sorted(color_prefs.items()):
        lines.append(f'    <int name="{escape(key)}" value="{argb_int(hex_val)}" />')
        lines.append(f'    <boolean name="{escape(key)}_Gactive" value="false" />')

    for key, int_val in sorted(int_prefs.items()):
        lines.append(f'    <int name="{escape(key)}" value="{int_val}" />')

    for key, bool_val in sorted(bool_prefs.items()):
        val_str = "true" if bool_val else "false"
        lines.append(f'    <boolean name="{escape(key)}" value="{val_str}" />')

    for key, str_val in sorted(string_prefs.items()):
        lines.append(f'    <string name="{escape(key)}">{escape(str_val)}</string>')

    lines.append("</map>")
    return "\n".join(lines) + "\n"


def render_wallpapers(spec: IOSThemeSpec, mask: Image.Image, out_dir: Path) -> Tuple[Path, Path]:
    """Generate <slug>_w.jpg (Chat Wallpaper) and <slug>_homeW.jpg (Home Wallpaper)."""
    # 1. Chat Doodle Wallpaper (<slug>_w.jpg) - 1080x1920
    bg_rgb = hex_to_rgb(spec.chat_bg_fallback)
    stroke_rgb = hex_to_rgb(spec.chat_doodle_stroke)
    bg_img = Image.new("RGB", mask.size, bg_rgb)
    stroke_img = Image.new("RGB", mask.size, stroke_rgb)
    chat_wall = Image.composite(stroke_img, bg_img, mask)

    chat_wall_path = out_dir / f"{spec.slug}_w.jpg"
    chat_wall.save(chat_wall_path, format="JPEG", quality=88, optimize=True, progressive=True)

    # 2. Home Background Wallpaper (<slug>_homeW.jpg) - 720x1280 (~3.5 KB, matching GoldThemes format)
    home_rgb = hex_to_rgb(spec.home_bg)
    home_wall = Image.new("RGB", (720, 1280), home_rgb)
    home_wall_path = out_dir / f"{spec.slug}_homeW.jpg"
    home_wall.save(home_wall_path, format="JPEG", quality=85, optimize=True)

    return chat_wall_path, home_wall_path


def build_showcase_preview(mask: Image.Image, out_path: Path) -> None:
    """Render a crisp 4-card visual preview sheet of all 4 iOS WhatsApp themes."""
    card_w, card_h = 420, 760
    pad = 28
    header_h = 84
    canvas_w = pad + len(THEMES) * (card_w + pad)
    canvas_h = header_h + card_h + pad

    canvas = Image.new("RGB", (canvas_w, canvas_h), (242, 242, 247))
    draw = ImageDraw.Draw(canvas)

    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except OSError:
        font_lg = font_md = font_sm = font_xs = ImageFont.load_default()

    draw.text(
        (pad, 28),
        "Z-Themes — iOS WhatsApp Theme Suite (4 Editions: Light & Dark × Classic Blue & Modern Green)",
        fill=(28, 28, 30),
        font=font_lg,
    )

    small_mask = mask.resize((card_w, 340), Image.BILINEAR)

    for idx, spec in enumerate(THEMES):
        x0 = pad + idx * (card_w + pad)
        y0 = header_h

        # Outer phone frame
        frame_border = (58, 58, 60) if spec.is_dark else (209, 209, 214)
        draw.rounded_rectangle(
            (x0 - 2, y0 - 2, x0 + card_w + 2, y0 + card_h + 2),
            radius=28,
            fill=frame_border,
        )
        card = Image.new("RGB", (card_w, card_h), hex_to_rgb(spec.home_bg))
        cd = ImageDraw.Draw(card)

        # Top Half: iOS Home Screen Preview (y = 0..340)
        cd.rectangle((0, 0, card_w, 56), fill=hex_to_rgb(spec.top_bar_bg))
        cd.text((16, 18), "Edit", fill=hex_to_rgb(spec.accent_hex), font=font_sm)
        cd.text((175, 17), "Chats", fill=hex_to_rgb(spec.row_title), font=font_md)
        cd.ellipse((card_w - 36, 16, card_w - 14, 38), outline=hex_to_rgb(spec.accent_hex), width=2)
        cd.line((card_w - 25, 21, card_w - 25, 33), fill=hex_to_rgb(spec.accent_hex), width=2)
        cd.line((card_w - 31, 27, card_w - 19, 27), fill=hex_to_rgb(spec.accent_hex), width=2)

        sample_rows = [
            ("Ahmed", "Sounds great! See you at 8", "9:41 AM", "2"),
            ("Sarah", "✓✓ Sent the iOS theme files", "Yesterday", ""),
            ("Design Team", " Omar: Perfect iOS look!", "Yesterday", "5"),
        ]
        for r_idx, (name, msg, time_str, unread) in enumerate(sample_rows):
            ry = 68 + r_idx * 64
            avatar_bg = (58, 58, 60) if spec.is_dark else (229, 229, 234)
            cd.ellipse((14, ry + 6, 56, ry + 48), fill=avatar_bg)
            cd.text((68, ry + 7), name, fill=hex_to_rgb(spec.row_title), font=font_md)
            cd.text((68, ry + 30), msg, fill=hex_to_rgb(spec.row_subtitle), font=font_xs)
            t_col = hex_to_rgb(spec.unread_badge_bg) if unread else hex_to_rgb(spec.row_subtitle)
            cd.text((card_w - 76, ry + 9), time_str, fill=t_col, font=font_xs)
            if unread:
                cd.ellipse((card_w - 36, ry + 28, card_w - 16, ry + 48), fill=hex_to_rgb(spec.unread_badge_bg))
                cd.text((card_w - 30, ry + 31), unread, fill=hex_to_rgb(spec.unread_badge_text), font=font_xs)
            cd.line((68, ry + 60, card_w, ry + 60), fill=hex_to_rgb(spec.row_divider), width=1)

        # iOS Bottom Tab Bar (y = 266..314)
        cd.rectangle((0, 266, card_w, 314), fill=hex_to_rgb(spec.bottom_bar_bg))
        cd.line((0, 266, card_w, 266), fill=hex_to_rgb(spec.row_divider), width=1)
        tabs = ["Updates", "Calls", "Camera", "Chats"]
        for t_i, t_name in enumerate(tabs):
            tx = 22 + t_i * 100
            is_sel = t_name == "Chats"
            col = hex_to_rgb(spec.tab_selected if is_sel else spec.tab_unselected)
            cd.rounded_rectangle((tx + 14, 273, tx + 36, 291), radius=5, outline=col, width=2)
            cd.text((tx + 6, 295), t_name, fill=col, font=font_xs)
            if is_sel:
                cd.ellipse((tx + 30, 269, tx + 46, 285), fill=hex_to_rgb(spec.tab_badge_bg))
                cd.text((tx + 35, 270), "7", fill=hex_to_rgb(spec.tab_badge_text), font=font_xs)

        # Bottom Half: iOS Chat Screen Preview (y = 316..card_h)
        chat_bg = Image.new("RGB", (card_w, 340), hex_to_rgb(spec.chat_bg_fallback))
        chat_stroke = Image.new("RGB", (card_w, 340), hex_to_rgb(spec.chat_doodle_stroke))
        chat_area = Image.composite(chat_stroke, chat_bg, small_mask)
        card.paste(chat_area, (0, 368))

        # Chat Top Bar (y = 316..368)
        cd.rectangle((0, 316, card_w, 368), fill=hex_to_rgb(spec.chat_top_bar_bg))
        cd.line((0, 316, card_w, 316), fill=frame_border, width=2)
        cd.text((12, 333), "< 7", fill=hex_to_rgb(spec.header_text_icons), font=font_md)
        cd.ellipse((52, 326, 84, 358), fill=(142, 142, 147))
        cd.text((94, 327), "Ahmed", fill=hex_to_rgb(spec.header_text_icons), font=font_md)
        cd.text((94, 345), "online", fill=hex_to_rgb(spec.row_subtitle), font=font_xs)
        cd.text((card_w - 72, 333), "Video  Call", fill=hex_to_rgb(spec.header_text_icons), font=font_xs)

        # Date pill
        cd.rounded_rectangle((172, 380, 248, 402), radius=10, fill=hex_to_rgb(spec.date_pill_bg))
        cd.text((190, 384), "Today", fill=hex_to_rgb(spec.date_pill_text), font=font_xs)

        # Left Incoming Bubble
        cd.rounded_rectangle((16, 416, 272, 466), radius=16, fill=hex_to_rgb(spec.left_bubble_bg))
        cd.text((28, 426), "Is this really Android WhatsApp?!", fill=hex_to_rgb(spec.left_bubble_text), font=font_sm)
        cd.text((214, 448), "9:40 AM", fill=hex_to_rgb(spec.left_bubble_time), font=font_xs)

        # Right Outgoing Bubble
        cd.rounded_rectangle((112, 480, card_w - 16, 546), radius=16, fill=hex_to_rgb(spec.right_bubble_bg))
        cd.text((126, 490), "100% iPhone WhatsApp theme!", fill=hex_to_rgb(spec.right_bubble_text), font=font_sm)
        cd.text((126, 510), "Exact bars, bubbles & doodles.", fill=hex_to_rgb(spec.right_bubble_text), font=font_sm)
        cd.text((card_w - 94, 528), "9:41 AM", fill=hex_to_rgb(spec.right_bubble_time), font=font_xs)
        cd.text((card_w - 42, 528), "✓✓", fill=(52, 183, 241), font=font_xs)

        # iOS 14+ Bottom Composer Bar (y = 660..712)
        cd.rectangle((0, 656, card_w, 712), fill=hex_to_rgb(spec.composer_bar_bg))
        cd.line((0, 656, card_w, 656), fill=hex_to_rgb(spec.row_divider), width=1)
        cd.text((14, 673), "+", fill=hex_to_rgb(spec.composer_icon_color), font=font_lg)
        cd.rounded_rectangle((42, 666, card_w - 86, 702), radius=18, fill=hex_to_rgb(spec.composer_pill_bg))
        cd.text((56, 676), "Message", fill=hex_to_rgb(spec.row_subtitle), font=font_sm)
        cd.ellipse((card_w - 74, 666, card_w - 42, 698), fill=hex_to_rgb(spec.composer_send_circle_bg))
        cd.text((card_w - 64, 674), "➤", fill=hex_to_rgb(spec.composer_icon_color), font=font_sm)
        # Crisp vector microphone icon
        mic_col = hex_to_rgb(spec.composer_icon_color)
        mx, my = card_w - 24, 673
        cd.rounded_rectangle((mx - 4, my, mx + 4, my + 12), radius=4, outline=mic_col, width=2)
        cd.arc((mx - 7, my + 4, mx + 7, my + 16), start=0, end=180, fill=mic_col, width=2)
        cd.line((mx, my + 16, mx, my + 20), fill=mic_col, width=2)

        # Footer label bar (y = 712..760)
        footer_bg = (28, 28, 30) if spec.is_dark else (242, 242, 247)
        cd.rectangle((0, 712, card_w, card_h), fill=footer_bg)
        cd.text((16, 726), spec.slug, fill=hex_to_rgb(spec.accent_hex), font=font_md)

        # Round card corners
        corner_mask = Image.new("L", (card_w, card_h), 0)
        ImageDraw.Draw(corner_mask).rounded_rectangle((0, 0, card_w, card_h), radius=26, fill=255)
        bg_patch = Image.new("RGB", (card_w, card_h), (242, 242, 247))
        rounded_card = Image.composite(card, bg_patch, corner_mask)
        canvas.paste(rounded_card, (x0, y0))

    canvas.save(out_path, format="PNG", optimize=True)


def main() -> None:
    if not DOODLE_MASK_PATH.exists():
        raise FileNotFoundError(f"Missing doodle mask: {DOODLE_MASK_PATH}")

    mask = Image.open(DOODLE_MASK_PATH).convert("L")
    THEMES_DIR.mkdir(parents=True, exist_ok=True)

    for spec in THEMES:
        out_dir = THEMES_DIR / spec.slug
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write <slug>.xml
        xml_path = out_dir / f"{spec.slug}.xml"
        xml_text = build_xml_content(spec)
        xml_path.write_text(xml_text, encoding="utf-8")

        # Validate XML structure & element types
        parsed = ET.fromstring(xml_text)
        assert parsed.tag == "map", f"{spec.slug}: root tag must be <map>"
        assert len(parsed) > 100, f"{spec.slug}: expected full preference set"

        # 2. Render <slug>_w.jpg & <slug>_homeW.jpg
        chat_wall_path, home_wall_path = render_wallpapers(spec, mask, out_dir)

        # 3. Package <slug>.zip with all 3 files at the archive root (YoThemes/GoldThemes format)
        zip_path = out_dir / f"{spec.slug}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in (xml_path, chat_wall_path, home_wall_path):
                zf.write(file_path, arcname=file_path.name)

        print(
            f"[OK] {spec.slug:20s} | "
            f"xml={xml_path.stat().st_size / 1024:5.2f} KB | "
            f"w={chat_wall_path.stat().st_size / 1024:6.2f} KB | "
            f"homeW={home_wall_path.stat().st_size / 1024:4.2f} KB | "
            f"zip={zip_path.stat().st_size / 1024:6.2f} KB"
        )

    preview_path = ASSETS_DIR / "ios_themes_preview.png"
    build_showcase_preview(mask, preview_path)
    print(f"[OK] Showcase preview -> {preview_path} ({preview_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
