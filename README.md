# H4ck3rMx

H4ck3rMx is a security-first Android-based OS that ships a trust-graph model, hex adjacency enforcement (each app declares up to six trusted peers), and multi-party signing for safer app distribution. The goal is to let users keep control of installs, networking, and inter-app communication while providing audited anchor apps and cosigner-backed manifests.

## What we’re building
- A trust-graph-aware package manager that enforces hex adjacency, cosignature thresholds, and revocation checks.
- Store/developer portal workflows for static/dynamic/AI analysis, sponsorship, and threshold signing.
- OS-level IPC controls (Binder/Intents/foreground services) locked to declared peers, plus SELinux policies generated from manifests.
- Connectivity and driver provisioning flow that can bootstrap networking, fingerprint hardware, and fetch signed vendor driver bundles dynamically.

## Tooling and package prerequisites
Install these on your build/flash host (Linux/macOS/Windows with suitable substitutes):
- `git`, `curl`, `python3`, `jq`
- Android platform tools: `adb`, `fastboot`
- Signing/build helpers: `avbtool`, `openssl`
- Optional diagnostics: `lsusb` (Linux), `uefi-firmware-parser`, `usbutils`
- GitHub CLI (optional for PRs): `gh`

## Getting started (host)
1. Clone the repo: `git clone https://github.com/<user>/H4ck3rMx.git && cd H4ck3rMx`
2. Ensure platform tools are on `PATH` (`adb version`, `fastboot --version` should work).
3. Follow `trust_architecture.md` for trust graph, signing, and enforcement design details.

## Development environment setup
- Run `./scripts/dev-setup.sh` to install common tooling (git, curl, python3, jq, openssl), Android platform tools (adb, fastboot), and optional helpers (avbtool, usbutils). Supports apt, dnf, or Homebrew; otherwise install the equivalents manually.
- Configure GitHub auth (PAT or SSH keys) if you need to push branches or open PRs.
