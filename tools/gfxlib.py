"""Small software renderer used by gen_grub_themes.py (numpy + Pillow only)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1920, 1080
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT_DIRS = [os.path.join(ROOT, "auroraboot", "assets", "fonts"), os.path.join(ROOT, "mq", "assets", "fonts"),
             "/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/poppins"]


def find_font(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit(f"font {name} not found (looked in {FONT_DIRS})")


def font(weight, size):
    return ImageFont.truetype(find_font(f"Poppins-{weight}.ttf"), size)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def to_img(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")


def from_img(im):
    return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


# ----------------------------------------------------------------- sky ----
def sky(stops, w=W, h=H):
    """Vertical gradient. stops = [(pos 0..1, '#hex'), ...]"""
    ys = np.linspace(0, 1, h, dtype=np.float32)
    out = np.zeros((h, w, 3), np.float32)
    pos = [p for p, _ in stops]
    cols = np.stack([rgb(c) for _, c in stops])
    for c in range(3):
        out[:, :, c] = np.interp(ys, pos, cols[:, c])[:, None]
    return out


def glow(img, cx, cy, rx, ry, color, strength):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
    img += rgb(color)[None, None, :] * (np.exp(-d * 2.2) * strength)[:, :, None]
    return img


def _noise1d(n, seed, octaves=4, base=6):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n, dtype=np.float32)
    out = np.zeros(n, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        k = base * (2 ** o)
        pts = rng.random(k + 2).astype(np.float32)
        out += amp * np.interp(x * k, np.arange(k + 2), pts)
        tot += amp
        amp *= 0.5
    return out / tot


def ribbons(img, specs, scale=2):
    """Aurora curtains. Each spec: dict(y, amp, freq, phase, height, c0, c1, gain, seed, x0, x1, tilt)."""
    h, w = img.shape[:2]
    hw, hh = w // scale, h // scale
    ys = np.arange(hh, dtype=np.float32)[:, None]
    xs = np.arange(hw, dtype=np.float32)[None, :]
    acc = np.zeros((hh, hw, 3), np.float32)
    for s in specs:
        seed = s.get("seed", 1)
        u_ = xs / hw
        base = (s["y"] * hh
                + s["amp"] * hh * np.sin(2 * math.pi * (s["freq"] * u_ + s["phase"]))
                + 0.45 * s["amp"] * hh * np.sin(2 * math.pi * (s["freq"] * 2.3 * u_ + s["phase"] * 1.7 + 0.3))
                + s.get("tilt", 0) * hh * (u_ - 0.5))
        hgt = s["height"] * hh * (0.55 + 0.9 * _noise1d(hw, seed, 4, 5))[None, :]
        u = base - ys                                    # >0 above the base line
        edge = 6.0 / scale * 2
        up = (1 - np.exp(-np.maximum(u, 0) / edge)) * np.exp(-np.maximum(u, 0) / hgt)
        below = 0.30 * np.exp(-(np.minimum(u, 0) / (14.0 / scale * 2)) ** 2)
        inten = up + below
        rays = 0.55 + 0.45 * _noise1d(hw, seed + 11, 5, 24)[None, :]
        inten = inten * rays
        x0, x1 = s.get("x0", 0.0), s.get("x1", 1.0)
        inten *= smooth(x0 - 0.001, x0 + 0.22, u_) * (1 - smooth(x1 - 0.22, x1 + 0.001, u_)) if (x0 > 0 or x1 < 1) else 1
        t = np.clip(np.maximum(u, 0) / (hgt * 2.2), 0, 1)[:, :, None]
        col = rgb(s["c0"])[None, None, :] * (1 - t) + rgb(s["c1"])[None, None, :] * t
        acc += col * inten[:, :, None] * s["gain"]
    acc_im = to_img(np.clip(acc, 0, 1)).filter(ImageFilter.GaussianBlur(1.2))
    up_im = acc_im.resize((w, h), Image.BICUBIC)
    a = from_img(up_im)
    img += a
    return img


def stars(img, n, seed=3, ymax=0.7, tint="#ffffff", big=14, bright=1.0):
    rng = np.random.default_rng(seed)
    im = to_img(np.zeros_like(img))
    d = ImageDraw.Draw(im)
    t = (np.array(rgb(tint)) * 255).astype(int)
    for i in range(n):
        x, y = rng.integers(0, W), int(rng.random() ** 1.3 * ymax * H)
        b = rng.random() ** 2.2 * bright
        c = tuple(int(v * b) for v in t)
        d.point((x, y), fill=c)
        if i < big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.point((x + dx, y + dy), fill=tuple(int(v * b * 0.45) for v in t))
    img += from_img(im.filter(ImageFilter.GaussianBlur(0.4))) * 1.6
    return img


def _ridge(xs, y0, amps, seed, ridged=False):
    rng = np.random.default_rng(seed)
    y = np.full_like(xs, y0, dtype=np.float32)
    for i, a in enumerate(amps):
        f = 1.7 * (2.05 ** i) + rng.random()
        ph = rng.random() * 6.28
        wave = np.sin(xs / W * 2 * math.pi * f + ph)
        y -= a * ((1 - np.abs(wave)) if ridged else wave)
    return y


def silhouette(img, y0, amps, color, seed, ridged=False, rim=None, rim_w=2.0, fade_to=None, snow=None):
    """Fill everything below a ridge line. Optional bright rim along the ridge and snow caps."""
    h, w = img.shape[:2]
    xs = np.arange(w, dtype=np.float32)
    ridge = _ridge(xs, y0, amps, seed, ridged)[None, :]
    ys = np.arange(h, dtype=np.float32)[:, None]
    d = ys - ridge                                   # >0 inside the mass
    m = smooth(-1.0, 1.0, d)[:, :, None]
    c0 = rgb(color)
    if fade_to is not None:
        t = np.clip(d / max(1, (h - y0)), 0, 1)[:, :, None]
        col = c0 * (1 - t) + rgb(fade_to) * t
    else:
        col = c0[None, None, :]
    if snow is not None:
        peak = smooth(0, 1, (y0 - ridge) / (max(amps) * 0.9))        # 1 near the tallest peaks
        cap = (1 - smooth(0, 46, d)) * peak
        col = col * (1 - (cap * 0.85)[:, :, None]) + rgb(snow)[None, None, :] * (cap * 0.85)[:, :, None]
    img[:] = img * (1 - m) + col * m
    if rim is not None:
        r = np.exp(-(np.abs(d) / rim_w) ** 2)[:, :, None]
        img += rgb(rim)[None, None, :] * r * 0.9
        img += rgb(rim)[None, None, :] * (np.exp(-np.maximum(-d, 0) / 26.0) * (d < 0) * 0.18)[:, :, None]
    return img


def sparks(img, n, seed, color, region=(0.35, 0.95), size=(1, 4), spread=0.35):
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    c = (rgb(color) * 255).astype(int)
    for _ in range(n):
        x = rng.integers(0, W)
        y = int((region[0] + (region[1] - region[0]) * rng.random() ** 0.6) * H)
        s = rng.uniform(*size)
        b = rng.random() ** 1.5
        d.ellipse((x - s, y - s, x + s, y + s), fill=tuple(int(v * b) for v in c))
    g = im.filter(ImageFilter.GaussianBlur(2.2))
    img += from_img(im) * 0.9 + from_img(g) * 1.5
    return img


def vignette(img, strength=0.55):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xs - w / 2) / (w * 0.75)) ** 2 + ((ys - h / 2) / (h * 0.85)) ** 2)
    img *= (1 - strength * smooth(0.45, 1.15, d))[:, :, None]
    return img


# ----------------------------------------------------------- logo / text ----
def load_alpha_logo(path, invert=False, crop=True):
    """Turn a logo (dark-on-white or white-on-black or RGBA) into a float alpha mask."""
    im = Image.open(path)
    if im.mode == "RGBA" and np.asarray(im)[:, :, 3].min() < 250:
        a = np.asarray(im)[:, :, 3].astype(np.float32) / 255
    else:
        g = np.asarray(im.convert("RGB"), dtype=np.float32)[:, :, 0] / 255
        a = g if invert else 1 - g
    if crop:
        ys, xs = np.where(a > 0.05)
        a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return a


def paste_mask(img, mask, cx, cy, height, color, opacity=1.0, glow_color=None, glow_amt=0.0):
    hh = int(height)
    ww = max(1, int(mask.shape[1] * hh / mask.shape[0]))
    m = Image.fromarray((mask * 255).astype(np.uint8)).resize((ww, hh), Image.LANCZOS)
    full = Image.new("L", (W, H), 0)
    full.paste(m, (int(cx - ww / 2), int(cy - hh / 2)))
    a = np.asarray(full, dtype=np.float32) / 255
    if glow_color is not None and glow_amt > 0:
        g = np.asarray(full.filter(ImageFilter.GaussianBlur(hh * 0.18)), dtype=np.float32) / 255
        img += rgb(glow_color)[None, None, :] * (g * glow_amt)[:, :, None]
    img[:] = img * (1 - a[:, :, None] * opacity) + rgb(color)[None, None, :] * (a[:, :, None] * opacity)
    return img


def text(img, s, x, y, fnt, color, anchor="la", opacity=1.0, spacing=0, glow=None, glow_amt=0.0):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    if spacing:
        # manual letter spacing (anchor left/middle/right supported)
        widths = [d.textlength(ch, font=fnt) + spacing for ch in s]
        total = sum(widths) - spacing
        x0 = x - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
        for ch, wd in zip(s, widths):
            d.text((x0, y), ch, font=fnt, fill=255, anchor="l" + anchor[1])
            x0 += wd
    else:
        d.text((x, y), s, font=fnt, fill=255, anchor=anchor)
    a = np.asarray(im, dtype=np.float32) / 255
    if glow is not None and glow_amt > 0:
        g = np.asarray(im.filter(ImageFilter.GaussianBlur(9)), dtype=np.float32) / 255
        img += rgb(glow)[None, None, :] * (g * glow_amt)[:, :, None]
    img[:] = img * (1 - a[:, :, None] * opacity) + rgb(color)[None, None, :] * (a[:, :, None] * opacity)
    return img


def rounded(img, box, r, outline=None, fill=None, width=2, fill_a=1.0, out_a=1.0):
    ss = 3
    x0, y0, x1, y1 = box
    im = Image.new("L", (W * 1, H * 1), 0)
    layer_f = Image.new("L", (int((x1 - x0 + 8) * ss), int((y1 - y0 + 8) * ss)), 0)
    layer_o = layer_f.copy()
    df, do = ImageDraw.Draw(layer_f), ImageDraw.Draw(layer_o)
    bx = (4 * ss, 4 * ss, (4 + x1 - x0) * ss, (4 + y1 - y0) * ss)
    df.rounded_rectangle(bx, r * ss, fill=255)
    do.rounded_rectangle(bx, r * ss, outline=255, width=int(width * ss))
    for layer, col, a in ((layer_f, fill, fill_a), (layer_o, outline, out_a)):
        if col is None:
            continue
        m = layer.resize((int(x1 - x0 + 8), int(y1 - y0 + 8)), Image.LANCZOS)
        full = Image.new("L", (W, H), 0)
        full.paste(m, (int(x0 - 4), int(y0 - 4)))
        mm = np.asarray(full, dtype=np.float32) / 255 * a
        img[:] = img * (1 - mm[:, :, None]) + rgb(col)[None, None, :] * mm[:, :, None]
    return img


def keycap_row(img, items, cx, cy, accent, text_col, key_col, size=22, gap=44, align="center"):
    """items = [('Enter', 'Boot'), ('UD', 'Select') ...]; 'UD' and 'LR' draw arrow glyphs."""
    fk, fl = font("Medium", size - 4), font("Medium", size)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    layout = []
    total = 0
    for key, label in items:
        kw = (44 if key in ("UD", "LR") else int(d.textlength(key, font=fk)) + 22)
        lw = int(d.textlength(label, font=fl))
        layout.append((key, label, kw, lw))
        total += kw + 12 + lw
    total += gap * (len(items) - 1)
    x = cx - total / 2 if align == "center" else (cx - total if align == "right" else cx)
    for key, label, kw, lw in layout:
        box = (x, cy - 18, x + kw, cy + 18)
        rounded(img, box, 9, outline=key_col, fill=key_col, width=2, fill_a=0.10, out_a=0.85)
        kc = (x + kw / 2, cy)
        if key in ("UD", "LR"):
            im = Image.new("L", (W * 1, H * 1), 0)
            dd = ImageDraw.Draw(im)
            if key == "UD":
                dd.polygon([(kc[0] - 9, cy - 8), (kc[0] - 15, cy + 1), (kc[0] - 3, cy + 1)], fill=255)
                dd.polygon([(kc[0] + 9, cy + 8), (kc[0] + 3, cy - 1), (kc[0] + 15, cy - 1)], fill=255)
            else:
                dd.polygon([(kc[0] - 9, cy), (kc[0] - 3, cy - 7), (kc[0] - 3, cy + 7)], fill=255)
                dd.polygon([(kc[0] + 9, cy), (kc[0] + 3, cy - 7), (kc[0] + 3, cy + 7)], fill=255)
            a = np.asarray(im, dtype=np.float32) / 255
            img[:] = img * (1 - a[:, :, None] * .95) + rgb(text_col)[None, None, :] * (a[:, :, None] * .95)
        else:
            text(img, key, kc[0], kc[1] + 1, fk, text_col, anchor="mm")
        text(img, label, x + kw + 12, cy + 1, fl, text_col, anchor="lm", opacity=0.75)
        x += kw + 12 + lw + gap
    return img


# ------------------------------------------------------- GRUB style boxes ----
_PARTS = ("nw", "n", "ne", "w", "c", "e", "sw", "s", "se")


def _sdf_round_box(px, py, hx, hy, r):
    qx, qy = np.abs(px) - (hx - r), np.abs(py) - (hy - r)
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r


def write_box(outdir, prefix, radius, fill, fill_a, corner=None, border=None, border_w=2, border_a=1.0,
              glow=None, glow_sigma=8, glow_a=0.0, accent_left=None, accent_w=0, top_light=0.0, cut=0):
    """Write <prefix>_{nw,n,ne,w,c,e,sw,s,se}.png as a 9-slice with `corner` px corners.
    The visible card is inset by `inset` so that glow fits in the corner pieces."""
    ss = 4
    need = (int(round(glow_sigma * 2.2)) if glow else 0) + int(radius) + 1 + (int(cut) if cut else 0)
    corner = max(corner or need, need)
    inset = corner - int(radius) - 1 - (int(cut) if cut else 0)   # transparent margin around the visible card
    S = 2 * corner + 8
    n = S * ss
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    px, py = (xs + 0.5) / ss - S / 2, (ys + 0.5) / ss - S / 2
    hx = hy = S / 2 - inset
    if cut:                                     # chamfered corners (neon)
        d = np.maximum(np.maximum(np.abs(px) - hx, np.abs(py) - hy), (np.abs(px) + np.abs(py) - (hx + hy - cut)) / 1.4142)
    else:
        d = _sdf_round_box(px, py, hx, hy, radius)
    inside = smooth(0.5, -0.5, d)
    rgba = np.zeros((n, n, 4), np.float32)
    f = rgb(fill)
    fa = inside * fill_a
    if top_light:
        fa = fa * (1 + top_light * smooth(0.0, -hy * 0.9, py / 1.0 * 0 + (py - hy * 0.2)) )
    rgba[..., :3] = f
    rgba[..., 3] = fa
    if glow:
        g = np.exp(-np.maximum(d, 0) / glow_sigma) * glow_a * (1 - inside)
        gc = rgb(glow)
        a0 = rgba[..., 3:4]
        ga = g[..., None]
        outa = a0 + ga * (1 - a0)
        rgba[..., :3] = np.where(outa > 1e-6, (rgba[..., :3] * a0 + gc * ga * (1 - a0)) / np.maximum(outa, 1e-6), 0)
        rgba[..., 3:4] = outa
    if border:
        ring = smooth(border_w / 2 + 0.6, border_w / 2 - 0.6, np.abs(d + border_w / 2)) * border_a
        bc = rgb(border)
        a0 = rgba[..., 3:4]
        ra = ring[..., None]
        outa = ra + a0 * (1 - ra)
        rgba[..., :3] = np.where(outa > 1e-6, (bc * ra + rgba[..., :3] * a0 * (1 - ra)) / np.maximum(outa, 1e-6), 0)
        rgba[..., 3:4] = outa
    if accent_left:
        bar = smooth(-0.5, 0.5, (px + hx) * -1 + accent_w) * inside if False else \
              inside * smooth(accent_w + 0.5, accent_w - 0.5, (px + hx))
        ac = rgb(accent_left)
        a0 = rgba[..., 3:4]
        ba = bar[..., None]
        outa = ba + a0 * (1 - ba)
        rgba[..., :3] = np.where(outa > 1e-6, (ac * ba + rgba[..., :3] * a0 * (1 - ba)) / np.maximum(outa, 1e-6), 0)
        rgba[..., 3:4] = outa
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").resize((S, S), Image.LANCZOS)
    c, mid = corner, S // 2
    pieces = {
        "nw": im.crop((0, 0, c, c)), "ne": im.crop((S - c, 0, S, c)),
        "sw": im.crop((0, S - c, c, S)), "se": im.crop((S - c, S - c, S, S)),
        "n": im.crop((mid, 0, mid + 1, c)), "s": im.crop((mid, S - c, mid + 1, S)),
        "w": im.crop((0, mid, c, mid + 1)), "e": im.crop((S - c, mid, S, mid + 1)),
        "c": im.crop((mid, mid, mid + 1, mid + 1)),
    }
    os.makedirs(outdir, exist_ok=True)
    for k, v in pieces.items():
        v.save(os.path.join(outdir, f"{prefix}_{k}.png"))


# ---------------------------------------------------------------- icons ----
def _tile(size, color, r=None):
    ss = 4
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = tuple(int(v * 255) for v in rgb(color))
    d.rounded_rectangle((0, 0, S - 1, S - 1), (r or size * 0.28) * ss, fill=c + (255,))
    return im, d, ss


def make_icon(kind, size, tile, glyph="#ffffff", ring="#ffffff"):
    im, d, ss = _tile(size, tile)
    S = size * ss
    g = tuple(int(v * 255) for v in rgb(glyph)) + (255,)
    cx = cy = S / 2
    if kind == "windows":
        a, gp = S * 0.20, S * 0.04
        s = (S - 2 * a - gp) / 2
        for i in range(2):
            for j in range(2):
                x, y = a + i * (s + gp), a + j * (s + gp)
                d.rectangle((x, y, x + s, y + s), fill=g)
    elif kind == "ubuntu":
        R = S * 0.27
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=g, width=int(S * 0.075))
        for ang in (-90, 30, 150):
            px, py = cx + R * math.cos(math.radians(ang)), cy + R * math.sin(math.radians(ang))
            r0 = S * 0.085
            d.ellipse((px - r0 - S * .03, py - r0 - S * .03, px + r0 + S * .03, py + r0 + S * .03), fill=tuple(int(v * 255) for v in rgb(tile)) + (255,))
            d.ellipse((px - r0, py - r0, px + r0, py + r0), fill=g)
    elif kind == "efi":            # chip
        b = S * 0.27
        d.rounded_rectangle((cx - b, cy - b, cx + b, cy + b), S * 0.05, outline=g, width=int(S * 0.07))
        for t in (-0.12, 0.12):
            for sgn in (-1, 1):
                d.line((cx + t * S, cy - sgn * b, cx + t * S, cy - sgn * (b + S * 0.09)), fill=g, width=int(S * 0.06))
                d.line((cx - sgn * b, cy + t * S, cx - sgn * (b + S * 0.09), cy + t * S), fill=g, width=int(S * 0.06))
        d.rectangle((cx - S * .08, cy - S * .08, cx + S * .08, cy + S * .08), fill=g)
    elif kind == "term":           # >_
        w = int(S * 0.075)
        d.line((S * .26, S * .34, S * .44, S * .5, S * .26, S * .66), fill=g, width=w, joint="curve")
        d.line((S * .52, S * .68, S * .74, S * .68), fill=g, width=w)
    elif kind == "os":
        R = S * 0.24
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=g, width=int(S * 0.07))
        d.ellipse((cx - S * .07, cy - S * .07, cx + S * .07, cy + S * .07), fill=g)
    else:                          # letter tile
        f = ImageFont.truetype(find_font("Poppins-Bold.ttf"), int(S * 0.56))
        d.text((cx, cy + S * 0.02), kind, font=f, fill=g, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


ICON_SET = {   # class -> (kind/letter, brand tile colour)
    "windows": ("windows", "#0d8ad6"), "ubuntu": ("ubuntu", "#e5522b"), "fedora": ("F", "#3c6eb4"),
    "arch": ("A", "#1793d1"), "archlinux": ("A", "#1793d1"), "debian": ("D", "#c70c4d"),
    "manjaro": ("M", "#1fa97a"), "linuxmint": ("M", "#5da542"), "mint": ("M", "#5da542"),
    "opensuse": ("S", "#2c9d3a"), "suse": ("S", "#2c9d3a"), "kali": ("K", "#2b6fb0"), "pop": ("P", "#3fb6c9"),
    "zorin": ("Z", "#1f8ad9"), "endeavouros": ("E", "#7f5fd0"), "nixos": ("N", "#5277c3"),
    "elementary": ("e", "#4a90d9"), "gentoo": ("G", "#6f5aa6"), "void": ("V", "#3e9c5b"),
    "gnu-linux": ("term", "#485468"), "gnu": ("term", "#485468"), "linux": ("term", "#485468"),
    "efi": ("efi", "#5b6577"), "uefi": ("efi", "#5b6577"), "os": ("os", "#4a5568"), "unknown": ("os", "#4a5568"),
    "recovery": ("term", "#8a5a2b"), "memtest": ("efi", "#8a5a2b"),
}


def write_icons(outdir, size, blend_to, blend=0.28):
    os.makedirs(outdir, exist_ok=True)
    acc = rgb(blend_to)
    for cls, (kind, tile) in ICON_SET.items():
        t = rgb(tile) * (1 - blend) + acc * blend
        col = "#%02x%02x%02x" % tuple(int(v * 255) for v in t)
        make_icon(kind, size, col).save(os.path.join(outdir, f"{cls}.png"))
