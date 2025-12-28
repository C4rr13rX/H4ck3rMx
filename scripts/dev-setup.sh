#!/usr/bin/env bash
set -euo pipefail

echo \"[+] Detecting package manager...\"
PKG_MANAGER=\"\"
if command -v apt-get >/dev/null 2>&1; then
  PKG_MANAGER=\"apt-get\"
elif command -v dnf >/dev/null 2>&1; then
  PKG_MANAGER=\"dnf\"
elif command -v brew >/dev/null 2>&1; then
  PKG_MANAGER=\"brew\"
fi

if [[ -z \"${PKG_MANAGER}\" ]]; then
  echo \"[-] Supported package manager not found (apt-get, dnf, brew). Install dependencies manually.\" >&2
  exit 1
fi

echo \"[+] Using package manager: ${PKG_MANAGER}\"

COMMON_PACKAGES=(
  git
  curl
  python3
  jq
  openssl
)

ANDROID_PACKAGES=(
  adb
  fastboot
)

EXTRA_PACKAGES=(
  avbtool
  usbutils
  udev
)

install_packages() {
  local packages=(\"$@\")
  if [[ \"${PKG_MANAGER}\" == \"apt-get\" ]]; then
    sudo apt-get update
    sudo apt-get install -y \"${packages[@]}\"
  elif [[ \"${PKG_MANAGER}\" == \"dnf\" ]]; then
    sudo dnf install -y \"${packages[@]}\"
  elif [[ \"${PKG_MANAGER}\" == \"brew\" ]]; then
    brew install \"${packages[@]}\"
  fi
}

echo \"[+] Installing common tooling...\"
install_packages \"${COMMON_PACKAGES[@]}\"

echo \"[+] Installing Android platform tools...\"
install_packages \"${ANDROID_PACKAGES[@]}\" || {
  echo \"[!] adb/fastboot package names may differ on this platform; install platform-tools manually if needed.\" >&2
}

echo \"[+] Installing signing/debug helpers (optional)...\"
install_packages \"${EXTRA_PACKAGES[@]}\" || true

echo \"[+] Verifying versions...\"
command -v git && git --version
command -v adb && adb version || echo \"[!] adb not found; install platform-tools manually.\"
command -v fastboot && fastboot --version || echo \"[!] fastboot not found; install platform-tools manually.\"
command -v avbtool && avbtool info_image --help >/dev/null 2>&1 || echo \"[!] avbtool not found; install from AOSP or distro package.\"

echo \"[+] Done. Ensure GitHub authentication is configured if pushing to remote (use PAT or SSH keys).\"
