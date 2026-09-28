#include "aurora.h"

void config_defaults(Config *c) {
    SetMem(c, sizeof(*c), 0);
    const char *t = "AuroraBoot", *s = "Choose an operating system";
    for (int i = 0; t[i]; i++) c->title[i] = t[i];
    for (int i = 0; s[i]; i++) c->subtitle[i] = s[i];
    c->title[10] = 0;
    c->timeout = 8; c->palette = 0; c->show_title = 1; c->show_system = 1; c->show_paths = 1;
}

static int lower(int c) { return (c >= 'A' && c <= 'Z') ? c + 32 : c; }
int ci_contains(const char *hay, const char *needle) {
    if (!*needle) return 1;
    for (; *hay; hay++) { int i = 0; while (needle[i] && hay[i] && lower(hay[i]) == lower(needle[i])) i++; if (!needle[i]) return 1; }
    return 0;
}
static int ci_eq(const char *a, const char *b) { while (*a && *b) { if (lower(*a) != lower(*b)) return 0; a++; b++; } return *a == *b; }
static int hexv(int c) { return c >= '0' && c <= '9' ? c - '0' : (c >= 'a' && c <= 'f' ? c - 'a' + 10 : (c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1)); }
static u32 parse_hex(const char *s) { if (*s == '#') s++; u32 v = 0; while (hexv(*s) >= 0) v = v * 16 + hexv(*s++); return v; }
static int atoi_(const char *s) { int v = 0; while (*s >= '0' && *s <= '9') v = v * 10 + *s++ - '0'; return v; }
static int truthy(const char *v) { return ci_eq(v, "true") || ci_eq(v, "1") || ci_eq(v, "yes") || ci_eq(v, "on"); }
static void cpy(char *d, const char *s, int n) { int i = 0; for (; s[i] && i < n - 1; i++) d[i] = s[i]; d[i] = 0; }

void config_load(Config *c) {
    if (!gLoaded) return;
    EFI_FILE_HANDLE root = LibOpenRoot(gLoaded->DeviceHandle), f;
    if (!root) return;
    if (EFI_ERROR(uefi_call_wrapper(root->Open, 5, root, &f, L"\\EFI\\AuroraBoot\\aurora.conf", EFI_FILE_MODE_READ, 0)) &&
        EFI_ERROR(uefi_call_wrapper(root->Open, 5, root, &f, L"\\aurora.conf", EFI_FILE_MODE_READ, 0))) return;
    static char buf[8192]; UINTN sz = sizeof(buf) - 1;
    if (EFI_ERROR(uefi_call_wrapper(f->Read, 3, f, &sz, buf))) sz = 0;
    buf[sz] = 0; uefi_call_wrapper(f->Close, 1, f);

    int in_entry = 0; Entry *cur = NULL;
    for (char *p = buf; *p;) {
        char *line = p; while (*p && *p != '\n') p++; if (*p) *p++ = 0;
        int n = 0; while (line[n]) n++;
        while (n && (line[n - 1] == '\r' || line[n - 1] == ' ' || line[n - 1] == '\t')) line[--n] = 0;
        while (*line == ' ' || *line == '\t') line++;
        if (!*line || *line == '#' || *line == ';') continue;
        if (ci_eq(line, "[entry]")) { if (c->extra_n < 8) { cur = &c->extra[c->extra_n++]; SetMem(cur, sizeof(*cur), 0); cur->kind = K_OS; in_entry = 1; } continue; }
        char *eq = line; while (*eq && *eq != '=') eq++; if (!*eq) continue;
        *eq = 0; char *k = line, *v = eq + 1;
        int kn = 0; while (k[kn]) kn++; while (kn && (k[kn - 1] == ' ' || k[kn - 1] == '\t')) k[--kn] = 0;
        while (*v == ' ' || *v == '\t') v++;
        if (in_entry && cur) {
            if (ci_eq(k, "name")) cpy(cur->name, v, sizeof(cur->name));
            else if (ci_eq(k, "path")) { int i = 0; for (; v[i] && i < 158; i++) cur->path[i] = v[i] == '/' ? '\\' : v[i]; cur->path[i] = 0; }
            continue;
        }
        if (ci_eq(k, "title")) cpy(c->title, v, sizeof(c->title));
        else if (ci_eq(k, "subtitle")) cpy(c->subtitle, v, sizeof(c->subtitle));
        else if (ci_eq(k, "timeout")) c->timeout = atoi_(v);
        else if (ci_eq(k, "default")) cpy(c->def, v, sizeof(c->def));
        else if (ci_eq(k, "theme")) { c->palette = ci_eq(v, "ember") ? 1 : ci_eq(v, "glacier") ? 2 : ci_eq(v, "neon") ? 3 : 0; }
        else if (ci_eq(k, "accent")) { c->accent = parse_hex(v); c->has_accent = 1; if (!c->accent2) c->accent2 = mixc(c->accent, 0x101830, 140); }
        else if (ci_eq(k, "accent2")) c->accent2 = parse_hex(v);
        else if (ci_eq(k, "resolution")) { if (!ci_eq(v, "auto")) { c->res_w = atoi_(v); while (*v && *v != 'x') v++; if (*v) c->res_h = atoi_(v + 1); } }
        else if (ci_eq(k, "show_title")) c->show_title = truthy(v);
        else if (ci_eq(k, "show_system_items")) c->show_system = truthy(v);
        else if (ci_eq(k, "show_paths")) c->show_paths = truthy(v);
        else if (ci_eq(k, "demo")) c->demo = truthy(v);
        else if (ci_eq(k, "hide")) cpy(c->hide, v, sizeof(c->hide));
    }
}
