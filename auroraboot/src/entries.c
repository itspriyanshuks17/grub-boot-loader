#include "aurora.h"
int ci_contains(const char *hay, const char *needle);

static const struct { const CHAR16 *path; const char *name; } known[] = {
    { L"\\EFI\\Microsoft\\Boot\\bootmgfw.efi", "Windows" },
    { L"\\EFI\\ubuntu\\shimx64.efi", "Ubuntu" }, { L"\\EFI\\ubuntu\\grubx64.efi", "Ubuntu" },
    { L"\\EFI\\fedora\\shimx64.efi", "Fedora" }, { L"\\EFI\\debian\\shimx64.efi", "Debian" },
    { L"\\EFI\\arch\\grubx64.efi", "Arch Linux" }, { L"\\EFI\\opensuse\\grubx64.efi", "openSUSE" },
    { L"\\EFI\\linuxmint\\shimx64.efi", "Linux Mint" }, { L"\\EFI\\pop\\grubx64.efi", "Pop!_OS" },
    { L"\\EFI\\manjaro\\grubx64.efi", "Manjaro" }, { L"\\EFI\\kali\\shimx64.efi", "Kali Linux" },
    { L"\\EFI\\systemd\\systemd-bootx64.efi", "systemd-boot" }, { L"\\EFI\\refind\\refind_x64.efi", "rEFInd" },
    { L"\\EFI\\zorin\\shimx64.efi", "Zorin OS" }, { L"\\shellx64.efi", "UEFI Shell" },
};

static int have(Entry *o, int n, const char *name, EFI_HANDLE dev) {
    for (int i = 0; i < n; i++) if (o[i].dev == dev && ci_contains(o[i].name, name) && ci_contains(name, o[i].name)) return 1;
    return 0;
}
static void add(Entry *o, int *n, int max, const char *name, const CHAR16 *path, EFI_HANDLE dev) {
    if (*n >= max || have(o, *n, name, dev)) return;
    Entry *e = &o[(*n)++]; SetMem(e, sizeof(*e), 0);
    int i = 0; for (; name[i] && i < 47; i++) e->name[i] = name[i];
    StrnCpy(e->path, path, 159); e->path[159] = 0; e->dev = dev; e->kind = K_OS;
}
static int exists(EFI_FILE_HANDLE root, const CHAR16 *p) {
    EFI_FILE_HANDLE f; if (EFI_ERROR(uefi_call_wrapper(root->Open, 5, root, &f, (CHAR16 *)p, EFI_FILE_MODE_READ, 0))) return 0;
    uefi_call_wrapper(f->Close, 1, f); return 1;
}
static int hidden(const Config *c, const char *name) {
    char tmp[128]; int n = 0; for (int i = 0; c->hide[i] && n < 127; i++) tmp[n++] = c->hide[i]; tmp[n] = 0;
    for (char *p = tmp; *p;) { char *s = p; while (*p && *p != ',') p++; if (*p) *p++ = 0; while (*s == ' ') s++; if (*s && ci_contains(name, s)) return 1; }
    return 0;
}

int discover(Entry *out, int max, const Config *c) {
    int n = 0;
    if (c->demo) {
        static const struct { const char *n; const CHAR16 *p; } d[] = {
            { "Windows 11", L"\\EFI\\Microsoft\\Boot\\bootmgfw.efi" }, { "Ubuntu 24.04", L"\\EFI\\ubuntu\\shimx64.efi" },
            { "Fedora", L"\\EFI\\fedora\\shimx64.efi" }, { "Arch Linux", L"\\EFI\\arch\\grubx64.efi" }, { "Debian", L"\\EFI\\debian\\shimx64.efi" } };
        for (int i = 0; i < 5; i++) add(out, &n, max, d[i].n, d[i].p, NULL);
    } else {
        EFI_HANDLE *hs; UINTN cnt;
        if (!EFI_ERROR(uefi_call_wrapper(BS->LocateHandleBuffer, 5, ByProtocol, &FileSystemProtocol, NULL, &cnt, &hs))) {
            for (UINTN h = 0; h < cnt; h++) {
                EFI_FILE_HANDLE root = LibOpenRoot(hs[h]); if (!root) continue;
                for (UINTN k = 0; k < sizeof(known) / sizeof(known[0]); k++) if (exists(root, known[k].path)) add(out, &n, max, known[k].name, known[k].path, hs[h]);
                /* generic scan of \EFI\<dir>\{shimx64,grubx64}.efi */
                EFI_FILE_HANDLE efi;
                if (!EFI_ERROR(uefi_call_wrapper(root->Open, 5, root, &efi, L"\\EFI", EFI_FILE_MODE_READ, 0))) {
                    CHAR16 dirs[24][40]; int nd = 0; UINT8 buf[600];
                    for (;;) {
                        UINTN sz = sizeof(buf); if (EFI_ERROR(uefi_call_wrapper(efi->Read, 3, efi, &sz, buf)) || !sz) break;
                        EFI_FILE_INFO *fi = (EFI_FILE_INFO *)buf;
                        if ((fi->Attribute & EFI_FILE_DIRECTORY) && fi->FileName[0] != L'.' && nd < 24) { StrnCpy(dirs[nd], fi->FileName, 39); dirs[nd][39] = 0; nd++; }
                    }
                    uefi_call_wrapper(efi->Close, 1, efi);
                    for (int d = 0; d < nd; d++) {
                        char nm[48]; int i = 0; for (; dirs[d][i] && i < 47; i++) nm[i] = (char)dirs[d][i]; nm[i] = 0;
                        if (ci_contains(nm, "boot") && nm[4] == 0) continue;
                        if (ci_contains(nm, "aurora") || ci_contains(nm, "microsoft")) continue;
                        int dup = 0; for (int q = 0; q < n; q++) if (out[q].dev == hs[h] && (ci_contains(out[q].name, nm) || ci_contains(nm, out[q].name))) dup = 1;
                        if (dup) continue;
                        CHAR16 p[160]; static const CHAR16 *files[] = { L"shimx64.efi", L"grubx64.efi" };
                        for (int f = 0; f < 2; f++) {
                            SPrint(p, sizeof(p), L"\\EFI\\%s\\%s", dirs[d], files[f]);
                            if (exists(root, p)) { if (nm[0] >= 'a' && nm[0] <= 'z') nm[0] -= 32; add(out, &n, max, nm, p, hs[h]); break; }
                        }
                    }
                }
                if (hs[h] != gLoaded->DeviceHandle && exists(root, L"\\EFI\\BOOT\\BOOTX64.EFI")) add(out, &n, max, "Removable Media", L"\\EFI\\BOOT\\BOOTX64.EFI", hs[h]);
            }
        }
    }
    for (int i = 0; i < c->extra_n && n < max; i++) if (c->extra[i].name[0] && c->extra[i].path[0]) { out[n] = c->extra[i]; if (!out[n].dev) out[n].dev = gLoaded->DeviceHandle; n++; }
    /* apply hide list */
    int m = 0; for (int i = 0; i < n; i++) if (!hidden(c, out[i].name)) out[m++] = out[i];
    n = m;
    if (c->show_system) {
        static const struct { const char *name; int kind; } sys[] = { { "Firmware Setup", K_FIRMWARE }, { "Restart", K_REBOOT }, { "Shut Down", K_SHUTDOWN } };
        for (int i = 0; i < 3 && n < max; i++) { Entry *e = &out[n++]; SetMem(e, sizeof(*e), 0); int j = 0; for (; sys[i].name[j]; j++) e->name[j] = sys[i].name[j]; e->kind = sys[i].kind; }
    }
    return n;
}
