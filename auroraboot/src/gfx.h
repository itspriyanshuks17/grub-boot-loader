/* AuroraBoot - software renderer for UEFI GOP. MIT licensed. */
#pragma once
#include <efi.h>
#include <efilib.h>
#include "assets.h"

typedef UINT32 u32;
typedef INT32 i32;
typedef UINT8 u8;

extern u32 *G_px;      /* back buffer, 0x00RRGGBB */
extern int G_w, G_h;
extern int G_scale16;  /* (height / 1080) in 16.16 */

#define S(v) ((int)(((INT64)(v) * G_scale16) >> 16))
static inline u32 rgb(u32 r, u32 g, u32 b) { return (r << 16) | (g << 8) | b; }
static inline int clampi(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }
static inline int absi(int v) { return v < 0 ? -v : v; }

/* alpha a: 0..255 */
static inline u32 blend(u32 d, u32 s, u32 a) {
    if (a > 255) a = 255;
    a += a >> 7; u32 ia = 256 - a;
    u32 rb = (((d & 0xFF00FF) * ia + (s & 0xFF00FF) * a) >> 8) & 0xFF00FF;
    u32 g  = (((d & 0x00FF00) * ia + (s & 0x00FF00) * a) >> 8) & 0x00FF00;
    return rb | g;
}
static inline u32 mixc(u32 a, u32 b, int t256) { return blend(a, b, clampi(t256, 0, 255)); }

int  gfx_init(int want_w, int want_h);
void gfx_present(void);
int  isin(int a);                /* a: 0..255 wraps; returns -1024..1024 */
int  icos(int a);

void fill_rect(int x, int y, int w, int h, u32 c, int a);
void fill_rrect(int x, int y, int w, int h, int r, u32 c, int a);
void stroke_rrect(int x, int y, int w, int h, int r, int t, u32 c, int a);
void fill_circle(int cx, int cy, int r, u32 c, int a);
/* mode 0: full ring, 1: gap on top (power), 2: gap on right (reload) */
void ring(int cx, int cy, int r, int t, u32 c, int a, int mode, int gapw);
void radial_glow(int cx, int cy, int r, u32 c, int a);

int  text_w(const Font *f, const char *s, int sc16);
void text(const Font *f, int x, int y, const char *s, u32 c, int a, int sc16);
void text_center(const Font *f, int cx, int y, const char *s, u32 c, int a, int sc16);
void logo_draw(int cx, int y, int h, u32 tint, int a, int *out_w);

void bg_init(void);
void bg_draw(UINT64 tms, u32 ca, u32 cb, int intro256);
void stars_step(int dt_ms);
void stars_draw(UINT64 tms, u32 ca);
