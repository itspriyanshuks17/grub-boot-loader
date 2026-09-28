/* AuroraBoot - animated, interactive UEFI boot menu.  MIT License. */
#include "aurora.h"
#include <efipoint.h>
int ci_contains(const char *hay, const char *needle);

EFI_HANDLE gImage; EFI_LOADED_IMAGE *gLoaded;
static Config cfg; static Entry ent[MAX_ENTRIES]; static int nent;

/* ---------- time ---------- */
static UINT64 tsc_per_ms;
static inline UINT64 rdtsc(void) { UINT32 lo, hi; __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi)); return ((UINT64)hi << 32) | lo; }
static UINT64 now_ms(void) { return rdtsc() / tsc_per_ms; }
static void calibrate(void) { UINT64 a = rdtsc(); uefi_call_wrapper(BS->Stall, 1, 30000); UINT64 b = rdtsc(); tsc_per_ms = (b - a) / 30; if (!tsc_per_ms) tsc_per_ms = 2000000; }
static int ease(int v, int target, int dt, int tau) { return v + (int)((INT64)(target - v) * dt / (tau + dt)); }

/* ---------- palettes ---------- */
static const struct { const char *name; u32 a, b; } PAL[4] = {
    { "Aurora", 0x2DE3B5, 0x7C5CFF }, { "Ember", 0xFF8A3D, 0xE0245E }, { "Glacier", 0x5CC8FF, 0x2A6BFF }, { "Neon", 0xFF3DA5, 0x22E5FF } };

/* ---------- tiny string helpers ---------- */
static void scat(char *d, const char *s) { while (*d) d++; while ((*d++ = *s++)); }
static void icat(char *d, int v) { char t[12]; int n = 0; if (!v) t[n++] = '0'; while (v) { t[n++] = '0' + v % 10; v /= 10; } while (*d) d++; while (n) *d++ = t[--n]; *d = 0; }
static void path_ascii(const CHAR16 *p, char *o, int max) { int n = 0; if (*p == L'\\') p++; for (; *p && n < max - 1; p++) o[n++] = (*p < 127 && *p >= 32) ? (char)*p : '?'; o[n] = 0; }

/* ---------- icons ---------- */
static u32 brand(const char *n, int *type) {
    *type = 3;
    if (ci_contains(n, "windows")) { *type = 1; return 0x4CC2FF; }
    if (ci_contains(n, "ubuntu")) { *type = 2; return 0xFF7A45; }
    if (ci_contains(n, "fedora")) return 0x5B9BE6;
    if (ci_contains(n, "debian")) return 0xF0407A;
    if (ci_contains(n, "arch")) return 0x3DB8F5;
    if (ci_contains(n, "suse")) return 0x7AC943;
    if (ci_contains(n, "mint")) return 0x8FD14F;
    if (ci_contains(n, "pop")) return 0x48B9C7;
    if (ci_contains(n, "kali")) return 0x4E8CFF;
    if (ci_contains(n, "manjaro")) return 0x35BF5C;
    if (ci_contains(n, "shell") || ci_contains(n, "removable")) return 0xC8D0DA;
    return 0xE6EEF5;
}
static void draw_icon(const Entry *e, int cx, int cy, int sz, u32 accent, int a) {
    int type; u32 col;
    if (e->kind == K_FIRMWARE) { type = 4; col = 0xB4C8FF; } else if (e->kind == K_REBOOT) { type = 5; col = 0xFFD166; }
    else if (e->kind == K_SHUTDOWN) { type = 6; col = 0xFF7B7B; } else col = brand(e->name, &type);
    fill_rrect(cx - sz / 2, cy - sz / 2, sz, sz, sz / 4, col, a * 42 / 255);
    stroke_rrect(cx - sz / 2, cy - sz / 2, sz, sz, sz / 4, S(2) > 1 ? S(2) : 1, col, a * 110 / 255);
    int t = sz * 7 / 100 + 1;
    switch (type) {
    case 1: { int g = sz * 5 / 100 + 1, p = sz * 24 / 100; for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++)
        fill_rrect(cx - p - g / 2 + i * (p + g), cy - p - g / 2 + j * (p + g), p, p, 2, col, a); break; }
    case 2: { int R = sz * 22 / 100; ring(cx, cy, R, t, col, a, 0, 0);
        for (int k = 0; k < 3; k++) { int ang = 20 + k * 85; fill_circle(cx + icos(ang) * (R + t) / 1024, cy + isin(ang) * (R + t) / 1024, sz * 7 / 100 + 1, col, a); } break; }
    case 4: { int R = sz * 17 / 100; ring(cx, cy, R, t + 1, col, a, 0, 0);
        for (int k = 0; k < 8; k++) { int ang = k * 32; int x = cx + icos(ang) * (R + t * 2) / 1024, y = cy + isin(ang) * (R + t * 2) / 1024; fill_circle(x, y, t + 1, col, a); } break; }
    case 5: { int R = sz * 22 / 100; ring(cx, cy, R, t, col, a, 2, sz * 8 / 100); fill_circle(cx + R, cy - sz * 8 / 100 - t, t + 1, col, a); break; }
    case 6: { int R = sz * 22 / 100; ring(cx, cy, R, t, col, a, 1, sz * 9 / 100); fill_rrect(cx - t / 2, cy - R - t, t + 1, R + t, t / 2, col, a); break; }
    default: { char l[2] = { e->name[0] >= 'a' && e->name[0] <= 'z' ? e->name[0] - 32 : e->name[0], 0 };
        int sc = (int)((INT64)sz * 65536 / 108); int w = text_w(&FONT_BIG, l, sc), lh = (int)((INT64)FONT_BIG.line * sc >> 16);
        text(&FONT_BIG, cx - w / 2, cy - lh / 2 - lh / 12, l, col, a, sc); (void)accent; }
    }
}

/* ---------- actions ---------- */
static void do_firmware(void) {
    UINT64 sup = 0, os = 0; UINTN sz = 8; UINT32 attr;
    if (!EFI_ERROR(uefi_call_wrapper(RT->GetVariable, 5, L"OsIndicationsSupported", &EfiGlobalVariable, &attr, &sz, &sup)) && (sup & 1)) {
        sz = 8; uefi_call_wrapper(RT->GetVariable, 5, L"OsIndications", &EfiGlobalVariable, &attr, &sz, &os);
        os |= 1; uefi_call_wrapper(RT->SetVariable, 5, L"OsIndications", &EfiGlobalVariable, EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS | EFI_VARIABLE_RUNTIME_ACCESS, 8, &os);
        uefi_call_wrapper(RT->ResetSystem, 4, EfiResetCold, EFI_SUCCESS, 0, NULL);
    }
}
static EFI_STATUS boot_entry(Entry *e) {
    if (e->kind == K_FIRMWARE) { do_firmware(); return EFI_UNSUPPORTED; }
    if (e->kind == K_REBOOT) uefi_call_wrapper(RT->ResetSystem, 4, EfiResetCold, EFI_SUCCESS, 0, NULL);
    if (e->kind == K_SHUTDOWN) uefi_call_wrapper(RT->ResetSystem, 4, EfiResetShutdown, EFI_SUCCESS, 0, NULL);
    if (cfg.demo || !e->dev) return EFI_UNSUPPORTED;
    EFI_DEVICE_PATH *dp = FileDevicePath(e->dev, e->path); if (!dp) return EFI_NOT_FOUND;
    EFI_HANDLE img; EFI_STATUS st = uefi_call_wrapper(BS->LoadImage, 6, FALSE, gImage, dp, NULL, 0, &img);
    if (EFI_ERROR(st)) return st;
    return uefi_call_wrapper(BS->StartImage, 3, img, NULL, NULL);
}

/* ---------- main ---------- */
static int card_w, card_h, pitch;
static void describe(const Entry *e, char *o, int max) {
    if (e->kind == K_FIRMWARE) { o[0] = 0; scat(o, "Reboot into UEFI firmware settings"); }
    else if (e->kind == K_REBOOT) { o[0] = 0; scat(o, "Restart this computer"); }
    else if (e->kind == K_SHUTDOWN) { o[0] = 0; scat(o, "Power off this computer"); }
    else path_ascii(e->path, o, max);
}

static void draw_hint(int *x, int y, const char *key, const char *label, int a, int sc, int measure) {
    int kw = text_w(&FONT_SMALL, key, sc) + S(26), h = S(38), lw = text_w(&FONT_SMALL, label, sc);
    if (!measure) {
        stroke_rrect(*x, y, kw, h, S(9), S(2) > 1 ? S(2) : 1, 0xFFFFFF, a * 90 / 255);
        fill_rrect(*x, y, kw, h, S(9), 0xFFFFFF, a * 14 / 255);
        text(&FONT_SMALL, *x + S(13), y + (h - (int)((INT64)FONT_SMALL.line * sc >> 16)) / 2, key, 0xFFFFFF, a * 230 / 255, sc);
        text(&FONT_SMALL, *x + kw + S(12), y + (h - (int)((INT64)FONT_SMALL.line * sc >> 16)) / 2, label, 0xFFFFFF, a * 150 / 255, sc);
    }
    *x += kw + S(12) + lw + S(38);
}

EFI_STATUS efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *systab) {
    InitializeLib(image, systab); gImage = image;
    uefi_call_wrapper(BS->HandleProtocol, 3, image, &LoadedImageProtocol, (void **)&gLoaded);
    uefi_call_wrapper(BS->SetWatchdogTimer, 4, 0, 0, 0, NULL);
    uefi_call_wrapper(ST->ConOut->EnableCursor, 2, ST->ConOut, FALSE);
    calibrate(); config_defaults(&cfg); config_load(&cfg);
    if (gfx_init(cfg.res_w, cfg.res_h)) { Print(L"AuroraBoot: no graphics output\n"); uefi_call_wrapper(BS->Stall, 1, 3000000); return EFI_UNSUPPORTED; }
    bg_init();
    nent = discover(ent, MAX_ENTRIES, &cfg);
    if (!nent) { Entry *e = &ent[nent++]; SetMem(e, sizeof(*e), 0); scat(e->name, "Firmware Setup"); e->kind = K_FIRMWARE; }

    int sel = 0;
    if (cfg.def[0]) for (int i = 0; i < nent; i++) if (ci_contains(ent[i].name, cfg.def) && ent[i].kind == K_OS) { sel = i; break; }
    int pal = cfg.has_accent ? 4 : cfg.palette, npal = cfg.has_accent ? 5 : 4;
    u32 ca = 0, cb = 0;
    if (pal == 4) { ca = cfg.accent; cb = cfg.accent2; } else { ca = PAL[pal].a; cb = PAL[pal].b; }
    u32 ta = ca, tb = cb;

    EFI_SIMPLE_POINTER_PROTOCOL *ptr = NULL; uefi_call_wrapper(BS->LocateProtocol, 3, &SimplePointerProtocol, NULL, (void **)&ptr);
    int mx = G_w / 2, my = G_h * 3 / 4, mouse_on = 0, hover = -1, click = 0;

    int scroll16 = sel << 16, hot[MAX_ENTRIES] = { 0 }, paused = 0, mode = 0, booted_once = 0;
    UINT64 t0 = now_ms(), last = t0, cd_start = t0 + 1800, boot_t0 = 0, toast_until = 0; char toast[96] = ""; u32 toast_col = 0xFFFFFF;
    card_w = S(230); card_h = S(290); pitch = S(325);
    int cxs[MAX_ENTRIES], cys[MAX_ENTRIES], chs[MAX_ENTRIES], cws[MAX_ENTRIES];

    for (;;) {
        UINT64 now = now_ms(), fs = now; int dt = (int)(now - last); last = now; if (dt > 100) dt = 100; if (dt < 1) dt = 1;
        int T = (int)(now - t0);

        /* ---- input ---- */
        EFI_INPUT_KEY k;
        while (mode == 0 && !EFI_ERROR(uefi_call_wrapper(ST->ConIn->ReadKeyStroke, 2, ST->ConIn, &k))) {
            paused = 1; int act = 0;
            if (k.ScanCode == 4 || k.ScanCode == 1) sel = (sel + nent - 1) % nent;
            else if (k.ScanCode == 3 || k.ScanCode == 2) sel = (sel + 1) % nent;
            else if (k.ScanCode == 5) sel = 0; else if (k.ScanCode == 6) sel = nent - 1;
            else if (k.ScanCode == 0x0C) { for (int i = 0; i < nent; i++) if (ent[i].kind == K_FIRMWARE) { sel = i; act = 1; } }
            else if (k.UnicodeChar == 0x0D || k.UnicodeChar == ' ') act = 1;
            else if (k.UnicodeChar == 't' || k.UnicodeChar == 'T') {
                pal = (pal + 1) % npal; if (pal == 4) { ta = cfg.accent; tb = cfg.accent2; } else { ta = PAL[pal].a; tb = PAL[pal].b; }
                toast[0] = 0; scat(toast, "Theme: "); scat(toast, pal == 4 ? "Custom" : PAL[pal].name); toast_until = now + 1800; toast_col = 0xFFFFFF;
            } else if (k.UnicodeChar == 'i' || k.UnicodeChar == 'I') { t0 = now; cd_start = now + 1800; paused = 0; }
            else if (k.UnicodeChar >= '1' && k.UnicodeChar <= '9') { int i = k.UnicodeChar - '1'; if (i < nent) sel = i; }
            if (act) { mode = 1; boot_t0 = now; }
        }
        if (mode == 0 && ptr) {
            EFI_SIMPLE_POINTER_STATE ps; static int lastbtn = 0;
            if (!EFI_ERROR(uefi_call_wrapper(ptr->GetState, 2, ptr, &ps))) {
                int res = ptr->Mode->ResolutionX ? (int)(ptr->Mode->ResolutionX / 1000000) : 1; if (res < 1) res = 1;
                if (ps.RelativeMovementX || ps.RelativeMovementY) { mouse_on = 1; mx = clampi(mx + (int)ps.RelativeMovementX * 3 / res, 0, G_w - 1); my = clampi(my + (int)ps.RelativeMovementY * 3 / res, 0, G_h - 1); }
                if (ps.LeftButton && !lastbtn) click = 1; lastbtn = ps.LeftButton;
            }
        }
        if (mode == 0 && mouse_on) {
            int h = -1; for (int i = 0; i < nent; i++) if (mx >= cxs[i] - cws[i] / 2 && mx < cxs[i] + cws[i] / 2 && my >= cys[i] - chs[i] / 2 && my < cys[i] + chs[i] / 2) h = i;
            if (h >= 0 && h != hover) { sel = h; paused = 1; } hover = h;
            if (click && h >= 0) { sel = h; paused = 1; mode = 1; boot_t0 = now; }
        }
        click = 0;

        /* ---- update ---- */
        scroll16 = ease(scroll16, sel << 16, dt, 120);
        for (int i = 0; i < nent; i++) hot[i] = ease(hot[i], i == sel ? 256 : 0, dt, 90);
        ca = mixc(ca, ta, dt * 255 / 220 + 1); cb = mixc(cb, tb, dt * 255 / 220 + 1);
        int remain_ms = 0, total_ms = cfg.timeout * 1000;
        if (mode == 0 && !paused && cfg.timeout > 0 && !cfg.demo) {
            remain_ms = total_ms - (int)((now > cd_start ? now - cd_start : 0));
            if (remain_ms <= 0) { mode = 1; boot_t0 = now; }
        } else if (!paused && cfg.demo && cfg.timeout > 0) remain_ms = total_ms - (int)((now > cd_start ? now - cd_start : 0)), remain_ms = remain_ms < 0 ? 0 : remain_ms;
        else remain_ms = total_ms;
        int bp = 0; /* boot progress 0..256 */
        if (mode == 1) bp = clampi((int)(now - boot_t0) * 256 / 650, 0, 256);
        int intro = clampi(T * 256 / 1400, 0, 256);

        /* ---- render ---- */
        bg_draw((UINT64)T, ca, cb, intro);
        stars_step(dt); stars_draw((UINT64)T, ca);
        int cx = G_w / 2, fade = 256 - bp;

        /* logo + title */
        { int lp = clampi((T - 150) * 256 / 800, 0, 256); lp = lp * lp >> 8;
          int maxh = S(150), maxw = S(420), lh = maxh; if ((INT64)lh * LOGO_W > (INT64)maxw * LOGO_H) lh = (int)((INT64)maxw * LOGO_H / LOGO_W);
          int ly = S(70) + (256 - lp) * S(-26) / 256, la = lp * fade >> 8;
          radial_glow(cx, S(70) + maxh / 2, S(250), ca, (26 + (isin(T / 9) + 1024) * 14 / 2048) * la / 256);
          logo_draw(cx, ly + (maxh - lh) / 2, lh, 0xFFFFFF, la, NULL);
          int ty = S(70) + maxh + S(22);
          if (cfg.show_title) { text_center(&FONT_BIG, cx, ty, cfg.title, 0xFFFFFF, la, G_scale16); ty += S(84); }
          text_center(&FONT_SMALL, cx, ty, cfg.subtitle, mixc(0xFFFFFF, ca, 90), la * 170 / 255, G_scale16); }

        /* cards (far to near so selected is on top) */
        int cyc = S(600);
        for (int pass = nent; pass >= 0; pass--) for (int i = 0; i < nent; i++) {
            int dist = absi(i * 65536 - scroll16) >> 8; int order = clampi(dist / 256, 0, nent);
            if (order != pass) continue;
            int grow = 100 + hot[i] * 24 / 256; int cp = clampi((T - 500 - i * 90) * 256 / 550, 0, 256); cp = cp * cp >> 8;
            int al = clampi(255 - dist * 72 / 256, 0, 255) * cp >> 8; al = al * (i == sel ? 256 : fade) >> 8;
            int w = card_w * grow / 100, h = card_h * grow / 100;
            int x = cx + (int)(((INT64)(i * 65536 - scroll16) * pitch) >> 16);
            int y = cyc + (256 - cp) * S(50) / 256 + (i == sel ? isin(T / 8) * S(5) / 1024 : 0);
            if (mode == 1 && i == sel) { w = w * (256 + bp / 3) >> 8; h = h * (256 + bp / 3) >> 8; }
            cxs[i] = x; cys[i] = y; cws[i] = w; chs[i] = h;
            if (al <= 0 || x + w / 2 < 0 || x - w / 2 > G_w) continue;
            int H = hot[i], r = S(30), bx = x - w / 2, by = y - h / 2;
            if (H > 8) radial_glow(x, y, S(300), ca, 34 * H / 256 * al / 255);
            fill_rrect(bx, by, w, h, r, 0x0A1520, al * 165 / 255);
            fill_rrect(bx, by, w, h, r, mixc(0xFFFFFF, ca, 120), al * (12 + H * 26 / 256) / 255);
            if (H > 8) for (int g = 0; g < 7; g++) stroke_rrect(bx - g * S(4) - S(2), by - g * S(4) - S(2), w + 2 * (g * S(4) + S(2)), h + 2 * (g * S(4) + S(2)), r + g * S(4), S(4), ca, (60 - g * 8) * H / 256 * al / 255);
            stroke_rrect(bx, by, w, h, r, S(3) > 2 ? S(3) : 2, mixc(0xFFFFFF, ca, 40 + H * 215 / 256), al * (55 + H * 200 / 256) / 255);
            draw_icon(&ent[i], x, y - h * 13 / 100, S(122) * grow / 100, ca, al);
            int sc = (int)((INT64)G_scale16 * grow / 100), nw = text_w(&FONT_BODY, ent[i].name, sc);
            if (nw > w - S(28)) { sc = (int)((INT64)sc * (w - S(28)) / nw); nw = text_w(&FONT_BODY, ent[i].name, sc); }
            text(&FONT_BODY, x - nw / 2, y + h * 27 / 100, ent[i].name, 0xFFFFFF, al * (170 + H * 85 / 256) / 255, sc);
            if (i < 9) { char n[2] = { '1' + i, 0 }; text(&FONT_SMALL, bx + S(18), by + S(12), n, 0xFFFFFF, al * 90 / 255, G_scale16); }
        }

        /* details + countdown */
        { int a = clampi((T - 900) * 256 / 500, 0, 256) * fade >> 8; char buf[200];
          if (cfg.show_paths) { describe(&ent[sel], buf, sizeof(buf)); text_center(&FONT_SMALL, cx, S(818), buf, 0xFFFFFF, a * 105 / 255, G_scale16); }
          int bw = S(460), by = S(920);
          if (cfg.timeout > 0 && ent[sel].kind != K_SHUTDOWN) {
              buf[0] = 0;
              if (paused) scat(buf, "Autoboot paused"); else { scat(buf, "Booting "); scat(buf, ent[sel].name); scat(buf, " in "); icat(buf, (remain_ms + 999) / 1000); scat(buf, "s"); }
              text_center(&FONT_SMALL, cx, S(866), buf, paused ? 0xAAB8C4 : 0xFFFFFF, a * (paused ? 130 : 210) / 255, G_scale16);
              fill_rrect(cx - bw / 2, by, bw, S(6), S(3), 0xFFFFFF, a * 28 / 255);
              int fw = paused ? bw : (int)((INT64)bw * remain_ms / total_ms);
              if (fw > S(6)) fill_rrect(cx - bw / 2, by, fw, S(6), S(3), paused ? mixc(0xFFFFFF, ca, 80) : ca, a * (paused ? 60 : 255) / 255);
          } }

        /* key hints */
        { int a = clampi((T - 1100) * 256 / 500, 0, 256) * fade >> 8, sc = G_scale16 * 90 / 100, x = 0, y = S(985);
          static const char *K[] = { "< >", "Enter", "1-9", "T", "F2" }, *L[] = { "Select", "Boot", "Jump", "Theme", "Firmware" };
          for (int i = 0; i < 5; i++) draw_hint(&x, y, K[i], L[i], 0, sc, 1);
          x = cx - (x - S(38)) / 2; for (int i = 0; i < 5; i++) draw_hint(&x, y, K[i], L[i], a, sc, 0); }

        if (now < toast_until) text_center(&FONT_SMALL, cx, S(1040), toast, toast_col, 230, G_scale16);
        if (mode == 1) {
            fill_rect(0, 0, G_w, G_h, 0x000000, bp * bp >> 8);
            char b[100]; b[0] = 0; scat(b, ent[sel].kind == K_OS ? "Starting " : ""); scat(b, ent[sel].name); if (ent[sel].kind == K_OS) scat(b, "...");
            text_center(&FONT_BODY, cx, G_h / 2 - S(24), b, 0xFFFFFF, bp * bp >> 8, G_scale16);
        }
        if (mouse_on && mode == 0) { fill_circle(mx, my, S(11), 0x000000, 120); fill_circle(mx, my, S(8), 0xFFFFFF, 240); fill_circle(mx, my, S(4), ca, 255); }
        gfx_present();

        /* ---- boot after fade-out ---- */
        if (mode == 1 && bp >= 256 && !booted_once) {
            EFI_STATUS st = boot_entry(&ent[sel]);
            mode = 0; paused = 1; t0 = now_ms() - 5000; last = now_ms();
            toast[0] = 0; toast_col = 0xFF8080;
            if (cfg.demo) { scat(toast, "Demo mode: nothing was booted"); toast_col = 0xFFD166; }
            else { scat(toast, "Could not start "); scat(toast, ent[sel].name); scat(toast, " (status "); icat(toast, (int)(st & 0xFFFF)); scat(toast, ")"); }
            toast_until = now_ms() + 4000;
        }
        while ((int)(now_ms() - fs) < 16) uefi_call_wrapper(BS->Stall, 1, 500);
    }
    return EFI_SUCCESS;
}
