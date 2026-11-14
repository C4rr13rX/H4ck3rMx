# H4ck3rMx Hardware Enablement & Driver Strategy

## 1. Vision & Core Distinction: Linux vs. Android

**H4ck3rMx is a custom, security-first Linux distribution built for Android-compatible mobile devices—it is NOT based on Android.**

### What This Means:
- **No Android Userland:** The operating system does not run the Android Open Source Project (AOSP) framework, SystemServer, ActivityManager, Zygote, or the Android Runtime (ART/Dalvik) as its base operating system.
- **Pure Linux Userland:** The core system is a native Linux distribution (glibc or musl userland, standard Linux init systems such as `systemd` or `runit`, Wayland display server, standard IPC, and native containerization).
- **Targeting Android Hardware:** The global mobile market is dominated by hardware designed and manufactured for the Android ecosystem (Qualcomm Snapdragon, MediaTek, Samsung Exynos, Google Tensor). This hardware features specialized power management ICs (PMICs), baseband cellular modems, audio DSPs, camera ISPs, and proprietary GPU architectures.
- **Hardware Enablement vs. OS Heritage:** In as much as we utilize repositories, device trees, kernel configurations, and HAL interfaces from the Android ecosystem to achieve hardware stability, we do so strictly as a **hardware enablement bridge**. Utilizing drivers, firmware, and adaptation layers to boot a device and power its peripherals does not make an OS "based on Android"—it makes the hardware functional for a sovereign Linux operating system.

---

## 2. System Architecture Blueprint

```
+--------------------------------------------------------------------------+
|                       H4ck3rMx Native Linux Userland                      |
|  - Agent-First Interface (Voice/Chat Orchestrator)                       |
|  - Hex Adjacency Trust Graph Package Manager & Policy Enforcement        |
|  - Wayland Compositor (Phosh / Sway / Custom Mobile UI)                  |
|  - Native Linux Subsystems (PipeWire, ModemManager, NetworkManager)      |
|  - Optional Android App Sandbox Container (Isolated Waydroid/LXC)       |
+--------------------------------------------------------------------------+
|                     Hardware Abstraction Bridge Layer                     |
|  - libhybris / Minimal Bionic Driver Harness (Sandboxed in Containers)   |
|  - Native-to-HAL Translators (Audio, RIL/QMI/MBIM, Camera, Sensors)     |
|  - Direct Linux DRM/KMS, Mesa (Freedreno/Panfrost), libcamera             |
+--------------------------------------------------------------------------+
|                         Linux Kernel Subsystem                           |
|  - Track A: Mainline Linux with Device Tree overlays (where available)    |
|  - Track B: Hardened Vendor LTS Kernel with Android Driver Stubs (GPLv2) |
+--------------------------------------------------------------------------+
|                     Firmware & Partition Environment                     |
|  - Bootloader: ABOOT / LittleKernel / EDK2 (Android Boot Header v2/v3/v4)|
|  - Dynamic Partitions: /system (H4ck3rMx Linux Rootfs), /vendor, /odm    |
|  - Peripheral Firmware: Modem Baseband, DSP/Hexagon, GPU microcode, Wi-Fi|
+--------------------------------------------------------------------------+
```

---

## 3. Hardware Abstraction & Driver Bridge

Smartphone SoCs rely on proprietary vendor microcode, firmware, and Board Support Packages (BSPs). H4ck3rMx approaches hardware enablement through a two-track strategy:

### Track A: Direct Mainline Linux (Pure Open-Source Stack)
For platforms with established or developing mainline Linux kernel support (e.g., Qualcomm Snapdragon SDM845, SM8250, SM8350, Fairphone, Pine64, and Sony Open Devices):
- **Graphics:** Direct Linux DRM/KMS driver paired with upstream Mesa (Freedreno for Adreno, Panfrost for Mali).
- **Audio:** Native ALSA drivers coupled directly into PipeWire.
- **Modem & Connectivity:** Native Linux kernel drivers (e.g., `qmi_wwan`, `mhi`, `ipa`) managed via `ModemManager` and `NetworkManager`.
- **Sensors:** Linux IIO (Industrial I/O) subsystem mapped directly into desktop environment sensor daemons.
- **Firmware:** Openly distributable firmware packages sourced from upstream `linux-firmware` or authorized OEM repositories.

### Track B: Treble HAL Compatibility Bridge (Ecosystem Enablement)
For modern Android-compatible devices where proprietary vendor blobs are required to operate cellular modems, camera image signal processors (ISPs), audio DSPs, or biometric hardware:
- **Project Treble Isolation:** Project Treble partitions drivers into `/vendor` and `/odm` partitions, communicating over standardized interfaces (HIDL/AIDL HALs). H4ck3rMx preserves these untouched vendor partitions.
- **Sandboxed Driver Harness:** We utilize an isolated driver bridge (incorporating `libhybris` and minimal Bionic dynamic loader shims). This allows standard glibc/musl Linux applications and daemons to dynamically load and communicate with proprietary Bionic-compiled shared libraries (`.so`) inside restricted system namespaces.
- **Daemon Bridging:**
  - *Audio:* A PipeWire plugin routes audio streams to the Android Audio HAL (`audio.primary.*`).
  - *Cellular / Data:* A telemetry/RIL bridge translates Linux `ModemManager` or `oFono` commands to Qualcomm QMI/MBIM or vendor RIL interfaces.
  - *Graphics:* Wayland compositor links to EGL/GBM via libhybris wrapper if native DRM/KMS is unavailable.
  - *Camera:* Standard V4L2/libcamera interface layered above Android Camera HAL3.
- **Security Sandboxing:** The HAL bridge executes within dedicated, unprivileged SELinux/AppArmor domains and seccomp profiles, preventing proprietary vendor blobs from having unrestricted access to the Linux system.

---

## 4. Official Driver Sourcing & Ingestion Pipeline

To provide stable, production-grade hardware support as a non-profit, H4ck3rMx maintains an automated, transparent pipeline for tracking, extracting, and packaging drivers and firmware from official sources.

### Official Ingestion Sources
1. **Official OEM Kernel Source Releases (GPLv2):**
   - Device manufacturers (Google, OnePlus, Xiaomi, Motorola, Sony, Samsung, Fairphone) are legally required to publish kernel source code for every device update.
   - We track official OEM source repositories and mirror release tags.
   - Kernel trees are audited, stripped of proprietary tracker submodules, hardened with security patches, and compiled with clean toolchains (LLVM/Clang or GCC).

2. **Official OEM Factory Firmware and OTA Payloads:**
   - Official factory images, fastboot update packages, and OTA update files (`payload.bin`, `super.img`, `boot.img`).
   - Sourced directly from OEM content delivery networks and official developer portals (e.g., Google Developers Factory Images, OnePlus Software Updates, Xiaomi Fastboot ROMs).

3. **Chipset Vendor Upstream Repositories:**
   - Qualcomm Innovation Center (QuIC) / CodeLinaro trees.
   - Android Common Kernels (ACK) with Generic Kernel Image (GKI) trees.
   - Linaro mobile landing team trees.

4. **Public Redistributable Firmware:**
   - Upstream `linux-firmware` tree.
   - Sony Open Devices Project binaries and vendor resources.

### Automated Driver Ingestion Workflow
```
[Official OEM OTA / Factory Image]
               │
               ▼
   [Automated Ingestion Daemon]
   - Validates OEM cryptographic checksums & TLS provenance
   - Unpacks payload (payload_dumper / lpunpack / simg2img)
               │
               ▼
   [Component Categorization]
   ├── Kernel & DTBO  ──► Audited against OEM GPL source & recompiled
   ├── Vendor HALs    ──► Classified by interface (HIDL/AIDL) & hashed
   └── Raw Firmware   ──► Baseband, DSP, Wi-Fi, Bluetooth firmware
               │
               ▼
   [Cryptographic Manifest Generation]
   - Extracts hardware signatures (SoC ID, Board Rev, Sensor UUIDs)
   - Packages into H4ck3rMx Driver Package (.hdp)
   - Multi-party cosigned by release engineering keys
               │
               ▼
   [Public Driver Catalog & Local On-Device Provisioning]
```

---

## 5. Dynamic On-Device Hardware Provisioning & OTA Strategy

H4ck3rMx decouples core Linux OS updates from hardware-specific vendor driver updates.

### 1. Device Fingerprinting at Boot
During the initramfs phase, the system executes a minimal, hardened discovery agent:
- Reads device tree compatibility strings (`/proc/device-tree/compatible`).
- Reads hardware revisions from bootloader cmdline (`androidboot.hardware`, `androidboot.dtbo_idx`).
- Queries PCI, USB, I2C, and MIPI bus devices.
- Fingerprints modem baseband version and sensor configurations.

### 2. Deterministic Driver Matching
The discovery agent compares the hardware fingerprint against the **H4ck3rMx Driver Manifest Catalog**:
- If matching signed driver packages are pre-installed in the local recovery cache or `/vendor` partition, they are initialized immediately.
- If updates or missing firmware modules are detected, the system fetches signed driver deltas over pinned TLS.

### 3. Atomic Driver OTA Updates
- **A/B Partitioning:** Driver packages and kernel updates are applied to inactive slots (Slot A / Slot B) using standard Android partition layout conventions.
- **Rollback Protection:** If a newly applied driver package or kernel fails health probes (watchdog ping, display initialization, modem registration), the hardware watchdog triggers automatic fallback to the previous known-good slot.
- **Integrity Verification:** Every driver bundle is verified against our multi-party cosigned trust manifest before being unpacked or mounted.

---

## 6. Non-Profit Legal & Compliance Strategy

As a non-profit organization providing an open, secure mobile operating system, full legal and licensing compliance is a mandatory foundation.

### Licensing Matrix
- **H4ck3rMx Core Code & Tooling:** Released under the permissive **MIT License**.
- **Kernel & Linux Drivers:** Licensed under **GPLv2**. We publish complete, matching source code, configuration trees, and build scripts for every distributed kernel binary.
- **Userland Middleware & HAL Adaptations:** Licensed under Apache 2.0 / MIT / BSD / LGPL depending on upstream components.
- **Proprietary Vendor Microcode & Blobs:**
  - Proprietary blobs (e.g. modem DSP firmware, proprietary GPU firmware) are owned by OEMs and chipset manufacturers and generally cannot be redistributed without explicit licensing.
  - **The Clean-Room Delivery Strategy:**
    1. **Direct Partition Retention:** When flashing H4ck3rMx, the installer does not touch or overwrite the device's pre-existing, legally licensed `/vendor`, `/odm`, or firmware partitions. The device continues to use its original, factory-licensed hardware drivers.
    2. **User-Side Ingestion Tooling:** When driver updates are released by OEMs in official factory images, H4ck3rMx provides open-source, automated extraction tools that allow the user to fetch the update directly from the official OEM source. The tool verifies the OEM cryptographic signature, extracts the needed driver binaries locally, and applies them to the device.
    3. **Transparency & SBOM:** Every H4ck3rMx build publishes a complete Software Bill of Materials (SBOM) detailing every component, origin URL, license, and cryptographic digest.

---

## 7. Integration with the Hex Adjacency Trust Graph

The hardware driver layer is deeply integrated with H4ck3rMx's core security innovation: the **Hex Trust Architecture**:
- **Driver Manifests:** Every driver bundle (`.hdp`) includes a cryptographically signed `driver_manifest.json` declaring hardware targets, file hashes, and required system capabilities.
- **Multi-Party Cosigning:** Driver packages targeting the official distribution must achieve the threshold of 6 independent cosigners before they are accepted by the system updater.
- **Isolation of Driver Daemons:** Driver bridge daemons interfacing with vendor HALs are confined to maximum 6 declared IPC peers, preventing compromised or proprietary vendor code from accessing user data or arbitrary network endpoints.
