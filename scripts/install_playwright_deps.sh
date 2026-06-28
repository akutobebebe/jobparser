#!/usr/bin/env bash
# Installs Playwright WebKit system dependencies for common Linux distros.
# Usage: bash scripts/install_playwright_deps.sh
set -euo pipefail

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID:-unknown}"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)

echo "Detected distro: $DISTRO"

case "$DISTRO" in
    ubuntu|debian|linuxmint|pop)
        sudo apt-get update -q
        sudo apt-get install -y \
            libicu74 \
            libjpeg-turbo8 \
            libwoff1 \
            gstreamer1.0-libav \
            libgbm1 \
            libxkbcommon0 \
            libatk1.0-0 \
            libatk-bridge2.0-0 \
            libcups2 \
            libdrm2 \
            libgtk-3-0 \
            libx11-xcb1 \
            libxcomposite1 \
            libxdamage1 \
            libxrandr2 \
            libnss3 \
            libpango-1.0-0 \
            libcairo2
        ;;

    fedora)
        sudo dnf install -y \
            libicu \
            libjpeg-turbo \
            woff2 \
            gstreamer1-plugin-libav \
            mesa-libgbm \
            libxkbcommon \
            atk \
            at-spi2-atk \
            cups-libs \
            libdrm \
            gtk3 \
            libX11-xcb \
            libXcomposite \
            libXdamage \
            libXrandr \
            nss \
            pango \
            cairo
        ;;

    rhel|centos|almalinux|rocky)
        sudo dnf install -y epel-release
        sudo dnf install -y \
            libicu \
            libjpeg-turbo \
            woff2 \
            gstreamer1-plugin-libav \
            mesa-libgbm \
            libxkbcommon \
            atk \
            at-spi2-atk \
            cups-libs \
            libdrm \
            gtk3 \
            libX11-xcb \
            libXcomposite \
            libXdamage \
            libXrandr \
            nss \
            pango \
            cairo
        ;;

    arch|manjaro|endeavouros)
        sudo pacman -S --noconfirm \
            icu \
            libjpeg-turbo \
            woff2 \
            gst-libav \
            mesa \
            libxkbcommon \
            at-spi2-atk \
            cups \
            libdrm \
            gtk3 \
            libx11 \
            libxcomposite \
            libxdamage \
            libxrandr \
            nss \
            pango \
            cairo
        ;;

    opensuse*|sles)
        sudo zypper install -y \
            libicu \
            libjpeg-turbo \
            woff2 \
            gstreamer-plugins-libav \
            Mesa-libgbm \
            libxkbcommon \
            atk \
            at-spi2-atk \
            cups-libs \
            libdrm \
            gtk3 \
            libX11-xcb1 \
            libXcomposite1 \
            libXdamage1 \
            libXrandr2 \
            mozilla-nss \
            pango \
            cairo
        ;;

    *)
        echo "Unsupported distro: $DISTRO"
        echo "Try running:  playwright install-deps"
        echo "Or install packages manually — see: https://playwright.dev/python/docs/browsers#install-system-dependencies"
        exit 1
        ;;
esac

echo ""
echo "Installing Playwright WebKit browser..."
playwright install webkit

echo ""
echo "Done! Run 'python cli.py' or 'streamlit run app.py' to start."
