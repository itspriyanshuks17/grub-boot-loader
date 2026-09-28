#!/usr/bin/env bash
# Installs the Marquardt GRUB theme (Debian/Ubuntu style; Fedora notes in README)
set -e
[ "$EUID" -eq 0 ] || { echo "Run with sudo"; exit 1; }
DEST=/boot/grub/themes/marquardt
mkdir -p "$DEST"
cp -r theme/* "$DEST"/
cp -n /etc/default/grub /etc/default/grub.bak-marquardt
if grep -q '^GRUB_THEME=' /etc/default/grub; then
  sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$DEST/theme.txt\"|" /etc/default/grub
else
  echo "GRUB_THEME=\"$DEST/theme.txt\"" >> /etc/default/grub
fi
grep -q '^GRUB_GFXMODE=' /etc/default/grub || echo 'GRUB_GFXMODE=1920x1080,auto' >> /etc/default/grub
sed -i 's|^#\?GRUB_TERMINAL_OUTPUT=.*|#GRUB_TERMINAL_OUTPUT=console|' /etc/default/grub
if command -v update-grub >/dev/null; then update-grub
else grub2-mkconfig -o "$(ls /boot/grub2/grub.cfg /boot/efi/EFI/*/grub.cfg 2>/dev/null | head -1)"; fi
echo "Done. Reboot to see the theme. Undo: cp /etc/default/grub.bak-marquardt /etc/default/grub && sudo update-grub"
