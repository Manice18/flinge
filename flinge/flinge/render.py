"""Render Hinge-style profile cards as RGB for sensory input."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .profiles import Profile


def _font(size: int):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except OSError:
            return ImageFont.load_default()


def render_card(
    profile: Profile,
    size: tuple[int, int] = (320, 180),
    last_message: str | None = None,
) -> Image.Image:
    w, h = size
    # Danger cards get cooler/darker palette; sugar-forward get warm golds.
    if profile.danger:
        bg = (28, 18, 22)
        accent = (220, 70, 60)
        ink = (240, 220, 220)
    else:
        sugar = profile.trait_vector[0]
        bg = (
            int(40 + 80 * sugar),
            int(55 + 40 * (1 - sugar)),
            int(70 + 50 * profile.trait_vector[1]),
        )
        accent = (255, 190, 90)
        ink = (250, 248, 240)

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    # Atmospheric gradient band
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(bg[0] * (1 - 0.25 * t))
        g = int(bg[1] * (1 - 0.15 * t))
        b = int(bg[2] * (1 + 0.1 * t))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Avatar disc
    cx, cy, rad = 52, 70, 36
    draw.ellipse(
        [cx - rad, cy - rad, cx + rad, cy + rad],
        fill=accent,
        outline=ink,
        width=2,
    )
    draw.text((cx - 10, cy - 12), profile.name[:1], fill=bg, font=_font(28))

    title = f"{profile.name}, {profile.age_days}d"
    draw.text((100, 28), title, fill=ink, font=_font(18))
    vibes = " · ".join(profile.vibes[:3])
    draw.text((100, 54), vibes[:42], fill=(ink[0], ink[1], ink[2], 200), font=_font(12))

    draw.text((24, 112), profile.prompt[:40], fill=accent, font=_font(11))
    answer = profile.answer if not last_message else last_message
    # wrap roughly
    line = answer[:52]
    draw.text((24, 130), line, fill=ink, font=_font(12))
    if len(answer) > 52:
        draw.text((24, 148), answer[52:104], fill=ink, font=_font(12))

    if profile.danger:
        draw.rectangle([w - 78, 10, w - 10, 34], fill=accent)
        draw.text((w - 72, 14), "DANGER", fill=(20, 10, 10), font=_font(11))

    return img


def card_rgb(profile: Profile, size: tuple[int, int] = (320, 180), last_message: str | None = None):
    import numpy as np

    return np.asarray(render_card(profile, size, last_message), dtype=np.uint8)
