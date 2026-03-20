#!/bin/bash
# Install CryptoDistro 2.0 desktop entry and icon for the current user.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ICON_SRC="$ROOT/assets/icon.png"
ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"

mkdir -p "$ICON_DIR" "$APP_DIR"

# Install icon
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$ICON_DIR/cryptodistro.png"
  echo "Icon installed to $ICON_DIR/cryptodistro.png"
else
  echo "Warning: icon not found at $ICON_SRC"
fi

# Generate desktop entry with correct paths
cat > "$APP_DIR/CryptoDistro.desktop" <<EOF
[Desktop Entry]
Name=CryptoDistro 2.0
Comment=P2P Bitcoin Trading Dashboard
Exec=$ROOT/scripts/launch.sh
Icon=$ICON_DIR/cryptodistro.png
Terminal=false
Type=Application
Categories=Finance;Network;
StartupNotify=true
EOF

chmod +x "$APP_DIR/CryptoDistro.desktop"
echo "Desktop entry installed to $APP_DIR/CryptoDistro.desktop"
