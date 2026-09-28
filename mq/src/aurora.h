#pragma once
#include "gfx.h"

#define MAX_ENTRIES 24
enum { K_OS, K_FIRMWARE, K_REBOOT, K_SHUTDOWN };

typedef struct {
    char name[48];
    CHAR16 path[160];
    EFI_HANDLE dev;
    int kind;
} Entry;

typedef struct {
    char title[48], subtitle[80];
    int timeout;            /* seconds, 0 = never autoboot */
    char def[48];           /* default entry (substring) */
    int palette;            /* -1 = custom / config accent */
    u32 accent, accent2; int has_accent;
    int res_w, res_h;
    int show_title, show_system, demo, show_paths;
    char hide[128];
    int extra_n; Entry extra[8];
} Config;

extern EFI_HANDLE gImage;
extern EFI_LOADED_IMAGE *gLoaded;

void config_defaults(Config *c);
void config_load(Config *c);
int  discover(Entry *out, int max, const Config *c);
