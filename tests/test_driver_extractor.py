"""
Unit tests for H4ck3rMx Driver Extractor and .HDP Packager.
"""

import tempfile
import unittest
from pathlib import Path
from emulator.config import PROFILES
from emulator.hardware_mock import MockHardwareEnvironment
from scripts.extract_official_drivers import build_hdp_package, inspect_binary_elf, categorize_driver_file


class TestDriverExtractor(unittest.TestCase):
    def test_inspect_elf(self):
        # Construct minimal ELF 64-bit ARM header
        elf_data = bytearray(64)
        elf_data[0:4] = b"\x7fELF"
        elf_data[4] = 2  # 64-bit
        elf_data[5] = 1  # Little endian
        elf_data[18:20] = b"\xb7\x00"  # AArch64 (0x00B7 in little endian)

        info = inspect_binary_elf(bytes(elf_data))
        self.assertTrue(info["is_elf"])
        self.assertEqual(info["bitness"], "64-bit")
        self.assertEqual(info["arch"], "AArch64 (ARM64)")

    def test_categorize_driver_file(self):
        self.assertEqual(categorize_driver_file("audio.primary.default.so"), "audio")
        self.assertEqual(categorize_driver_file("camera.device@3.5.so"), "camera")
        self.assertEqual(categorize_driver_file("sensors.ssc.so"), "sensors")
        self.assertEqual(categorize_driver_file("vulkan.adreno.so"), "display_gpu")
        self.assertEqual(categorize_driver_file("modem.mbn"), "modem_dsp_firmware")

    def test_end_to_end_packaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = MockHardwareEnvironment(root, PROFILES["snapdragon_865"])
            env.initialize()

            out_hdp = root / "drivers" / "qcom_sm8250.hdp"
            hdp_result = build_hdp_package(
                source_dir=env.vendor_dir,
                output_path=out_hdp,
                target_soc="sm8250",
                package_name="h4ck3rmx-driver-sm8250",
                version="1.0.0",
            )
            self.assertTrue(hdp_result.exists())
            self.assertGreater(hdp_result.stat().st_size, 500)


if __name__ == "__main__":
    unittest.main()
