# Marquardt GRUB Theme
Files: theme/ (theme.txt, background.png, selection graphics), install.sh

Install:   sudo ./install.sh      Undo: see last line of install.sh output
Test first: put theme/ in a Linux VM, or in GRUB press `c` and run `loadfont`/`set theme=...`.
Fedora: paths use /boot/grub2 and grub2-mkconfig (script handles it); if GRUB_THEME is ignored on
BLS systems, set GRUB_ENABLE_BLSCFG=false only if you know your setup.

Company-laptop notes:
- Check with IT first. Secure Boot/BitLocker/TPM policies may flag boot-chain changes.
- This only themes GRUB's menu; it doesn't replace Windows Boot Manager or shim.
- Keep the .bak-marquardt backup of /etc/default/grub.
