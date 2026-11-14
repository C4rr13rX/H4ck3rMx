# H4ck3rMx

**A custom, security-first Linux distribution built for Android-compatible mobile devices.**  
*Engineered for hackers, anarchists, privacy advocates, and individuals who demand absolute sovereignty over their devices, code, and communications.*

> **Clarification of Architecture:**  
> H4ck3rMx is **not based on Android**. It does not run the Android framework, ART/Dalvik virtual machine, or Google/AOSP userland as its operating system. H4ck3rMx is a **pure Linux distribution** (glibc/musl userland, standard Linux init, Wayland, PipeWire, ModemManager, native containers) built to run directly on the physical hardware of mass-market, Android-compatible smartphones and tablets.  
> 
> Leveraging device trees, vendor partitions, firmware blobs, and hardware abstraction layers (HALs) originally authored for Android devices does not make an operating system "Android-based"—it enables a sovereign Linux operating system to drive complex modern mobile hardware stably, securely, and legally as a non-profit initiative.

---

## What We Are Building

1. **A Custom Linux OS for Mobile Hardware:** A native Linux distribution engineered from the ground up for mobile form factors, low-power ARM64 SoCs, touchscreen input, cellular connectivity, and dynamic power management.
2. **Official Hardware Driver & Firmware Integration:** An automated, verifiable pipeline that pulls, verifies, and packages official drivers, firmware, and kernel updates from official OEM and chipset repositories to ensure maximum device stability and peripheral support (cellular modems, Wi-Fi, Bluetooth, GPU acceleration, cameras, and audio DSPs).
3. **Hex Adjacency Trust Graph Package Manager:** A revolutionary software distribution and isolation model where each application declares at most six trusted peers (`trusted_peers <= 6`), enforced by multi-party threshold cosignatures (6-of-N cosigners), transparency logs, and kernel-level IPC confinement.
4. **Agent-First Native UX:** A voice- and chat-orchestrated operating experience optimized for fast mobile interaction, terminal power, and agentic task execution, powered by on-device neural models with optional user-provided cloud API fallbacks.
5. **Non-Profit, Legally Bulletproof Delivery:** Clear separation between copyleft (GPL kernel sources), permissive open-source (MIT H4ck3rMx core), and proprietary vendor microcode, ensuring legal compliance, transparency, and reproducible builds.

---

## Hardware & Driver Strategy

Modern mobile devices (Qualcomm Snapdragon, MediaTek, Samsung Exynos, Google Tensor) feature intricate proprietary hardware subsystems that standard desktop Linux kernels do not support out-of-the-box. H4ck3rMx bridges this divide using a comprehensive hardware enablement strategy:

### 1. Dual-Track Hardware Enablement
- **Track A: Direct Mainline Linux (Pure Open Source):**  
  On supported platforms (e.g., Qualcomm SDM845, SM8250, SM8350, Sony Open Devices, Fairphone), H4ck3rMx runs upstream Linux kernels, direct DRM/KMS graphics with Mesa (Freedreno/Panfrost), ALSA/PipeWire audio, and native `ModemManager` cellular control.
- **Track B: Treble HAL Compatibility Bridge (Ecosystem Enablement):**  
  For devices requiring proprietary vendor modules, H4ck3rMx interfaces with the device's native Project Treble vendor partitions (`/vendor` and `/odm`) through an isolated, sandboxed translation bridge (`libhybris` and minimal Bionic dynamic loader shims). Standard Linux daemons (PipeWire for audio, ModemManager for cellular, Wayland for display) communicate with the hardware HALs inside confined namespaces without running Android system services.

### 2. Sourcing Drivers from Official Sources
- **Official OEM Kernel Releases (GPLv2):** OEMs (Google, OnePlus, Xiaomi, Motorola, Sony, Samsung) are legally bound to release kernel source code for each firmware version. We automate the ingestion, hardening, and compilation of these official kernel trees.
- **Official OEM Factory Firmware & OTA Payloads:** We extract device firmware, DSP microcode, and vendor binaries directly from official OEM factory images and OTA packages (`payload.bin`, `super.img`) with automated cryptographic verification against vendor certificates.
- **Chipset Vendor Repositories:** Direct integration of reference BSPs and open-source HALs from Qualcomm Innovation Center (CodeLinaro), Android Common Kernels (ACK/GKI), and Linaro.
- **Upstream Linux Repositories:** Ongoing backporting and alignment with upstream `linux-firmware` and Mesa drivers.

### 3. Dynamic Hardware Fingerprinting & Atomic Driver OTAs
- **On-Boot Discovery:** Minimal initramfs discovery agents fingerprint hardware components (SoC ID, board revision, modem baseband version, PCI/USB IDs).
- **H4ck3rMx Driver Packages (`.hdp`):** Drivers are packaged into cryptographically signed, standalone bundles decoupled from the base OS root filesystem.
- **Atomic A/B Slotting:** Hardware updates are applied to alternate partitions with automatic health-check rollbacks to prevent bricking or connectivity loss.

For the complete technical blueprint, read our [Hardware Enablement & Driver Strategy](docs/hardware_and_driver_strategy.md).

---

## Hex Adjacency Trust Architecture

H4ck3rMx replaces the conventional, opaque app-store model with a mathematical, tamper-evident trust graph:

- **Hex Adjacency Rule:** Each application explicitly declares up to six trusted peers (`trusted_peers <= 6`). Inter-process communication (IPC), shared sockets, and local network exchanges are restricted strictly to this declared hexagonal neighborhood.
- **Threshold Cosigning:** Applications require 6-of-N independent cosigner attestations from verified security analysts and community cosigners before installation is permitted by the package manager.
- **Kernel-Level Enforcement:** Linux security modules (SELinux / AppArmor), network namespaces, and seccomp filters are automatically generated from the application's signed `trust_manifest.json`.
- **Tamper-Evident Transparency:** All manifests, sponsorships, and revocations are committed to an append-only, Merkle-linked public audit log.

For full mathematical and implementation details, see [Trust Architecture](trust_architecture.md).

---

## Tooling and Prerequisites

To build, test, or flash H4ck3rMx on your host machine (Linux, macOS, or Windows):
- **Core CLI Tools:** `git`, `curl`, `python3`, `jq`, `openssl`
- **Android Platform & Flashing Tools:** `adb`, `fastboot` (used strictly for interacting with Android bootloaders and fastboot/fastbootd partitions)
- **Image & Signing Helpers:** `avbtool`, `mkbootimg`, `payload_dumper`, `simg2img`, `lpunpack`
- **Diagnostics (optional):** `lsusb`, `usbutils`, `uefi-firmware-parser`
- **GitHub CLI:** `gh`

### Host Setup
Run our bootstrap script to install host dependencies:
```bash
./scripts/dev-setup.sh
```

---

## Agent-First Operating Experience

- **Voice and Chat Native:** Built with a primary agentic interface. Users can inspect system logs, query network connections, manage files, configure firewall rules, or interact with apps using conversational commands.
- **Local Neural Engine:** Engineered for local, on-device inference using quantized neural models running on mobile NPUs and GPUs.
- **Sovereign Cloud Keys:** Users may supply their own API keys (OpenAI, Anthropic, Ollama, self-hosted endpoints) for hybrid inference. Keys remain encrypted locally and are never exfiltrated.
- **Terminal Power:** Full Linux terminal capabilities available at all times (zsh/bash, tmux, SSH, Python, native compilers).

---

## Licensing, Non-Profit Mission & Compliance

H4ck3rMx is developed and provided as a non-profit initiative dedicated to digital sovereignty and user freedom.

- **H4ck3rMx Core:** Licensed under the [MIT License](LICENSE).
- **Linux Kernel & Driver Patches:** Licensed under the **GNU General Public License v2 (GPLv2)**. We publish full source code, configuration manifests, and build scripts for all distributed kernel binaries in strict compliance with the GPL.
- **Hardware Adaptation & Firmware Blobs:**
  - Proprietary vendor blobs (modem baseband microcode, GPU firmware) are never unlawfully bundled.
  - The OS utilizes clean-room, user-side extraction scripts or preserves the device's original OEM-licensed `/vendor` partition directly on the physical hardware.
  - Every release includes a comprehensive Software Bill of Materials (SBOM) and third-party license notices.
