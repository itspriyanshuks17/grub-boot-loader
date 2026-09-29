"""Theme definitions for gen_grub_themes.py. Each theme() returns a spec dict."""
import os, math
import numpy as np
from PIL import Image, ImageDraw
import gfxlib as G
from gfxlib import W, H, rgb

ROOT = G.ROOT
LOGO_WAVE = lambda: G.load_alpha_logo(os.path.join(ROOT, "tools", "assets", "logos", "wave-mark.png"))       # AuroraBoot mark
_MQ_FULL = lambda: G.load_alpha_logo(os.path.join(ROOT, "tools", "assets", "logos", "marquardt-logo.png"))     # mark + wordmark


def _mq_parts():
    full = _MQ_FULL()
    # top ~62 % is the round "m" mark, bottom is the MARQUARDT wordmark
    rows = np.where(full.max(axis=1) < 0.05)[0]
    split = None
    for r in rows:
        if 0.3 * full.shape[0] < r < 0.75 * full.shape[0]:
            split = r
            break
    split = split or int(full.shape[0] * 0.55)
    mark, word = full[:split], full[split:]
    def trim(a):
        ys, xs = np.where(a > 0.05)
        return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return full, trim(mark), trim(word)


def heart(img, cx, cy, s, color, opacity=1.0):
    ss = 6
    im = Image.new("L", (int(s * 3 * ss), int(s * 3 * ss)), 0)
    d = ImageDraw.Draw(im)
    c = im.size[0] / 2
    r = s * ss * 0.5
    d.ellipse((c - r * 1.0, c - r * 1.2, c, c - r * 0.2 + r * 0.0), fill=255)
    d.ellipse((c, c - r * 1.2, c + r * 1.0, c - r * 0.2), fill=255)
    d.polygon([(c - r * 0.98, c - r * 0.55), (c + r * 0.98, c - r * 0.55), (c, c + r * 1.05)], fill=255)
    m = im.resize((int(s * 3), int(s * 3)), Image.LANCZOS)
    full = Image.new("L", (W, H), 0)
    full.paste(m, (int(cx - s * 1.5), int(cy - s * 1.5)))
    a = np.asarray(full, dtype=np.float32) / 255 * opacity
    img[:] = img * (1 - a[:, :, None]) + rgb(color)[None, None, :] * a[:, :, None]


def credit(img, cx, y, color, opacity=0.55, align="center"):
    f = G.font("Medium", 18)
    s = "Made with"
    t2 = "by Priyanshu Kumar Sharma"
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    w1, w2 = d.textlength(s, font=f), d.textlength(t2, font=f)
    tot = w1 + 12 + 18 + 12 + w2
    x = cx - tot / 2 if align == "center" else (cx - tot if align == "right" else cx)
    G.text(img, s, x, y, f, color, anchor="lm", opacity=opacity)
    heart(img, x + w1 + 12 + 9, y - 1, 6, "#ff4d6d", opacity=min(1, opacity + 0.3))
    G.text(img, t2, x + w1 + 12 + 18 + 12, y, f, color, anchor="lm", opacity=opacity)




THEMES = {}


def theme(fn):
    THEMES[fn.__name__] = fn
    return fn


# =============================================================== AURORA (centre, glass cards)
@theme
def aurora():
    A, B = "#2de3b5", "#7c5cff"

    def paint():
        img = G.sky([(0, "#02050d"), (0.4, "#06112b"), (0.72, "#0a1a3b"), (1, "#040919")])
        G.glow(img, 960, 330, 900, 420, "#123a6b", 0.18)
        G.ribbons(img, [
            dict(y=0.36, amp=0.05, freq=1.1, phase=0.05, height=0.20, c0="#1fe0b0", c1="#3a7bff", gain=0.50, seed=2),
            dict(y=0.30, amp=0.06, freq=0.9, phase=0.42, height=0.22, c0="#6a4dff", c1="#1fd6c0", gain=0.36, seed=5),
            dict(y=0.42, amp=0.04, freq=1.6, phase=0.71, height=0.14, c0="#2de3b5", c1="#7c5cff", gain=0.30, seed=9),
        ])
        G.stars(img, 700, seed=4, ymax=0.62, tint="#cfe6ff")
        G.silhouette(img, 905, [46, 22, 9], "#040914", seed=7, rim="#2de3b5", rim_w=1.6, fade_to="#02050b")
        G.silhouette(img, 960, [30, 14, 6], "#02050b", seed=13)
        G.vignette(img, 0.5)
        G.paste_mask(img, LOGO_WAVE(), 960, 150, 116, "#ffffff", 0.95, glow_color=A, glow_amt=0.55)
        G.text(img, "Aurora", 960, 268, G.font("Bold", 62), "#ffffff", anchor="mm", glow=A, glow_amt=0.25)
        G.text(img, "Choose an operating system", 960, 326, G.font("Medium", 26), "#9fe9d6", anchor="mm", opacity=0.85)
        G.keycap_row(img, [("UD", "Select"), ("Enter", "Boot"), ("E", "Edit"), ("C", "Console")], 960, 1012,
                     A, "#bff5e6", "#2de3b5")
        credit(img, 960, 1054, "#7fb6c9", 0.5)
        return img

    return dict(
        title="Aurora", accent=A, trough="#0d2a40", desktop_color="#050a1a",
        font_item="ABText Regular 24", font_sel="ABText Bold 24", font_small="ABText Regular 20",
        item_color="#b7f3e3", sel_color="#ffffff", countdown_color="#8fe8d0",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=15, corner=30, fill="#0d2540", fill_a=0.42, border="#2de3b5", border_w=2, border_a=0.20),
            dict(prefix="select", radius=15, corner=30, fill="#12483f", fill_a=0.62, border="#2de3b5", border_w=2,
                 border_a=1.0, glow="#2de3b5", glow_sigma=7, glow_a=0.50),
            dict(prefix="trough", radius=2, fill="#0d2a40", fill_a=0.95),
            dict(prefix="fill", radius=2, fill="#2de3b5", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left="50%-330", top=430, width=660, height=470, item_h=26, spacing=42, pad=14, icon=40, icon_space=18),
            progress=dict(kind="bar", left="50%-330", top=940, width=660, height=2),
            countdown=dict(left=0, top=956, width="100%", align="center", text="Booting in %d seconds"),
        ),
    )


# =============================================================== EMBER (left rail, warm)
@theme
def ember():
    A, B = "#ff8a3d", "#ffcf6b"

    def paint():
        img = G.sky([(0, "#0b0503"), (0.45, "#170a06"), (0.8, "#1c0d06"), (1, "#0a0402")])
        G.glow(img, 1500, 760, 1100, 620, "#3a1608", 0.65)
        G.glow(img, 300, 120, 700, 420, "#2a1206", 0.35)
        G.stars(img, 260, seed=21, ymax=0.4, tint="#ffd8b0", big=6, bright=0.7)
        for i, (r, seed) in enumerate([(760, 31), (860, 32), (960, 33)]):
            im = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(im)
            d.arc((960 - r, 700 - r, 960 + r, 700 + r), 200, 340, fill=255, width=2)
            a = np.asarray(im, dtype=np.float32) / 255
            img[:] = img + rgb(A)[None, None, :] * a[:, :, None] * (0.10 - i * 0.02)
        G.silhouette(img, 1060, [32, 52, 24, 38], "#0a0402", seed=41, rim="#ff8a3d", rim_w=1.4)
        G.sparks(img, 90, 51, "#ffb15c", region=(0.68, 0.95))
        G.vignette(img, 0.55)
        lx = 150
        G.paste_mask(img, LOGO_WAVE(), lx + 46, 118, 92, "#ffffff", 0.95, glow_color=A, glow_amt=0.6)
        G.text(img, "Ember", lx, 210, G.font("Bold", 54), "#ffffff", anchor="lm", glow=A, glow_amt=0.25)
        G.text(img, "Choose an operating system", lx, 250, G.font("Medium", 22), "#f3c79a", anchor="lm", opacity=0.85)
        G.keycap_row(img, [("UD", "Select"), ("Enter", "Boot"), ("E", "Edit"), ("C", "Console")], lx, 1006,
                     A, "#f3c79a", "#ff8a3d", align="left")
        credit(img, lx, 1048, "#c98a55", 0.55, align="left")
        return img

    return dict(
        title="Ember", accent=A, trough="#2a1206", desktop_color="#0a0402",
        font_item="ABText Regular 24", font_sel="ABText Bold 24", font_small="ABText Regular 20",
        item_color="#e8c6a4", sel_color="#ffffff", countdown_color="#ffb15c",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=10, fill="#2a1206", fill_a=0.35, border="#ff8a3d", border_w=1, border_a=0.14, accent_left="#ff8a3d", accent_w=3),
            dict(prefix="select", radius=10, corner=24, fill="#3a1a08", fill_a=0.75, border="#ffb15c", border_w=2, border_a=1.0,
                 glow="#ff8a3d", glow_sigma=6, glow_a=0.55, accent_left="#ffcf6b", accent_w=4),
            dict(prefix="trough", radius=2, fill="#2a1206", fill_a=0.9),
            dict(prefix="fill", radius=2, fill="#ff8a3d", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left=150, top=290, width=620, height=680, item_h=58, spacing=16, pad=16, icon=36, icon_space=16),
            progress=dict(kind="bar", left=150, top=930, width=620, height=3),
            countdown=dict(left=150, top=950, width=620, align="left", text="Booting default in %d seconds"),
        ),
    )


# =============================================================== GLACIER (right-aligned, cool)
@theme
def glacier():
    A, B = "#5fd0ff", "#eaf7ff"

    def paint():
        img = G.sky([(0, "#020a14"), (0.4, "#04182c"), (0.75, "#0a2b46"), (1, "#already" if False else "#03101d")])
        G.glow(img, 1400, 240, 1000, 480, "#123a56", 0.4)
        G.stars(img, 500, seed=61, ymax=0.5, tint="#dff3ff")
        G.silhouette(img, 760, [120, 200, 90, 150, 60], "#0a2c46", seed=71, ridged=True, rim="#bfe9ff", rim_w=1.2,
                     fade_to="#04121f", snow="#eaf7ff")
        G.silhouette(img, 860, [70, 130, 50], "#062032", seed=77, ridged=True, fade_to="#03101d")
        G.vignette(img, 0.5)
        rx = 1920 - 150
        G.paste_mask(img, LOGO_WAVE(), rx - 46, 118, 92, "#ffffff", 0.95, glow_color=A, glow_amt=0.5)
        G.text(img, "Glacier", rx, 210, G.font("Bold", 54), "#ffffff", anchor="rm", glow=A, glow_amt=0.2)
        G.text(img, "Choose an operating system", rx, 250, G.font("Medium", 22), "#bfe6f5", anchor="rm", opacity=0.85)
        G.keycap_row(img, [("UD", "Select"), ("Enter", "Boot"), ("E", "Edit"), ("C", "Console")], rx, 990,
                     A, "#dff3ff", "#5fd0ff", align="right")
        credit(img, rx, 1044, "#7fb0c9", 0.55, align="right")
        return img

    return dict(
        title="Glacier", accent=A, trough="#0c2e44", desktop_color="#03101d",
        font_item="ABText Regular 23", font_sel="ABText Bold 23", font_small="ABText Regular 19",
        item_color="#cdeeff", sel_color="#062032", countdown_color="#bfe6f5",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=8, fill="#0c2e44", fill_a=0.40, border="#5fd0ff", border_w=1, border_a=0.18),
            dict(prefix="select", radius=8, corner=22, fill="#eaf7ff", fill_a=0.92, border="#ffffff", border_w=1, border_a=0.6,
                 glow="#5fd0ff", glow_sigma=6, glow_a=0.5),
            dict(prefix="trough", radius=2, fill="#0c2e44", fill_a=0.9),
            dict(prefix="fill", radius=2, fill="#5fd0ff", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left="100%-770", top=330, width=620, height=520, item_h=54, spacing=18, pad=14, icon=38, icon_space=16),
            progress=dict(kind="bar", left="100%-770", top=896, width=620, height=3),
            countdown=dict(left="100%-770", top=914, width=620, align="right", text="Booting in %d seconds"),
        ),
    )


# =============================================================== NEON (chamfered, synthwave)
@theme
def neon():
    A, B = "#ff2fd6", "#33e6ff"

    def paint():
        img = G.sky([(0, "#050014"), (0.45, "#12002b"), (0.8, "#1d0135"), (1, "#03000c")])
        G.glow(img, 960, 900, 1400, 500, "#3a0a55", 0.55)
        ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        grid_y0 = 760
        for gy in range(grid_y0, H, 34):
            t = (gy - grid_y0) / (H - grid_y0)
            im = Image.new("L", (W, H), 0)
            ImageDraw.Draw(im).line((0, gy, W, gy), fill=255, width=1)
            a = np.asarray(im, dtype=np.float32) / 255 * (0.22 * (1 - t * 0.6))
            img[:] = img + rgb(B)[None, None, :] * a[:, :, None]
        cx = 960
        for gx in range(-1600, 1600, 90):
            x0, y0 = cx + gx * 0.18, grid_y0
            x1, y1 = cx + gx * 2.2, H
            im = Image.new("L", (W, H), 0)
            ImageDraw.Draw(im).line((x0, y0, x1, y1), fill=255, width=1)
            a = np.asarray(im, dtype=np.float32) / 255 * 0.16
            img[:] = img + rgb(B)[None, None, :] * a[:, :, None]
        sun_y = grid_y0
        for i in range(6):
            r = 210 - i * 30
            im = Image.new("L", (W, H), 0)
            ImageDraw.Draw(im).ellipse((cx - r, sun_y - r, cx + r, sun_y + r), fill=255)
            a = np.asarray(im, dtype=np.float32) / 255 * 0.05
            img[:] = img + rgb(A)[None, None, :] * a[:, :, None]
        G.stars(img, 260, seed=91, ymax=0.5, tint="#e6d6ff", big=4, bright=0.6)
        G.vignette(img, 0.45)
        G.paste_mask(img, LOGO_WAVE(), 960, 120, 92, "#ffffff", 0.95, glow_color=B, glow_amt=0.6)
        G.text(img, "NEON", 960, 216, G.font("Bold", 56), "#ffffff", anchor="mm", spacing=10, glow=A, glow_amt=0.4)
        G.text(img, "CHOOSE AN OPERATING SYSTEM", 960, 258, G.font("Medium", 20), "#ff9be9", anchor="mm", spacing=3, opacity=0.85)
        G.keycap_row(img, [("UD", "SELECT"), ("Enter", "BOOT"), ("E", "EDIT"), ("C", "CONSOLE")], 960, 1006,
                     B, "#eafcff", "#33e6ff")
        credit(img, 960, 1048, "#a877c9", 0.55)
        return img

    return dict(
        title="Neon", accent=A, trough="#26063a", desktop_color="#050014",
        font_item="ABText Regular 22", font_sel="ABText Bold 22", font_small="ABText Regular 19",
        item_color="#e3c9ff", sel_color="#ffffff", countdown_color="#ff9be9",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=2, cut=10, corner=13, fill="#1a0430", fill_a=0.5, border="#33e6ff", border_w=1, border_a=0.30),
            dict(prefix="select", radius=2, cut=10, corner=22, fill="#2a0850", fill_a=0.72, border="#ff2fd6", border_w=2, border_a=1.0,
                 glow="#ff2fd6", glow_sigma=3, glow_a=0.6),
            dict(prefix="trough", radius=1, fill="#26063a", fill_a=0.9),
            dict(prefix="fill", radius=1, fill="#ff2fd6", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left="50%-320", top=300, width=640, height=700, item_h=50, spacing=17, pad=14, icon=38, icon_space=16),
            progress=dict(kind="bar", left="50%-320", top=946, width=640, height=3),
            countdown=dict(left=0, top=966, width="100%", align="center", text="LAUNCH IN %d SECONDS"),
        ),
    )


# =============================================================== MARQUARDT (brand, centred pills)
@theme
def marquardt():
    A, B = "#00b3a4", "#0d3b3a"

    def paint():
        img = G.sky([(0, "#03110f"), (0.45, "#04211c"), (0.8, "#062c26"), (1, "#020a09")])
        G.glow(img, 960, 260, 1100, 480, "#0c4a41", 0.4)
        G.ribbons(img, [
            dict(y=0.30, amp=0.035, freq=0.8, phase=0.1, height=0.16, c0="#00d8c2", c1="#00988a", gain=0.30, seed=101),
        ])
        G.stars(img, 260, seed=102, ymax=0.45, tint="#bdfff2", big=4, bright=0.6)
        G.vignette(img, 0.5)
        full, mark, word = _mq_parts()
        G.paste_mask(img, mark, 960, 128, 108, "#ffffff", 0.97, glow_color=A, glow_amt=0.5)
        G.paste_mask(img, word, 960, 214, 40, "#ffffff", 0.92)
        G.text(img, "Choose an operating system", 960, 268, G.font("Medium", 24), "#8fe3d8", anchor="mm", opacity=0.85)
        G.keycap_row(img, [("UD", "Select"), ("Enter", "Boot"), ("E", "Edit"), ("C", "Console")], 960, 1006,
                     A, "#d6fff6", "#00b3a4")
        credit(img, 960, 1048, "#5fae9f", 0.55)
        return img

    return dict(
        title="Marquardt", accent=A, trough="#0c2e29", desktop_color="#020a09",
        font_item="ABText Regular 23", font_sel="ABText Bold 23", font_small="ABText Regular 19",
        item_color="#cdf5ee", sel_color="#04211c", countdown_color="#8fe3d8",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=16, corner=17, fill="#0c2e29", fill_a=0.45, border="#00b3a4", border_w=1, border_a=0.20),
            dict(prefix="select", radius=16, corner=17, fill="#e7fffb", fill_a=0.95, border="#00b3a4", border_w=2, border_a=0.9),
            dict(prefix="trough", radius=3, fill="#0c2e29", fill_a=0.9),
            dict(prefix="fill", radius=3, fill="#00b3a4", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left="50%-300", top=300, width=600, height=700, item_h=52, spacing=15, pad=14, icon=36, icon_space=16),
            progress=dict(kind="bar", left="50%-300", top=928, width=600, height=3),
            countdown=dict(left=0, top=954, width="100%", align="center", text="Booting in %d seconds"),
        ),
        icon_blend=0.0,
    )


# =============================================================== MQ (side rail, minimal)
@theme
def mq():
    A, B = "#22e0c8", "#0a2b28"

    def paint():
        img = G.sky([(0, "#03100e"), (0.5, "#04211d"), (1, "#010807")])
        G.glow(img, 260, 540, 620, 900, "#0a3a34", 0.5)
        G.stars(img, 220, seed=201, ymax=0.55, tint="#bdfff2", big=3, bright=0.5)
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).rectangle((0, 0, 3, H), fill=255)
        a = np.asarray(im, dtype=np.float32) / 255
        img[:] = img + rgb(A)[None, None, :] * a[:, :, None] * 0.9
        G.vignette(img, 0.45)
        full, mark, word = _mq_parts()
        cx = 210
        G.paste_mask(img, mark, cx, 150, 108, "#ffffff", 0.97, glow_color=A, glow_amt=0.55)
        G.paste_mask(img, word, cx, 226, 30, "#ffffff", 0.85)
        G.text(img, "Boot Manager", cx, 288, G.font("Medium", 22), "#8fe3d8", anchor="mm", opacity=0.85)
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).line((cx - 150, 330, cx + 150, 330), fill=255, width=1)
        a = np.asarray(im, dtype=np.float32) / 255
        img[:] = img + rgb(A)[None, None, :] * a[:, :, None] * 0.4
        f = G.font("Medium", 18)
        rows = [("UD", "Select"), ("Enter", "Boot"), ("E", "Edit config"), ("C", "Console"), ("F2", "Firmware")]
        y = 760
        for key, label in rows:
            box = (cx - 90, y - 16, cx - 90 + 62, y + 16)
            G.rounded(img, box, 8, outline=A, fill=A, width=1, fill_a=0.10, out_a=0.55)
            if key == "UD":
                kc = (cx - 59, y)
                im = Image.new("L", (W, H), 0)
                dd = ImageDraw.Draw(im)
                dd.polygon([(kc[0] - 7, kc[1] - 6), (kc[0] - 12, kc[1] + 2), (kc[0] - 2, kc[1] + 2)], fill=255)
                dd.polygon([(kc[0] + 7, kc[1] + 6), (kc[0] + 2, kc[1] - 2), (kc[0] + 12, kc[1] - 2)], fill=255)
                aa = np.asarray(im, dtype=np.float32) / 255
                img[:] = img * (1 - aa[:, :, None] * .95) + rgb("#d6fff6")[None, None, :] * (aa[:, :, None] * .95)
            else:
                G.text(img, key, cx - 59, y + 1, f, "#d6fff6", anchor="mm")
            G.text(img, label, cx - 18, y + 1, f, "#bfe9df", anchor="lm", opacity=0.8)
            y += 46
        credit(img, cx, 990, "#5fae9f", 0.55, align="left")
        return img

    return dict(
        title="MQ", accent=A, trough="#0a2b28", desktop_color="#010807",
        font_item="ABText Regular 24", font_sel="ABText Bold 24", font_small="ABText Regular 19",
        item_color="#cdf5ee", sel_color="#ffffff", countdown_color="#8fe3d8",
        paint=paint,
        boxes=[
            dict(prefix="item", radius=12, fill="#0a2b28", fill_a=0.4, border="#22e0c8", border_w=1, border_a=0.16),
            dict(prefix="select", radius=12, corner=26, fill="#0f3d38", fill_a=0.85, border="#22e0c8", border_w=2, border_a=1.0,
                 glow="#22e0c8", glow_sigma=6, glow_a=0.55, accent_left="#22e0c8", accent_w=4),
            dict(prefix="trough", radius=2, fill="#0a2b28", fill_a=0.9),
            dict(prefix="fill", radius=2, fill="#22e0c8", fill_a=1.0),
        ],
        layout=dict(
            menu=dict(left=480, top=210, width=1260, height=620, item_h=58, spacing=18, pad=16, icon=40, icon_space=18),
            progress=dict(kind="bar", left=480, top=900, width=1260, height=3),
            countdown=dict(left=480, top=930, width=1260, align="left", text="Booting default entry in %d seconds"),
        ),
        icon_blend=0.0,
    )
