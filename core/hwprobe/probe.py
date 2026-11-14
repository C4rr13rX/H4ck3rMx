"""
Hardware Discovery & Fingerprinting Engine for H4ck3rMx
Scans bootloader cmdline, device-tree, sysfs, and hardware buses to construct a
cryptographic hardware signature and query matching official driver packages.
"""

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class HardwareFingerprint:
    soc_id: str
    soc_vendor: str
    board_sku: str
    boot_device: str
    active_slot: str
    serial_no: str
    modem_baseband: str
    battery_health: str
    thermal_temp_c: float
    signature_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.soc_id}|{self.soc_vendor}|{self.board_sku}|{self.boot_device}|{self.modem_baseband}"
        self.signature_hash = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return self.signature_hash


class HardwareProbe:
    """Probes the physical or emulated Linux environment on Android-compatible hardware."""

    def __init__(self, root_dir: Path = Path("/")):
        self.root_dir = Path(root_dir)
        self.proc_dir = self.root_dir / "proc"
        self.sys_dir = self.root_dir / "sys"

    def probe(self, mock_modem_response: Optional[str] = None) -> HardwareFingerprint:
        soc_id = self._read_soc_id()
        soc_vendor = self._read_soc_vendor()
        cmdline_props = self._parse_cmdline()
        battery_data = self._probe_battery()
        thermal_c = self._probe_thermal()
        baseband = mock_modem_response or "Generic Qualcomm Baseband"

        fp = HardwareFingerprint(
            soc_id=soc_id,
            soc_vendor=soc_vendor,
            board_sku=cmdline_props.get("ro.boot.hardware.sku", cmdline_props.get("androidboot.hardware", "unknown")),
            boot_device=cmdline_props.get("androidboot.bootdevice", "mmcblk0"),
            active_slot=cmdline_props.get("androidboot.slot_suffix", "_a"),
            serial_no=cmdline_props.get("androidboot.serialno", "SOVEREIGN_NODE_0"),
            modem_baseband=baseband,
            battery_health=battery_data.get("status", "Normal"),
            thermal_temp_c=thermal_c,
        )
        fp.compute_hash()
        return fp

    def _read_soc_id(self) -> str:
        # Check /proc/device-tree/compatible first
        dt_compat = self.proc_dir / "device-tree" / "compatible"
        if dt_compat.exists():
            try:
                raw = dt_compat.read_bytes().decode("utf-8", errors="ignore")
                return raw.split("\x00")[0]
            except Exception:
                pass
        # Fallback to /sys/devices/soc0/soc_id
        soc_f = self.sys_dir / "devices" / "soc0" / "soc_id"
        if soc_f.exists():
            return soc_f.read_text().strip()
        return "generic,arm64"

    def _read_soc_vendor(self) -> str:
        soc_fam = self.sys_dir / "devices" / "soc0" / "family"
        if soc_fam.exists():
            return soc_fam.read_text().strip()
        return "UnknownVendor"

    def _parse_cmdline(self) -> Dict[str, str]:
        props = {}
        cmdline_f = self.proc_dir / "cmdline"
        if cmdline_f.exists():
            text = cmdline_f.read_text(encoding="utf-8", errors="ignore")
            for token in text.strip().split():
                if "=" in token:
                    k, v = token.split("=", 1)
                    props[k] = v
        return props

    def _probe_battery(self) -> Dict[str, Any]:
        bat_dir = self.sys_dir / "class" / "power_supply" / "battery"
        if bat_dir.exists():
            cap = (bat_dir / "capacity").read_text().strip() if (bat_dir / "capacity").exists() else "100"
            status = (bat_dir / "status").read_text().strip() if (bat_dir / "status").exists() else "Discharging"
            return {"capacity": cap, "status": status}
        return {"capacity": "100", "status": "AC_Connected"}

    def _probe_thermal(self) -> float:
        th_f = self.sys_dir / "class" / "thermal" / "thermal_zone0" / "temp"
        if th_f.exists():
            try:
                return int(th_f.read_text().strip()) / 1000.0
            except Exception:
                return 30.0
        return 30.0
