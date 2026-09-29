#!/usr/bin/env bash
# Preview a bundled GRUB theme in QEMU/OVMF without touching your real system.
#   tools/preview-theme.sh aurora            # opens a QEMU window
#   tools/preview-theme.sh aurora shot.png   # headless: saves a screenshot after ~7 s
# Needs: grub-mkstandalone (grub-common + grub-efi-amd64-bin), qemu-system-x86, ovmf, mtools, python3-pil
set -euo pipefail
THEME="${1:?usage: $0 THEME [screenshot.png]}"; SHOT="${2:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; SRC="${THEMES_DIR:-$ROOT/themes}/$THEME"
[ -f "$SRC/theme.txt" ] || { echo "no such theme: $THEME" >&2; exit 1; }
WAIT="${WAIT:-7}"; TMO="${TMO:-30}"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
cat > "$W/grub.cfg" <<CFG
insmod all_video
insmod gfxterm
insmod png
insmod gfxmenu
set gfxmode=1920x1080
terminal_output gfxterm
set timeout=$TMO
$(for f in "$SRC"/*.pf2; do echo "loadfont (memdisk)/themes/$THEME/$(basename "$f")"; done)
set theme=(memdisk)/themes/$THEME/theme.txt
menuentry 'Windows 11' --class windows --class os { true; }
menuentry 'Ubuntu 24.04 LTS' --class ubuntu --class gnu-linux --class gnu --class os { true; }
menuentry 'Fedora Linux 40' --class fedora --class gnu-linux --class gnu --class os { true; }
menuentry 'Arch Linux' --class arch --class gnu-linux --class gnu --class os { true; }
menuentry 'Advanced options' --class gnu-linux --class gnu --class os { true; }
menuentry 'UEFI Firmware Settings' --class efi { true; }
CFG
ARGS=("boot/grub/grub.cfg=$W/grub.cfg")
while IFS= read -r -d '' f; do ARGS+=("themes/$THEME/${f#$SRC/}=$f"); done < <(find "$SRC" -type f -print0)
mkdir -p "$W/esp/EFI/BOOT"
grub-mkstandalone -O x86_64-efi -o "$W/esp/EFI/BOOT/BOOTX64.EFI" --themes= --fonts= --locales= \
    --modules="part_gpt fat memdisk all_video gfxterm gfxmenu png" "${ARGS[@]}" >/dev/null
CODE=/usr/share/OVMF/OVMF_CODE_4M.fd; cp /usr/share/OVMF/OVMF_VARS_4M.fd "$W/vars.fd"
COMMON=(-machine q35 -m 1024 -drive if=pflash,format=raw,readonly=on,file=$CODE
        -drive if=pflash,format=raw,file="$W/vars.fd" -drive file=fat:rw:"$W/esp",format=raw -vga std)
if [ -z "$SHOT" ]; then exec qemu-system-x86_64 "${COMMON[@]}"; fi
qemu-system-x86_64 "${COMMON[@]}" -display none -monitor unix:"$W/mon",server,nowait &
QP=$!; sleep "$WAIT"
echo "screendump $W/s.ppm" | python3 -c "
import socket,sys,time
s=socket.socket(socket.AF_UNIX); s.connect('$W/mon'); time.sleep(.3); s.recv(4096)
s.send((sys.stdin.read()+'\n').encode()); time.sleep(1.5)"
kill $QP 2>/dev/null || true
python3 -c "from PIL import Image; Image.open('$W/s.ppm').convert('RGB').save('$SHOT')"
echo "saved $SHOT"
