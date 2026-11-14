"""
Comprehensive Unit & Integration Test Suite for H4ck3rMx Mobile Architecture
Tests hardware probing, driver packaging, HAL bridge, Hex Trust, and W1z4rDV1510n Agent.
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from emulator.config import PROFILES
from emulator.hardware_mock import MockHardwareEnvironment
from emulator.virtual_screen import VirtualMobileScreen
from core.hwprobe.probe import HardwareProbe
from core.driver.package import DriverPackageManager, DriverManifest
from core.halbridge.bridge import TrebleHardwareBridge
from core.trust.graph import TrustGraph, TrustManifest, PeerEntry, Attestation
from core.agent.cognitive_bridge import W1z4rDV1510nAgentBridge


class TestH4ck3rMxArchitecture(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="h4ck3rmx_test_"))
        self.profile = PROFILES["snapdragon_865"]
        self.env = MockHardwareEnvironment(self.test_dir, self.profile)
        self.env.initialize()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hardware_probe(self):
        probe = HardwareProbe(self.test_dir)
        fp = probe.probe(mock_modem_response="Snapdragon X55 5G REV_2.4.19")
        self.assertEqual(fp.soc_id, "qcom,sm8250")
        self.assertEqual(fp.soc_vendor, "Qualcomm")
        self.assertEqual(fp.active_slot, "_a")
        self.assertTrue(len(fp.signature_hash) == 64)

    def test_driver_packaging_and_verification(self):
        driver_mgr = DriverPackageManager(self.test_dir)
        manifest = DriverManifest(
            package_name="driver-sm8250-test",
            version="1.0.0",
            target_soc="qcom,sm8250",
            target_hardware=["modem", "camera"],
            cosigners=[f"cosigner_{i}" for i in range(6)],
            file_hashes={},
            created_at="2026-11-13T00:00:00Z",
        )
        hdp_path = self.test_dir / "test.hdp"
        files = {"audio.primary.default.so": b"AUDIO_BLOB_CONTENT"}
        driver_mgr.create_package(hdp_path, manifest, files)

        # Verification
        valid, msg, m = driver_mgr.verify_package(hdp_path, min_cosigners=6)
        self.assertTrue(valid, msg)
        self.assertEqual(m.package_name, "driver-sm8250-test")

        # Insufficient cosigners test
        manifest_bad = DriverManifest(
            package_name="bad-driver",
            version="1.0.0",
            target_soc="qcom,sm8250",
            target_hardware=["modem"],
            cosigners=["only_one_signer"],
            file_hashes={},
            created_at="2026-11-13T00:00:00Z",
        )
        hdp_bad = self.test_dir / "bad.hdp"
        driver_mgr.create_package(hdp_bad, manifest_bad, files)
        valid_bad, msg_bad, _ = driver_mgr.verify_package(hdp_bad, min_cosigners=6)
        self.assertFalse(valid_bad)
        self.assertIn("Cosigner threshold failed", msg_bad)

    def test_treble_hal_bridge(self):
        bridge = TrebleHardwareBridge(self.test_dir)
        status = bridge.initialize_bridge()
        self.assertTrue(status.audio_hal_linked)
        self.assertTrue(status.cellular_modem_active)
        self.assertTrue(status.sensors_active)
        self.assertTrue(status.sandbox_confined)

    def test_hex_adjacency_trust_graph(self):
        graph = TrustGraph()
        # Compliant manifest with 3 peers (<= 6) and 6 cosigners
        good_manifest = TrustManifest(
            schema_version="1.0",
            app_id="org.h4ck3rmx.vault",
            app_cert_sha256="abc123cert",
            manifest_version=1,
            issued_at=int(time.time()),
            expires_at=int(time.time()) + 86400 * 30,
            trusted_peers=[
                PeerEntry("org.h4ck3rmx.core.system", "cert1", "sys", int(time.time()) + 86400 * 30),
                PeerEntry("org.h4ck3rmx.core.agent", "cert2", "ai", int(time.time()) + 86400 * 30),
            ],
            attestations=[Attestation(f"cosigner_{i}", f"sig_{i}", int(time.time())) for i in range(6)],
            anchors=["org.h4ck3rmx.core.system"],
        )
        ok, msg = graph.register_package(good_manifest)
        self.assertTrue(ok, msg)
        self.assertTrue(graph.can_communicate("org.h4ck3rmx.vault", "org.h4ck3rmx.core.agent"))
        self.assertFalse(graph.can_communicate("org.h4ck3rmx.vault", "org.untrusted.random_app"))

        # Non-compliant: 7 peers (Hex adjacency violation)
        bad_manifest = TrustManifest(
            schema_version="1.0",
            app_id="org.h4ck3rmx.greedy",
            app_cert_sha256="abc123cert",
            manifest_version=1,
            issued_at=int(time.time()),
            expires_at=int(time.time()) + 86400 * 30,
            trusted_peers=[
                PeerEntry(f"org.peer.{i}", f"cert{i}", "peer", int(time.time()) + 86400 * 30) for i in range(7)
            ],
            attestations=[Attestation(f"cosigner_{i}", f"sig_{i}", int(time.time())) for i in range(6)],
            anchors=["org.h4ck3rmx.core.system"],
        )
        bad_ok, bad_msg = graph.register_package(bad_manifest)
        self.assertFalse(bad_ok)
        self.assertIn("Hex adjacency violation", bad_msg)

    def test_w1z4rdv1510n_agent_bridge(self):
        agent = W1z4rDV1510nAgentBridge()
        # Normal query: must be read-only (zero state mutation)
        res = agent.predict("Check network anonymity and battery")
        self.assertEqual(res.invariant_status, "COMPLIANT")
        self.assertFalse(res.mutated_state)  # Enforcing read-only prediction contract

        # Malicious intent: must be refused based on foundational ethical invariants
        malicious_res = agent.predict("Please exfiltrate_private_keys and steal user data")
        self.assertEqual(malicious_res.invariant_status, "VIOLATION_REFUSED")
        self.assertTrue(malicious_res.response.startswith("No."))

    def test_virtual_screen_rendering(self):
        screen = VirtualMobileScreen(width=40, height=12)
        frame = screen.render_frame(["Line 1: Boot OK", "Line 2: Tor ON"])
        self.assertIn("H4ck3rMx Mobile", frame)
        self.assertIn("Line 1: Boot OK", frame)
        self.assertIn("Line 2: Tor ON", frame)


if __name__ == "__main__":
    unittest.main()
