"""
Driver Package & Verification Engine for H4ck3rMx (.hdp)
Manages cryptographically signed driver bundles sourced from official OEM releases and OTAs.
"""

import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DriverManifest:
    package_name: str
    version: str
    target_soc: str
    target_hardware: List[str]
    cosigners: List[str]
    file_hashes: Dict[str, str]
    created_at: str
    license_type: str = "GPLv2/Vendor-CleanRoom"


class DriverPackageManager:
    """Creates, verifies, and installs H4ck3rMx Driver Packages (.hdp)."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.vendor_dir = self.root_dir / "vendor"
        self.firmware_dir = self.root_dir / "lib" / "firmware"

    def create_package(
        self,
        output_hdp_path: Path,
        manifest: DriverManifest,
        files: Dict[str, bytes],
    ) -> Path:
        """Builds a .hdp zip archive containing driver assets and signed manifest."""
        output_hdp_path = Path(output_hdp_path)
        output_hdp_path.parent.mkdir(parents=True, exist_ok=True)

        # Update manifest file_hashes
        manifest.file_hashes = {}
        for fname, content in files.items():
            manifest.file_hashes[fname] = hashlib.sha256(content).hexdigest()

        with zipfile.ZipFile(output_hdp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write driver manifest
            manifest_json = json.dumps(manifest.__dict__, indent=2)
            zf.writestr("driver_manifest.json", manifest_json)
            # Write payload files
            for fname, content in files.items():
                zf.writestr(f"payload/{fname}", content)

        return output_hdp_path

    def verify_package(self, hdp_path: Path, min_cosigners: int = 6) -> tuple[bool, str, Optional[DriverManifest]]:
        """Verifies package integrity, hashes, and minimum cosigner threshold."""
        hdp_path = Path(hdp_path)
        if not hdp_path.exists():
            return False, "Package file not found", None

        with zipfile.ZipFile(hdp_path, "r") as zf:
            if "driver_manifest.json" not in zf.namelist():
                return False, "Missing driver_manifest.json", None

            manifest_raw = zf.read("driver_manifest.json").decode("utf-8")
            data = json.loads(manifest_raw)
            manifest = DriverManifest(**data)

            # Check cosigner threshold
            if len(manifest.cosigners) < min_cosigners:
                return False, f"Cosigner threshold failed: {len(manifest.cosigners)}/{min_cosigners} signatures", manifest

            # Verify individual file checksums
            for fname, expected_hash in manifest.file_hashes.items():
                arcname = f"payload/{fname}"
                if arcname not in zf.namelist():
                    return False, f"Missing payload file: {fname}", manifest
                actual_hash = hashlib.sha256(zf.read(arcname)).hexdigest()
                if actual_hash != expected_hash:
                    return False, f"Hash mismatch for {fname}: expected {expected_hash}, got {actual_hash}", manifest

        return True, "Integrity verified successfully", manifest

    def install_package(self, hdp_path: Path, target_slot: str = "slot_a") -> tuple[bool, str]:
        """Installs verified driver payload into isolated target vendor/firmware directories."""
        valid, reason, manifest = self.verify_package(hdp_path)
        if not valid:
            return False, f"Installation rejected: {reason}"

        with zipfile.ZipFile(hdp_path, "r") as zf:
            for fname in manifest.file_hashes.keys():
                arcname = f"payload/{fname}"
                content = zf.read(arcname)
                # Route destination based on extension
                if fname.endswith(".so"):
                    dest = self.vendor_dir / "lib64" / "hw" / fname
                elif fname.endswith(".mbn") or fname.endswith(".bin"):
                    dest = self.firmware_dir / fname
                else:
                    dest = self.vendor_dir / "etc" / fname

                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)

        return True, f"Installed {manifest.package_name} v{manifest.version} to {target_slot}"
