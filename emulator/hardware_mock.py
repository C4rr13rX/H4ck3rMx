"""
Hardware Peripheral & Sysfs/Proc Mock Engine for H4ck3rMx Mobile Emulator
Simulates hardware interfaces (proc, sysfs, dev nodes, modem) without kernel-level requirements.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from emulator.config import HardwareProfile


class MockHardwareEnvironment:
    """Creates and manages a virtual Android-compatible hardware environment on disk."""

    def __init__(self, root_dir: Path, profile: HardwareProfile):
        self.root_dir = Path(root_dir)
        self.profile = profile
        self.proc_dir = self.root_dir / "proc"
        self.sys_dir = self.root_dir / "sys"
        self.dev_dir = self.root_dir / "dev"
        self.vendor_dir = self.root_dir / "vendor"
        self.system_dir = self.root_dir / "system"
        self.data_dir = self.root_dir / "data"

    def initialize(self):
        """Builds virtual /proc, /sys, /dev, and partition trees."""
        self._create_directories()
        self._populate_proc()
        self._populate_sys()
        self._populate_dev()
        self._populate_vendor_stubs()

    def _iio_dirname(self) -> str:
        # Windows does not permit ':' in directory names
        return "iio_device0" if os.name == "nt" else "iio:device0"

    def _create_directories(self):
        dirs = [
            self.proc_dir / "device-tree",
            self.sys_dir / "class" / "power_supply" / "battery",
            self.sys_dir / "class" / "thermal" / "thermal_zone0",
            self.sys_dir / "bus" / "iio" / "devices" / self._iio_dirname(),
            self.sys_dir / "devices" / "soc0",
            self.dev_dir,
            self.vendor_dir / "lib64" / "hw",
            self.vendor_dir / "etc" / "vintf",
            self.system_dir,
            self.data_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _populate_proc(self):
        # /proc/cmdline
        (self.proc_dir / "cmdline").write_text(self.profile.cmdline_template + "\n", encoding="utf-8")

        # /proc/cpuinfo
        cpuinfo = f"""Processor\t: {self.profile.cpu_arch}
BogoMIPS\t: 38.40
Features\t: fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm lrcpc dcpop asimddp
CPU implementer\t: 0x51
CPU architecture: 8
CPU variant\t: 0x7
CPU part\t: 0x805
CPU revision\t: 14

Hardware\t: {self.profile.soc_vendor} {self.profile.soc_id}
Revision\t: 0000
Serial\t\t: H4CK3RMX00000001
"""
        (self.proc_dir / "cpuinfo").write_text(cpuinfo, encoding="utf-8")

        # /proc/device-tree/compatible
        (self.proc_dir / "device-tree" / "compatible").write_text(
            f"{self.profile.soc_id}\x00qcom,board-id\x00", encoding="utf-8"
        )

    def _populate_sys(self):
        # Battery mock: 85% capacity, discharging, 28.5 C, 4.15V
        bat_dir = self.sys_dir / "class" / "power_supply" / "battery"
        (bat_dir / "capacity").write_text("85\n", encoding="utf-8")
        (bat_dir / "status").write_text("Discharging\n", encoding="utf-8")
        (bat_dir / "temp").write_text("285\n", encoding="utf-8")  # 28.5 C
        (bat_dir / "voltage_now").write_text("4150000\n", encoding="utf-8")  # 4.15 V
        (bat_dir / "health").write_text("Good\n", encoding="utf-8")

        # Thermal mock: 34.0 C
        thermal_dir = self.sys_dir / "class" / "thermal" / "thermal_zone0"
        (thermal_dir / "temp").write_text("34000\n", encoding="utf-8")
        (thermal_dir / "type").write_text("cpu-thermal\n", encoding="utf-8")

        # Accelerometer mock
        iio_dir = self.sys_dir / "bus" / "iio" / "devices" / self._iio_dirname()
        (iio_dir / "name").write_text("accelerometer\n", encoding="utf-8")
        (iio_dir / "in_accel_x_raw").write_text("12\n", encoding="utf-8")
        (iio_dir / "in_accel_y_raw").write_text("-4\n", encoding="utf-8")
        (iio_dir / "in_accel_z_raw").write_text("981\n", encoding="utf-8")

        # SoC information
        soc_dir = self.sys_dir / "devices" / "soc0"
        (soc_dir / "family").write_text(f"{self.profile.soc_vendor}\n", encoding="utf-8")
        (soc_dir / "soc_id").write_text(f"{self.profile.soc_id}\n", encoding="utf-8")
        (soc_dir / "revision").write_text("v2.1\n", encoding="utf-8")

    def _populate_dev(self):
        # Create virtual character device stub placeholders
        dev_nodes = ["binder", "hwbinder", "vndbinder", "ion", "dma_heap", "modem_at0"]
        for node in dev_nodes:
            f = self.dev_dir / node
            if not f.exists():
                f.write_text(f"[MOCK_DEV_NODE:{node}]\n", encoding="utf-8")

    def _populate_vendor_stubs(self):
        # VINTF manifest stub declaring HAL interfaces
        manifest_xml = f"""<manifest version="2.0" type="device">
    <hal format="hidl">
        <name>android.hardware.audio</name>
        <transport>hwbinder</transport>
        <version>6.0</version>
        <interface>
            <name>IDevicesFactory</name>
            <instance>default</instance>
        </interface>
    </hal>
    <hal format="hidl">
        <name>android.hardware.radio</name>
        <transport>hwbinder</transport>
        <version>1.5</version>
        <interface>
            <name>IRadio</name>
            <instance>slot1</instance>
        </interface>
    </hal>
    <hal format="hidl">
        <name>android.hardware.graphics.composer</name>
        <transport>hwbinder</transport>
        <version>2.4</version>
        <interface>
            <name>IComposer</name>
            <instance>default</instance>
        </interface>
    </hal>
</manifest>
"""
        (self.vendor_dir / "etc" / "vintf" / "manifest.xml").write_text(manifest_xml, encoding="utf-8")

        # Vendor HAL shared library stubs (mocked metadata)
        hal_libs = [
            "audio.primary.default.so",
            "gralloc.default.so",
            "camera.device@3.5-impl.so",
            "gatekeeper.default.so",
        ]
        for lib in hal_libs:
            (self.vendor_dir / "lib64" / "hw" / lib).write_text(f"# STUB_ELF64_{lib}\n", encoding="utf-8")

    def query_battery(self) -> Dict[str, Any]:
        bat_dir = self.sys_dir / "class" / "power_supply" / "battery"
        return {
            "capacity": int((bat_dir / "capacity").read_text().strip()),
            "status": (bat_dir / "status").read_text().strip(),
            "temp_c": int((bat_dir / "temp").read_text().strip()) / 10.0,
            "voltage_v": int((bat_dir / "voltage_now").read_text().strip()) / 1000000.0,
        }

    def query_thermal(self) -> float:
        thermal_dir = self.sys_dir / "class" / "thermal" / "thermal_zone0"
        return int((thermal_dir / "temp").read_text().strip()) / 1000.0

    def query_accel(self) -> Dict[str, int]:
        iio_dir = self.sys_dir / "bus" / "iio" / "devices" / self._iio_dirname()
        return {
            "x": int((iio_dir / "in_accel_x_raw").read_text().strip()),
            "y": int((iio_dir / "in_accel_y_raw").read_text().strip()),
            "z": int((iio_dir / "in_accel_z_raw").read_text().strip()),
        }

    def simulate_modem_at(self, command: str) -> str:
        """Simulates AT command responses from the mobile baseband modem."""
        cmd = command.strip().upper()
        if cmd == "AT":
            return "OK\r\n"
        elif cmd == "AT+CSQ":
            # Signal quality: rssi 28 (excellent), ber 0
            return "+CSQ: 28,0\r\nOK\r\n"
        elif cmd == "AT+COPS?":
            # Current operator
            return '+COPS: 0,0,"H4ck3rMx Sovereign Cellular",7\r\nOK\r\n'
        elif cmd == "AT+CGATT?":
            # GPRS/LTE/5G Packet Domain Attached
            return "+CGATT: 1\r\nOK\r\n"
        elif cmd == "AT+CGMR":
            # Revision identification (baseband version)
            return f"{self.profile.modem_model} REV_2.4.19\r\nOK\r\n"
        elif cmd.startswith("AT+CGDCONT?"):
            # PDP Context
            return '+CGDCONT: 1,"IPV4V6","sovereign.mesh.net","0.0.0.0",0,0\r\nOK\r\n'
        else:
            return "ERROR\r\n"
