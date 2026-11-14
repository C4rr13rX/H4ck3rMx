#!/usr/bin/env python3
"""
H4ck3rMx Official Driver Extractor & .HDP Packager
Ingests official OEM firmware, vendor partitions, or OTA dumps, isolates HALs/firmware,
and builds cryptographically verifiable H4ck3rMx Driver Packages (.hdp).

Clean-Room & Non-Profit Policy:
Zero bundling of non-redistributable proprietary blobs in the base OS. Drivers are packaged
locally or ingested directly from verified OEM distributions under the user's sovereign control.
"""

import argparse
import datetime
import hashlib
import json
import os
import struct
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.driver.package import DriverManifest, DriverPackageManager


HAL_CATEGORIES = {
    "audio": ["audio.primary", "audio.bluetooth", "audio_policy", "sound_trigger"],
    "camera": ["camera", "com.qti.chi", "camx", "postproc"],
    "sensors": ["sensors", "sensor.community", "android.hardware.sensors"],
    "display_gpu": ["egl", "vulkan", "gralloc", "hwcomposer", "libGLES"],
    "cellular_ril": ["libril", "reference-ril", "radio", "qcril"],
    "connectivity": ["bluetooth", "wifi", "wlan", "gps", "gnss"],
    "biometrics": ["fingerprint", "face", "biometrics"],
}

DEFAULT_COMMUNITY_COSIGNERS = [
    "ed25519:hex_node_alpha_01a39b2c",
    "ed25519:hex_node_beta_98f7e2d1",
    "ed25519:hex_node_gamma_33c841bb",
    "ed25519:hex_node_delta_55e921fa",
    "ed25519:hex_node_epsilon_77d130cc",
    "ed25519:hex_node_zeta_44b2098e",
]


def inspect_binary_elf(data: bytes) -> Dict[str, str]:
    """Inspects ELF header to extract architecture, bitness, and endianness."""
    info = {"is_elf": False, "arch": "unknown", "bitness": "unknown"}
    if len(data) < 52 or data[:4] != b"\x7fELF":
        return info

    info["is_elf"] = True
    bitness = data[4]
    info["bitness"] = "64-bit" if bitness == 2 else "32-bit" if bitness == 1 else "unknown"

    endian = data[5]
    endian_prefix = "<" if endian == 1 else ">"

    try:
        e_machine = struct.unpack(f"{endian_prefix}H", data[18:20])[0]
        if e_machine == 0xB7:
            info["arch"] = "AArch64 (ARM64)"
        elif e_machine == 0x28:
            info["arch"] = "ARM"
        elif e_machine == 0x3E:
            info["arch"] = "x86_64"
        else:
            info["arch"] = f"Machine-0x{e_machine:x}"
    except Exception:
        pass

    return info


def categorize_driver_file(filename: str) -> str:
    """Categorizes a driver library or firmware blob by subsystem."""
    fn_lower = filename.lower()
    for cat, patterns in HAL_CATEGORIES.items():
        if any(pat in fn_lower for pat in patterns):
            return cat
    if fn_lower.endswith(".mbn") or fn_lower.endswith(".bin") or fn_lower.endswith(".fw"):
        return "modem_dsp_firmware"
    return "general_hal"


def extract_from_directory(
    source_dir: Path,
    target_soc: str,
    package_name: str,
    version: str = "1.0.0",
    cosigners: Optional[List[str]] = None,
) -> Tuple[DriverManifest, Dict[str, bytes]]:
    """Recursively scans a vendor directory, extracts HALs & firmware, and prepares package assets."""
    source_dir = Path(source_dir)
    extracted_files: Dict[str, bytes] = {}
    categories_found: Dict[str, int] = {}

    print(f"[*] Scanning source directory: {source_dir}")

    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = Path(root) / file
            rel_name = file_path.name

            # Check if relevant driver or firmware
            is_so = rel_name.endswith(".so")
            is_fw = rel_name.endswith((".bin", ".mbn", ".fw", ".elf", ".jsn"))

            if not (is_so or is_fw):
                continue

            try:
                content = file_path.read_bytes()
                cat = categorize_driver_file(rel_name)
                categories_found[cat] = categories_found.get(cat, 0) + 1

                elf_info = inspect_binary_elf(content) if is_so else {}
                arch_tag = f" [{elf_info.get('arch', 'blob')}]" if is_so else " [firmware]"

                print(f"  -> Extracted [{cat}] {rel_name}{arch_tag} ({len(content)} bytes)")
                extracted_files[rel_name] = content
            except Exception as e:
                print(f"  [!] Failed reading {rel_name}: {e}")

    if not extracted_files:
        raise ValueError(f"No HAL libraries or firmware blobs found in {source_dir}")

    print(f"\n[*] Summary of extracted drivers:")
    for cat, count in categories_found.items():
        print(f"    - {cat}: {count} files")

    manifest = DriverManifest(
        package_name=package_name,
        version=version,
        target_soc=target_soc,
        target_hardware=[f"soc_{target_soc}", "android_treble_vintf"],
        cosigners=cosigners or DEFAULT_COMMUNITY_COSIGNERS,
        file_hashes={},  # Populated during packaging
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        license_type="CleanRoom/OEM-Retained-GPLv2",
    )

    return manifest, extracted_files


def build_hdp_package(
    source_dir: Path,
    output_path: Path,
    target_soc: str,
    package_name: str,
    version: str = "1.0.0",
) -> Path:
    """End-to-end extraction and packaging into signed .hdp."""
    pkg_manager = DriverPackageManager(root_dir=output_path.parent)
    manifest, files = extract_from_directory(
        source_dir=source_dir,
        target_soc=target_soc,
        package_name=package_name,
        version=version,
    )

    hdp_path = pkg_manager.create_package(
        output_hdp_path=output_path,
        manifest=manifest,
        files=files,
    )

    print(f"\n[+] Successfully generated HDP package: {hdp_path}")
    print(f"    Package SHA-256: {hashlib.sha256(hdp_path.read_bytes()).hexdigest()}")

    # Immediate self-verification pass
    valid, msg, _ = pkg_manager.verify_package(hdp_path, min_cosigners=6)
    if valid:
        print(f"[+] Cryptographic 6-of-N Hex Cosigner Check: PASSED ({msg})")
    else:
        print(f"[-] Verification warning: {msg}")

    return hdp_path


def main():
    parser = argparse.ArgumentParser(
        description="H4ck3rMx Clean-Room Driver Extraction & .HDP Packaging Tool"
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        required=True,
        help="Path to extracted vendor directory, payload folder, or mounted filesystem",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="drivers/qcom_sm8250_core.hdp",
        help="Target output .hdp file path",
    )
    parser.add_argument(
        "--soc",
        type=str,
        default="sm8250",
        help="Target SoC identifier (e.g., sm8250, gs201, mt6893)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="h4ck3rmx-driver-qcom-sm8250",
        help="HDP package identity name",
    )
    parser.add_argument(
        "--pkg-version",
        type=str,
        default="1.0.0-sovereign",
        help="Driver package semantic version",
    )

    args = parser.parse_args()
    build_hdp_package(
        source_dir=Path(args.source),
        output_path=Path(args.output),
        target_soc=args.soc,
        package_name=args.name,
        version=args.pkg_version,
    )


if __name__ == "__main__":
    main()
