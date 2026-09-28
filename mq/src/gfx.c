#include "gfx.h"

u32 *G_px; int G_w, G_h, G_scale16 = 65536;
static EFI_GRAPHICS_OUTPUT_PROTOCOL *gop;

#define NOOPT __attribute__((optimize("no-tree-loop-distribute-patterns")))
NOOPT void *memmove(void *d, const void *s, UINTN n) {
    u8 *a = d; const u8 *b = s;
    if (a < b) while (n--) *a++ = *b++; else { a += n; b += n; while (n--) *--a = *--b; }
    return d;
}

int isin(int a) { return sintab[a & 255]; }
int icos(int a) { return sintab[(a + 64) & 255]; }

static u32 isqrt32(u32 x) {
    u32 r = 0, b = 1u << 30;
    while (b > x) b >>= 2;
    while (b) { if (x >= r + b) { x -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; }
    return r;
}

int gfx_init(int want_w, int want_h) {
    EFI_STATUS st = uefi_call_wrapper(BS->LocateProtocol, 3, &GraphicsOutputProtocol, NULL, (void **)&gop);
    if (EFI_ERROR(st) || !gop) return -1;
    UINT32 best = gop->Mode->Mode; INT64 bestscore = -1;
    for (UINT32 i = 0; i < gop->Mode->MaxMode; i++) {
        EFI_GRAPHICS_OUTPUT_MODE_INFORMATION *inf; UINTN isz;
        if (EFI_ERROR(uefi_call_wrapper(gop->QueryMode, 4, gop, i, &isz, &inf))) continue;
        INT64 w = inf->HorizontalResolution, h = inf->VerticalResolution, score;
        if (want_w > 0) score = (w == want_w && h == want_h) ? 1000000000LL : 500000000LL - absi((int)(w - want_w)) - absi((int)(h - want_h));
        else score = (w <= 1920 && h <= 1080) ? w * h : 1000 - w;
        if (score > bestscore) { bestscore = score; best = i; }
    }
    if (best != gop->Mode->Mode) uefi_call_wrapper(gop->SetMode, 2, gop, best);
    G_w = gop->Mode->Info->HorizontalResolution; G_h = gop->Mode->Info->VerticalResolution;
    G_scale16 = (int)(((INT64)G_h << 16) / 1080);
    G_px = AllocatePool((UINTN)G_w * G_h * 4);
    if (!G_px) return -2;
    return 0;
}

void gfx_present(void) {
    uefi_call_wrapper(gop->Blt, 10, gop, (EFI_GRAPHICS_OUTPUT_BLT_PIXEL *)G_px, EfiBltBufferToVideo, 0, 0, 0, 0, (UINTN)G_w, (UINTN)G_h, (UINTN)G_w * 4);
}

/* ---------- primitives ---------- */
static inline void put(int x, int y, u32 c, int a) {
    if (x < 0 || y < 0 || x >= G_w || y >= G_h || a <= 0) return;
    u32 *p = &G_px[y * G_w + x]; *p = blend(*p, c, a > 255 ? 255 : a);
}
static void span(int y, int x0, int x1, u32 c, int a) {
    if (y < 0 || y >= G_h || a <= 0) return;
    if (x0 < 0) x0 = 0; if (x1 > G_w) x1 = G_w;
    u32 *p = &G_px[y * G_w];
    if (a >= 255) { for (int x = x0; x < x1; x++) p[x] = c; }
    else for (int x = x0; x < x1; x++) p[x] = blend(p[x], c, a);
}
void fill_rect(int x, int y, int w, int h, u32 c, int a) { for (int j = 0; j < h; j++) span(y + j, x, x + w, c, a); }

/* coverage 0..16 of rounded rect at pixel */
static int rr_cov(int px, int py, int x, int y, int w, int h, int r) {
    if (px < x || px >= x + w || py < y || py >= y + h) return 0;
    int dx = 0, dy = 0;
    if (px < x + r) dx = px * 16 + 8 - (x + r) * 16; else if (px >= x + w - r) dx = px * 16 + 8 - (x + w - r) * 16;
    if (py < y + r) dy = py * 16 + 8 - (y + r) * 16; else if (py >= y + h - r) dy = py * 16 + 8 - (y + h - r) * 16;
    if (!dx && !dy) return 16;
    int d = (int)isqrt32((u32)(dx * dx + dy * dy));
    return clampi(r * 16 - d + 8, 0, 16);
}
void fill_rrect(int x, int y, int w, int h, int r, u32 c, int a) {
    if (r * 2 > w) r = w / 2; if (r * 2 > h) r = h / 2;
    for (int j = 0; j < h; j++) {
        int py = y + j; if (py < 0 || py >= G_h) continue;
        if (j < r || j >= h - r) {
            for (int i = 0; i < r; i++) {
                put(x + i, py, c, a * rr_cov(x + i, py, x, y, w, h, r) / 16);
                put(x + w - 1 - i, py, c, a * rr_cov(x + w - 1 - i, py, x, y, w, h, r) / 16);
            }
            span(py, x + r, x + w - r, c, a);
        } else span(py, x, x + w, c, a);
    }
}
void stroke_rrect(int x, int y, int w, int h, int r, int t, u32 c, int a) {
    if (r * 2 > w) r = w / 2; if (r * 2 > h) r = h / 2;
    int ir = r > t ? r - t : 0;
    for (int j = 0; j < h; j++) {
        int py = y + j; if (py < 0 || py >= G_h) continue;
        int band = (j < t + r || j >= h - t - r);
        for (int i = 0; i < w; i++) {
            if (!band && i >= t && i < w - t) { i = w - t - 1; continue; }
            int px = x + i;
            int cv = rr_cov(px, py, x, y, w, h, r) - rr_cov(px, py, x + t, y + t, w - 2 * t, h - 2 * t, ir);
            if (cv > 0) put(px, py, c, a * cv / 16);
        }
    }
}
void fill_circle(int cx, int cy, int r, u32 c, int a) {
    for (int j = -r - 1; j <= r + 1; j++) for (int i = -r - 1; i <= r + 1; i++) {
        int d = (int)isqrt32((u32)((i * 16) * (i * 16) + (j * 16) * (j * 16)));
        int cv = clampi(r * 16 - d + 8, 0, 16);
        if (cv) put(cx + i, cy + j, c, a * cv / 16);
    }
}
void ring(int cx, int cy, int r, int t, u32 c, int a, int mode, int gapw) {
    int ext = r + t / 2 + 2;
    for (int j = -ext; j <= ext; j++) for (int i = -ext; i <= ext; i++) {
        if (mode == 1 && j < 0 && absi(i) < gapw) continue;
        if (mode == 2 && i > 0 && absi(j) < gapw) continue;
        int d = (int)isqrt32((u32)((i * 16) * (i * 16) + (j * 16) * (j * 16)));
        int cv = clampi(t * 8 - absi(d - r * 16) + 8, 0, 16);
        if (cv) put(cx + i, cy + j, c, a * cv / 16);
    }
}
void radial_glow(int cx, int cy, int r, u32 c, int a) {
    for (int j = -r; j <= r; j += 1) {
        int py = cy + j; if (py < 0 || py >= G_h) continue;
        for (int i = -r; i <= r; i++) {
            int px = cx + i; if (px < 0 || px >= G_w) continue;
            u32 d2 = (u32)(i * i + j * j); if (d2 >= (u32)(r * r)) continue;
            int t = 256 - (int)((d2 * 256) / (u32)(r * r));      /* 256 centre .. 0 edge */
            int al = (t * t >> 8) * a >> 8;
            if (al > 0) { u32 *p = &G_px[py * G_w + px]; *p = blend(*p, c, al); }
        }
    }
}

/* ---------- alpha8 blit with bilinear scaling ---------- */
static void blit_a8(const u8 *bmp, int bw, int bh, int dx, int dy, int dw, int dh, u32 c, int a) {
    if (dw <= 0 || dh <= 0 || a <= 0) return;
    int stx = (int)(((INT64)bw << 16) / dw), sty = (int)(((INT64)bh << 16) / dh);
    int same = (dw == bw && dh == bh);
    for (int j = 0; j < dh; j++) {
        int py = dy + j; if (py < 0 || py >= G_h) continue;
        int sy = clampi(j * sty + sty / 2 - 32768, 0, (bh - 1) << 16), y0 = sy >> 16, wy = (sy & 0xFFFF) >> 8, y1 = y0 + 1 < bh ? y0 + 1 : y0;
        for (int i = 0; i < dw; i++) {
            int px = dx + i; if (px < 0 || px >= G_w) continue;
            int cov;
            if (same) cov = bmp[j * bw + i];
            else {
                int sx = clampi(i * stx + stx / 2 - 32768, 0, (bw - 1) << 16), x0 = sx >> 16, wx = (sx & 0xFFFF) >> 8, x1 = x0 + 1 < bw ? x0 + 1 : x0;
                int t = bmp[y0 * bw + x0] * (256 - wx) + bmp[y0 * bw + x1] * wx;
                int b = bmp[y1 * bw + x0] * (256 - wx) + bmp[y1 * bw + x1] * wx;
                cov = ((t >> 8) * (256 - wy) + (b >> 8) * wy) >> 8;
            }
            if (cov) { u32 *p = &G_px[py * G_w + px]; *p = blend(*p, c, cov * a / 255); }
        }
    }
}

int text_w(const Font *f, const char *s, int sc16) {
    INT64 w = 0; for (; *s; s++) { if (*s < 32 || *s > 126) continue; w += (INT64)f->g[*s - 32].adv * sc16; }
    return (int)(w >> 16);
}
void text(const Font *f, int x, int y, const char *s, u32 c, int a, int sc16) {
    INT64 pen = (INT64)x << 16; int base = y + (int)(((INT64)f->ascent * sc16) >> 16);
    for (; *s; s++) {
        if (*s < 32 || *s > 126) continue;
        const Glyph *g = &f->g[*s - 32];
        if (g->w) {
            int gx = (int)(pen >> 16) + (int)(((INT64)g->bx * sc16) >> 16);
            int gy = base - (int)(((INT64)g->by * sc16) >> 16);
            int dw = (int)(((INT64)g->w * sc16 + 32768) >> 16), dh = (int)(((INT64)g->h * sc16 + 32768) >> 16);
            if (dw < 1) dw = 1; if (dh < 1) dh = 1;
            blit_a8(f->bmp + g->off, g->w, g->h, gx, gy, dw, dh, c, a);
        }
        pen += (INT64)g->adv * sc16;
    }
}
void text_center(const Font *f, int cx, int y, const char *s, u32 c, int a, int sc16) { text(f, cx - text_w(f, s, sc16) / 2, y, s, c, a, sc16); }
void logo_draw(int cx, int y, int h, u32 tint, int a, int *out_w) {
    int w = (int)((INT64)LOGO_W * h / LOGO_H); if (out_w) *out_w = w;
    blit_a8(logo_alpha, LOGO_W, LOGO_H, cx - w / 2, y, w, h, tint, a);
}

/* ---------- animated background ---------- */
static u32 *lo, *hrowA, *hrowB, *rowc, *vcol;
static int LW, LH;
typedef struct { int x, y, sp, ph, sz; } Star;
#define NSTAR 120
static Star stars[NSTAR];
static u32 rng = 12345;
static u32 rnd(void) { rng = rng * 1664525u + 1013904223u; return rng >> 8; }

void bg_init(void) {
    LW = G_w / 4 + 2; LH = G_h / 4 + 2;
    lo = AllocatePool((UINTN)LW * LH * 4); hrowA = AllocatePool((UINTN)G_w * 4 + 64); hrowB = AllocatePool((UINTN)G_w * 4 + 64);
    rowc = AllocatePool((UINTN)G_h * 4); vcol = AllocatePool((UINTN)G_w * 4);
    for (int x = 0; x < G_w; x++) {   /* vignette factor 150..256 */
        int d = absi(x - G_w / 2) * 256 / (G_w / 2); vcol[x] = 256 - (d * d >> 8) * 100 / 256;
    }
    for (int i = 0; i < NSTAR; i++) { stars[i].x = (int)(rnd() % G_w) << 8; stars[i].y = (int)(rnd() % G_h) << 8; stars[i].sp = 6 + rnd() % 30; stars[i].ph = rnd() & 255; stars[i].sz = (rnd() % 7 == 0) ? 2 : 1; }
}

void stars_step(int dt) {
    for (int i = 0; i < NSTAR; i++) {
        stars[i].y -= stars[i].sp * dt * 2 * 256 / 1000 * G_scale16 / 65536; stars[i].x += stars[i].sp * dt * 256 / 4000;
        if (stars[i].y < 0) { stars[i].y += G_h << 8; stars[i].x = (int)(rnd() % G_w) << 8; }
        if ((stars[i].x >> 8) >= G_w) stars[i].x -= G_w << 8;
    }
}
void stars_draw(UINT64 t, u32 ca) {
    for (int i = 0; i < NSTAR; i++) {
        int tw = 110 + (isin((int)(t / 14) * stars[i].sp / 12 + stars[i].ph) + 1024) * 145 / 2048;
        u32 col = (i & 3) == 0 ? mixc(0xFFFFFF, ca, 110) : 0xDDEEFF;
        int x = stars[i].x >> 8, y = stars[i].y >> 8, sz = stars[i].sz * (G_h >= 900 ? 2 : 1);
        for (int j = 0; j < sz; j++) for (int k = 0; k < sz; k++) put(x + k, y + j, col, tw * (sz > 1 ? 200 : 255) / 255);
        if (sz > 2) put(x + 1, y + 1, col, tw / 3);
    }
}

void bg_draw(UINT64 t, u32 ca, u32 cb, int intro) {
    u32 cm = mixc(ca, cb, 128);
    /* row gradient (dark, tinted by palette) */
    u32 top = mixc(rgb(3, 7, 14), cb, 22), bot = mixc(rgb(1, 3, 7), ca, 10);
    for (int y = 0; y < G_h; y++) rowc[y] = mixc(top, bot, y * 255 / G_h);
    /* low-res aurora field */
    static const int cyc10[3] = {13, 21, 9}, spd[3] = {18, -26, 11}, ph[3] = {0, 70, 150};
    static const int base100[3] = {30, 40, 22};
    for (int lx = 0; lx < LW; lx++) {
        int sh = 190 + isin(lx * 256 * 7 / (10 * LW) + (int)(t / 23)) * 60 / 1024;
        int cy[3];
        for (int k = 0; k < 3; k++) {
            int ang = lx * cyc10[k] * 256 / (10 * LW) + (int)(t * spd[k] / 400) + ph[k];
            cy[k] = LH * base100[k] / 100 + isin(ang) * (LH * 9 / 100) / 1024 + isin(ang * 2 + 40) * (LH * 3 / 100) / 1024;
        }
        for (int ly = 0; ly < LH; ly++) {
            int R = 0, G = 0, B = 0;
            for (int k = 0; k < 3; k++) {
                int d = ly - cy[k], up = LH * 24 / 100, dn = LH * 5 / 100, v;
                if (d < 0) { if (-d >= up) continue; v = 256 - (-d) * 256 / up; }
                else { if (d >= dn) continue; v = 256 - d * 256 / dn; }
                v = (v * v >> 8) * sh >> 8; v = v * 150 >> 8;
                u32 col = k == 0 ? ca : (k == 1 ? cm : cb);
                R += v * (int)((col >> 16) & 255) >> 8; G += v * (int)((col >> 8) & 255) >> 8; B += v * (int)(col & 255) >> 8;
            }
            R = R * intro >> 8; G = G * intro >> 8; B = B * intro >> 8;
            lo[ly * LW + lx] = ((u32)clampi(R, 0, 200) << 16) | ((u32)clampi(G, 0, 200) << 8) | (u32)clampi(B, 0, 200);
        }
    }
    /* bilinear upscale + add to gradient + vignette */
    #define HROW(dst, ly) do { const u32 *s = &lo[(ly) * LW]; for (int x = 0; x < G_w; x++) { int lx = x >> 2, fx = (x & 3) * 64; \
        u32 a = s[lx], b = s[lx + 1]; \
        (dst)[x] = ((((a & 0xFF00FF) * (256 - fx) + (b & 0xFF00FF) * fx) >> 8) & 0xFF00FF) | ((((a & 0x00FF00) * (256 - fx) + (b & 0x00FF00) * fx) >> 8) & 0x00FF00); } } while (0)
    u32 *A = hrowA, *Bq = hrowB; HROW(A, 0);
    for (int ly = 0; ly + 1 < LH; ly++) {
        HROW(Bq, ly + 1);
        for (int sy = 0; sy < 4; sy++) {
            int y = ly * 4 + sy; if (y >= G_h) break;
            u32 wy = sy * 64, base = rowc[y]; u32 *o = &G_px[y * G_w];
            for (int x = 0; x < G_w; x++) {
                u32 a = A[x], b = Bq[x];
                u32 v = ((((a & 0xFF00FF) * (256 - wy) + (b & 0xFF00FF) * wy) >> 8) & 0xFF00FF) | ((((a & 0x00FF00) * (256 - wy) + (b & 0x00FF00) * wy) >> 8) & 0x00FF00);
                v += base; u32 vc = vcol[x];
                o[x] = (((v & 0xFF00FF) * vc >> 8) & 0xFF00FF) | (((v & 0x00FF00) * vc >> 8) & 0x00FF00);
            }
        }
        u32 *tmp = A; A = Bq; Bq = tmp;
    }
}
