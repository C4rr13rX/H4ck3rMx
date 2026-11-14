"""
Device Hardware Profiles for H4ck3rMx Lightweight Mobile Emulator
Simulates physical Android-compatible hardware platforms (Qualcomm Snapdragon, Google Tensor, MediaTek Dimensity)
without requiring heavy GPU virtualization or slow CPU shader emulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HardwareProfile:
    name: str
    soc_id: str
    soc_vendor: str
    cpu_arch: str
    cores: int
    ram_mb: int
    storage_gb: int
    modem_model: str
    camera_sensor: str
    display_resolution: tuple
    cmdline_template: str
    partitions: List[str] = field(default_factory=lambda: ["system", "vendor", "odm", "boot_a", "boot_b", "data"])
    hal_interfaces: Dict[str, str] = field(default_factory=dict)


# Official Hardware Profiles
PROFILES: Dict[str, HardwareProfile] = {
    "snapdragon_865": HardwareProfile(
        name="Qualcomm Snapdragon 865 (SM8250 Reference)",
        soc_id="qcom,sm8250",
        soc_vendor="Qualcomm",
        cpu_arch="aarch64",
        cores=8,
        ram_mb=8192,
        storage_gb=128,
        modem_model="Snapdragon X55 5G (SM8250)",
        camera_sensor="Sony IMX689 48MP ISP",
        display_resolution=(1080, 2400),
        cmdline_template=(
            "console=ttyMSM0,115200 androidboot.hardware=qcom "
            "androidboot.bootdevice=1d84000.ufshc androidboot.slot_suffix=_a "
            "androidboot.serialno=H4CK3RMX-QCOM-8250 androidboot.dtbo_idx=0 "
            "ro.boot.hardware.sku=GLOBAL"
        ),
        hal_interfaces={
            "audio": "android.hardware.audio@6.0::IDevicesFactory",
            "cellular": "android.hardware.radio@1.5::IRadio",
            "graphics": "android.hardware.graphics.composer@2.4::IComposer",
            "camera": "android.hardware.camera.provider@2.5::ICameraProvider",
            "sensors": "android.hardware.sensors@2.0::ISensors",
        },
    ),
    "tensor_g2": HardwareProfile(
        name="Google Tensor G2 (GS201 Reference)",
        soc_id="google,gs201",
        soc_vendor="Google/Samsung",
        cpu_arch="aarch64",
        cores=8,
        ram_mb=12288,
        storage_gb=256,
        modem_model="Shannon 5123b (Exynos Modem)",
        camera_sensor="Samsung GN1 50MP",
        display_resolution=(1440, 3120),
        cmdline_template=(
            "console=ttySAC0,115200 androidboot.hardware=gs201 "
            "androidboot.bootdevice=14700000.ufs androidboot.slot_suffix=_a "
            "androidboot.serialno=H4CK3RMX-TENSOR-G2 androidboot.dtbo_idx=1 "
            "ro.boot.hardware.sku=PRO"
        ),
        hal_interfaces={
            "audio": "android.hardware.audio@7.0::IDevicesFactory",
            "cellular": "android.hardware.radio@1.6::IRadio",
            "graphics": "android.hardware.graphics.composer@2.4::IComposer",
            "camera": "android.hardware.camera.provider@2.6::ICameraProvider",
            "sensors": "android.hardware.sensors@2.1::ISensors",
        },
    ),
    "generic_arm64_mobile": HardwareProfile(
        name="Generic Android-Compatible ARM64 Mobile Target",
        soc_id="generic,arm64",
        soc_vendor="Generic",
        cpu_arch="aarch64",
        cores=4,
        ram_mb=4096,
        storage_gb=64,
        modem_model="Generic LTE/5G Baseband",
        camera_sensor="Generic V4L2/HAL3 Sensor",
        display_resolution=(720, 1600),
        cmdline_template=(
            "console=ttyAMA0,115200 androidboot.hardware=generic_arm64 "
            "androidboot.slot_suffix=_a androidboot.serialno=H4CK3RMX-GEN-001"
        ),
        hal_interfaces={
            "audio": "android.hardware.audio@5.0::IDevicesFactory",
            "cellular": "android.hardware.radio@1.4::IRadio",
            "graphics": "android.hardware.graphics.composer@2.1::IComposer",
            "camera": "android.hardware.camera.provider@2.4::ICameraProvider",
            "sensors": "android.hardware.sensors@1.0::ISensors",
        },
    ),
}
