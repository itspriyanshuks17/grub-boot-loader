# Marquardt GRUB Theme

A minimal dark GRUB bootloader theme with multiple color palettes, branded for Marquardt.

## Themes

Open [`docs/preview.html`](docs/preview.html) in a browser to see all themes side by side.

| Name | Accent | Hint |
|---|---|---|
| `marquardt` | Teal `#009aa6` | Original branded look |
| `aurora` | Teal/Purple `#2de3b5` / `#7c5cff` | Cool sky |
| `ember` | Orange/Red `#ff8a3d` / `#e0245e` | Warm fire |
| `glacier` | Blue `#5cc8ff` / `#2a6bff` | Ice cold |
| `neon` | Pink/Cyan `#ff3da5` / `#22e5ff` | Synthwave |
| `mq` | Dark Teal `#009aa6` / `#0b4f5c` | Marquardt branded |

## Structure

```
themes/
  marquardt/   — original teal branded theme
  aurora/      — teal + purple
  ember/       — orange + red
  glacier/     — light blue + deep blue
  neon/        — pink + cyan
  mq/           — Marquardt branded dark teal
  (each folder contains theme.txt + all assets)
theme/         — original source assets
install.sh     — interactive installer / uninstaller
```

## Install

```bash
sudo ./install.sh
```

Presents a numbered menu to pick a theme, then installs it and runs `update-grub` / `grub2-mkconfig` automatically.

## Switch theme

Run the installer again — it will overwrite the current theme with your new choice.

```bash
sudo ./install.sh
```

## Uninstall

```bash
sudo ./install.sh --uninstall
```

Removes the installed theme files and cleans `/etc/default/grub`. A backup is kept at `/etc/default/grub.bak-grubtheme`.

## Manual install

```bash
sudo cp -r themes/marquardt/ /boot/grub/themes/marquardt
# add to /etc/default/grub:
GRUB_THEME="/boot/grub/themes/marquardt/theme.txt"
GRUB_GFXMODE=1920x1080,auto
sudo update-grub   # or: sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

## Test without installing

In a running GRUB command line (`c` at the menu):

```
loadfont (hd0,1)/boot/grub/fonts/unicode.pf2
set theme=(hd0,1)/boot/grub/themes/marquardt/theme.txt
export theme
```

## Notes

- Themes only GRUB's menu; does not touch Windows Boot Manager or shim.
- On company laptops: check with IT — Secure Boot / BitLocker / TPM policies may flag boot-chain changes.
- Fedora: if `GRUB_THEME` is ignored on BLS systems, set `GRUB_ENABLE_BLSCFG=false` only if you understand your setup.
