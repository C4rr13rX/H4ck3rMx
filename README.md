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

## Agent-first experience
- The UX is agent-first (voice/chat), optimized for mobile but scales to desktop. A “classic” Android-like mode remains available.
- System apps and GUI are designed to be driven by the on-device agent, with optional cloud fallbacks.
- Users can supply API keys for OpenAI and other providers (e.g., Anthropic, local endpoints) to run agent inference via third-party services; billing flows remain with those providers.
- Default goal is on-device inference using our neural architecture; cloud keys are optional. Protect keys in secure storage and gate network calls on explicit user consent.

## Licensing and compliance
- This repo’s content is MIT-licensed. Keep the MIT notice when you reuse/redistribute this code.
- Upstream components carry their own licenses: AOSP pieces are typically Apache 2.0/BSD; the Linux kernel is GPLv2 (obligates you to share kernel source + modifications when you distribute binaries); vendor firmware/drivers and proprietary APKs are usually closed and require explicit OEM/vendor permission to redistribute.
- To stay legal and reach the same outcome:
  - Prefer AOSP sources and open drivers where available; keep full source and license notices.
  - For proprietary blobs/apps, use user-supplied sideload flows or obtain redistribution rights; do not bundle without permission.
  - Maintain a NOTICE/THIRD_PARTY file enumerating all third-party components and their licenses.
  - When shipping kernels or other copyleft pieces, publish matching source and build instructions for any released binaries.
