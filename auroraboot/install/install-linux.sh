#!/usr/bin/env bash
# AuroraBoot installer for Linux (UEFI). Non-destructive: adds a boot entry, never removes yours.
#   sudo ./install-linux.sh --try        boot AuroraBoot ONCE on next reboot (safest; recommended first)
#   sudo ./install-linux.sh              install and add to boot list (does not change boot order)
#   sudo ./install-linux.sh --first      install and make AuroraBoot the first firmware option
#   sudo ./install-linux.sh --uninstall  remove files and boot entry
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<EOF
Usage: sudo $0 [--try | --first | --uninstall]

Installs AuroraBoot.efi and aurora.conf to the mounted EFI System Partition
under EFI/AuroraBoot/ (usually /boot/efi/EFI/AuroraBoot/ on Ubuntu).
By default the firmware boot order is unchanged. Use --first to make
AuroraBoot the default firmware entry, or --try to boot it once.
AuroraBoot chain-loads Ubuntu's existing shim/GRUB; it does not replace GRUB.
EOF
  exit 0
fi
case "${1:-}" in
  ""|--try|--first|--uninstall) ;;
  *) echo "Unknown option '$1'. Use --help for usage." >&2; exit 2 ;;
esac
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Run as root (sudo)."; exit 1; }
[ -d /sys/firmware/efi ] || { echo "This system did not boot in UEFI mode."; exit 1; }
command -v efibootmgr >/dev/null || { echo "Install efibootmgr first."; exit 1; }
HERE="$(cd "$(dirname "$0")/.." && pwd)"
EFI="$HERE/build/AuroraBoot.efi"; [ -f "$EFI" ] || EFI="$HERE/dist/AuroraBoot.efi"
ESP=""; for d in /boot/efi /efi /boot; do mountpoint -q "$d" && findmnt -no FSTYPE "$d" | grep -qi vfat && { ESP="$d"; break; }; done
[ -n "$ESP" ] || { echo "Could not find the mounted EFI System Partition."; exit 1; }
SRC=$(findmnt -no SOURCE "$ESP"); DISK="/dev/$(lsblk -no PKNAME "$SRC")"; PART=$(cat /sys/class/block/"$(basename "$SRC")"/partition)
DEST="$ESP/EFI/AuroraBoot"; LABEL="AuroraBoot"

if [ "${1:-}" = "--uninstall" ]; then
  for n in $(efibootmgr | awk -v l="$LABEL" '$0 ~ l {sub(/^Boot/,"",$1); sub(/\*/,"",$1); print $1}'); do efibootmgr -q -b "$n" -B; done
  rm -rf "$DEST"; echo "AuroraBoot removed."; exit 0
fi
mkdir -p "$DEST"; cp "$EFI" "$DEST/AuroraBoot.efi"
[ -f "$DEST/aurora.conf" ] || cp "$HERE/config/aurora.conf" "$DEST/aurora.conf"
if ! efibootmgr | grep -q "$LABEL"; then efibootmgr -q -c -d "$DISK" -p "$PART" -L "$LABEL" -l '\EFI\AuroraBoot\AuroraBoot.efi'; fi
NUM=$(efibootmgr | awk -v l="$LABEL" '$0 ~ l {sub(/^Boot/,"",$1); sub(/\*/,"",$1); print $1; exit}')
case "${1:-}" in
  --try)   efibootmgr -q -n "$NUM"; echo "Reboot now: AuroraBoot will run ONCE. Your normal boot order is unchanged." ;;
  --first) ORDER=$(efibootmgr | awk '/BootOrder/{print $2}'); efibootmgr -q -o "$NUM,$(echo "$ORDER" | sed "s/\b$NUM\b,\?//;s/,$//")"; echo "AuroraBoot is now first in the boot order." ;;
  "")      echo "Installed as boot entry $NUM (boot order unchanged). Pick it from your firmware boot menu (F12/Esc)." ;;
  *)       echo "Unknown option '$1'. Use --help for usage." >&2; exit 2 ;;
esac
echo "EFI application: $DEST/AuroraBoot.efi"
echo "Configuration:   $DEST/aurora.conf"
echo "Ubuntu note: selecting Ubuntu in AuroraBoot starts Ubuntu's existing shim/GRUB bootloader."
