#!/bin/sh
# Try AuroraBoot in a VM (demo entries). Needs qemu-system-x86_64 and OVMF (edk2).
set -e
cd "$(dirname "$0")/.."
OVMF=${OVMF:-$(ls /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd /usr/share/edk2/ovmf/OVMF_CODE.fd /usr/share/edk2-ovmf/x64/OVMF_CODE.fd 2>/dev/null | head -1)}
[ -n "$OVMF" ] || { echo "OVMF firmware not found (install ovmf / edk2-ovmf)"; exit 1; }
rm -rf build/esp && mkdir -p build/esp/EFI/BOOT build/esp/EFI/AuroraBoot
cp build/AuroraBoot.efi build/esp/EFI/BOOT/BOOTX64.EFI
cp "${CONF:-config/demo.conf}" build/esp/EFI/AuroraBoot/aurora.conf
exec qemu-system-x86_64 -machine q35 -m 512 -vga std ${QEMU_EXTRA:-} \
  -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
  -drive format=raw,file=fat:rw:build/esp -usb -device usb-mouse
