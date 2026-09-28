#!/usr/bin/env bash
# GRUB theme installer with theme selection
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Run with sudo."; exit 1; }

GRUB_CFG="/etc/default/grub"
THEMES_DIR="$(cd "$(dirname "$0")" && pwd)/themes"

# Detect GRUB config command and themes install path
if [ -d /boot/grub2 ]; then
    GRUB_THEMES="/boot/grub2/themes"
    MKCONFIG="grub2-mkconfig -o /boot/grub2/grub.cfg"
else
    GRUB_THEMES="/boot/grub/themes"
    MKCONFIG="update-grub"
    command -v update-grub >/dev/null || MKCONFIG="grub-mkconfig -o /boot/grub/grub.cfg"
fi

# --- Uninstall ---
if [ "${1:-}" = "--uninstall" ]; then
    INSTALLED=$(grep '^GRUB_THEME=' "$GRUB_CFG" 2>/dev/null | sed 's/.*themes\/\([^/]*\)\/.*/\1/' || true)
    [ -n "$INSTALLED" ] && rm -rf "$GRUB_THEMES/$INSTALLED"
    sed -i '/^GRUB_THEME=/d' "$GRUB_CFG"
    $MKCONFIG
    echo "Uninstalled. Reboot to apply."
    exit 0
fi

# --- Theme picker ---
LOCKED_THEMES=("marquardt" "mq")
ACCESS_KEY="interns@mqi2025"

THEMES=()
for d in "$THEMES_DIR"/*/; do
    THEMES+=("$(basename "$d")")
done

# Direct theme via --theme flag (used by website unlock flow)
if [ -n "${2:-}" ] && [ "${1:-}" = "--theme" ]; then
    THEME="$2"
else
    echo ""
    echo "Available themes:"
    for i in "${!THEMES[@]}"; do
        NAME="${THEMES[$i]}"
        LOCKED=""
        for lt in "${LOCKED_THEMES[@]}"; do [ "$NAME" = "$lt" ] && LOCKED=" [access key required]"; done
        echo "  $((i+1))) $NAME$LOCKED"
    done
    echo ""
    read -rp "Select a theme [1-${#THEMES[@]}]: " CHOICE
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#THEMES[@]}" ]; then
        echo "Invalid choice."; exit 1
    fi
    THEME="${THEMES[$((CHOICE-1))]}"
fi

# Check if locked
for lt in "${LOCKED_THEMES[@]}"; do
    if [ "$THEME" = "$lt" ]; then
        read -rsp "Enter access key for '$THEME': " KEY; echo
        if [ "$KEY" != "$ACCESS_KEY" ]; then
            echo "Invalid access key."; exit 1
        fi
    fi
done
SRC="$THEMES_DIR/$THEME"
DEST="$GRUB_THEMES/$THEME"

echo "Installing theme: $THEME"
mkdir -p "$DEST"
cp -r "$SRC/"* "$DEST/"

cp -n "$GRUB_CFG" "${GRUB_CFG}.bak-grubtheme" 2>/dev/null || true

if grep -q '^GRUB_THEME=' "$GRUB_CFG"; then
    sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$DEST/theme.txt\"|" "$GRUB_CFG"
else
    echo "GRUB_THEME=\"$DEST/theme.txt\"" >> "$GRUB_CFG"
fi

grep -q '^GRUB_GFXMODE=' "$GRUB_CFG" || echo 'GRUB_GFXMODE=1920x1080,auto' >> "$GRUB_CFG"
sed -i 's|^GRUB_TERMINAL_OUTPUT=|#GRUB_TERMINAL_OUTPUT=|' "$GRUB_CFG"

$MKCONFIG
echo ""
echo "Done! Theme '$THEME' installed. Reboot to see it."
echo "To switch themes, run this script again."
echo "To uninstall: sudo $0 --uninstall"
