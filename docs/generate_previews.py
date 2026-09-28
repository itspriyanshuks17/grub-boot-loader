"""Generate illustrative GRUB menu previews from the bundled theme assets.

Requires Pillow: python -m pip install Pillow
Run from the repository root: python docs/generate_previews.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "img"
SIZE = (1280, 720)
SCALE = SIZE[0] / 1920
FONT_PATHS = (
    Path("C:/Windows/Fonts/consola.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
)

THEMES = {
    "aurora": ("#2de3b5", "#b0f0e0", "#7c5cff"),
    "ember": ("#ff8a3d", "#ffd0a0", "#e0245e"),
    "glacier": ("#5cc8ff", "#b8e8ff", "#2a6bff"),
    "neon": ("#ff3da5", "#ffb8e0", "#22e5ff"),
    "marquardt": ("#009aa6", "#c9e9ec", "#4f8f96"),
    "mq": ("#009aa6", "#c9e9ec", "#4f8f96"),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, color: str,
                  face: ImageFont.FreeTypeFont) -> None:
    bounds = draw.textbbox((0, 0), text, font=face)
    x = (SIZE[0] - (bounds[2] - bounds[0])) // 2
    draw.text((x, y), text, font=face, fill=color)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, (accent, item_color, hint_color) in THEMES.items():
        theme_dir = ROOT / "themes" / name
        background = Image.open(theme_dir / "background.png").convert("RGB")
        screen = background.resize(SIZE, Image.Resampling.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        draw_centered(draw, round(0.58 * SIZE[1]), "SELECT OPERATING SYSTEM",
                      accent, font(18))

        # Use the theme's actual left, center, and right selection textures.
        scale = SCALE
        left = Image.open(theme_dir / "select_w.png").convert("RGBA")
        center = Image.open(theme_dir / "select_c.png").convert("RGBA")
        right = Image.open(theme_dir / "select_e.png").convert("RGBA")
        tile_h = round(44 * scale)
        left = left.resize((round(left.width * scale), tile_h), Image.Resampling.LANCZOS)
        center = center.resize((max(1, round(center.width * scale)), tile_h), Image.Resampling.LANCZOS)
        right = right.resize((round(right.width * scale), tile_h), Image.Resampling.LANCZOS)

        menu_w = round(520 * scale)
        menu_x = (SIZE[0] - menu_w) // 2
        row_h = tile_h
        gap = round(8 * scale)
        menu_y = round(0.63 * SIZE[1])
        center_width = menu_w - left.width - right.width
        selection = Image.new("RGBA", (menu_w, row_h), (0, 0, 0, 0))
        selection.alpha_composite(left, (0, 0))
        for x in range(left.width, left.width + center_width, center.width):
            crop_w = min(center.width, left.width + center_width - x)
            selection.alpha_composite(center.crop((0, 0, crop_w, row_h)), (x, 0))
        selection.alpha_composite(right, (menu_w - right.width, 0))
        overlay.alpha_composite(selection, (menu_x, menu_y))

        menu_font = font(17)
        entries = ["Ubuntu", "Advanced options for Ubuntu", "Windows Boot Manager", "UEFI Firmware Settings"]
        text_x = menu_x + round(14 * scale)
        for index, entry in enumerate(entries):
            y = menu_y + index * (row_h + gap) + round(5 * scale)
            draw.text((text_x, y), entry,
                      font=menu_font,
                      fill="#ffffff" if index == 0 else item_color)

        # The theme defines a 520 by 6 pixel timeout bar at 90% screen height.
        bar_y = round(0.90 * SIZE[1])
        bar_w = round(520 * scale)
        bar_h = max(3, round(6 * scale))
        bar_x = (SIZE[0] - bar_w) // 2
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                               radius=bar_h // 2, fill="#20333a")
        draw.rounded_rectangle((bar_x, bar_y, bar_x + round(bar_w * 0.68), bar_y + bar_h),
                               radius=bar_h // 2, fill=accent)

        draw_centered(draw, round(0.93 * SIZE[1]), "Booting in 5 seconds", accent, font(15))
        draw_centered(draw, round(0.97 * SIZE[1]), "↑ ↓ select    Enter boot    E edit    C command line",
                      hint_color, font(13))

        result = Image.alpha_composite(screen, overlay).convert("RGB")
        result.save(OUTPUT / f"grub-{name}.webp", "WEBP", quality=88, method=6)


if __name__ == "__main__":
    main()
