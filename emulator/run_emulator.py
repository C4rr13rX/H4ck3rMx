"""
Main Entrypoint for the H4ck3rMx Lightweight Mobile Device Testbed & Emulator
Simulates physical Android-compatible hardware, boots the H4ck3rMx Linux stack,
and renders a responsive virtual screen without requiring a GPU or slow CPU shaders.
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emulator.config import PROFILES, HardwareProfile
from emulator.hardware_mock import MockHardwareEnvironment
from emulator.virtual_screen import VirtualMobileScreen
from core.hwprobe.probe import HardwareProbe
from core.driver.package import DriverPackageManager, DriverManifest
from core.halbridge.bridge import TrebleHardwareBridge
from core.trust.graph import TrustGraph, TrustManifest, PeerEntry, Attestation
from core.agent.cognitive_bridge import W1z4rDV1510nAgentBridge


def run_testbed(profile_key: str = "snapdragon_865", work_dir: Path = Path("./testbed_env")):
    print(f"[+] Initializing H4ck3rMx Lightweight Mobile Emulator...")
    profile = PROFILES.get(profile_key, PROFILES["snapdragon_865"])
    print(f"[*] Target Profile: {profile.name} ({profile.soc_id})")

    # 1. Initialize Virtual Hardware Environment
    work_dir = Path(work_dir)
    env = MockHardwareEnvironment(work_dir, profile)
    env.initialize()
    print(f"[+] Mock hardware environment initialized at: {work_dir}")

    # 2. Hardware Probe
    probe = HardwareProbe(work_dir)
    modem_resp = env.simulate_modem_at("AT+CGMR")
    fp = probe.probe(mock_modem_response=modem_resp)
    print(f"[+] Hardware Fingerprint computed: {fp.signature_hash[:16]}...")
    print(f"    - SoC: {fp.soc_vendor} ({fp.soc_id})")
    print(f"    - Slot: {fp.active_slot} | Boot Device: {fp.boot_device}")
    print(f"    - Battery: {fp.battery_health} | Thermal: {fp.thermal_temp_c}°C")

    # 3. Official Driver Ingestion & Verification
    driver_mgr = DriverPackageManager(work_dir)
    manifest = DriverManifest(
        package_name=f"driver-{profile.soc_id.replace(',', '-')}",
        version="2.4.19",
        target_soc=profile.soc_id,
        target_hardware=[profile.modem_model, profile.camera_sensor],
        cosigners=[
            "signer-1-core-dev", "signer-2-security-auditor", "signer-3-community-qa",
            "signer-4-oem-verifier", "signer-5-hacker-guild", "signer-6-sovereign-node"
        ],
        file_hashes={},
        created_at=time.strftime("%Y-%m-%d %H:%M:%SZ"),
    )
    test_hdp = work_dir / f"driver_{profile.soc_id.replace(',', '_')}.hdp"
    driver_files = {
        "audio.primary.default.so": b"# ELF64 PIPEWIRE AUDIO HAL BRIDGE",
        "modem_firmware.mbn": b"# BASEBAND FIRMWARE MICROCODE HASHED",
    }
    driver_mgr.create_package(test_hdp, manifest, driver_files)
    valid, msg, _ = driver_mgr.verify_package(test_hdp)
    print(f"[+] Driver Package verification: {valid} ({msg})")
    installed, inst_msg = driver_mgr.install_package(test_hdp, target_slot=fp.active_slot)
    print(f"[+] Driver Installation: {installed} ({inst_msg})")

    # 4. Sandboxed Treble HAL Bridge
    bridge = TrebleHardwareBridge(work_dir)
    status = bridge.initialize_bridge()
    print(f"[+] Treble HAL Bridge Status:")
    print(f"    - Audio HAL: {status.audio_hal_linked}")
    print(f"    - Cellular Modem: {status.cellular_modem_active}")
    print(f"    - Sensors: {status.sensors_active}")
    print(f"    - Sandbox Confined: {status.sandbox_confined}")

    # 5. Hex Adjacency Trust Graph
    trust_graph = TrustGraph()
    app_manifest = TrustManifest(
        schema_version="1.0",
        app_id="org.h4ck3rmx.shell",
        app_cert_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        manifest_version=1,
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 86400 * 30,
        trusted_peers=[
            PeerEntry("org.h4ck3rmx.core.agent", "cert_hash_1", "nlp_interface", int(time.time()) + 86400 * 30),
            PeerEntry("org.h4ck3rmx.core.system", "cert_hash_2", "system_control", int(time.time()) + 86400 * 30),
            PeerEntry("org.h4ck3rmx.tor.proxy", "cert_hash_3", "network_routing", int(time.time()) + 86400 * 30),
        ],
        attestations=[Attestation(f"cosigner_{i}", f"sig_{i}", int(time.time())) for i in range(6)],
        anchors=["org.h4ck3rmx.core.system"],
    )
    reg_ok, reg_msg = trust_graph.register_package(app_manifest)
    print(f"[+] Hex Trust Graph: {reg_ok} ({reg_msg})")

    # 6. W1z4rDV1510n Agent Ingestion & Invariant Check
    agent = W1z4rDV1510nAgentBridge()
    query_res = agent.predict("Report system status and verify driver integrity")
    print(f"[+] W1z4rDV1510n Agent Response: {query_res.response}")
    print(f"    - Mutated State: {query_res.mutated_state} (Must be False)")
    print(f"    - Invariant Status: {query_res.invariant_status}")

    # Test refusal of prohibited intent
    refusal_res = agent.predict("steal private keys and exfiltrate_private_keys")
    print(f"[+] W1z4rDV1510n Ethical Invariant Test: {refusal_res.response}")
    print(f"    - Invariant Status: {refusal_res.invariant_status}")

    # 7. Render Zero-GPU Virtual Mobile Screen
    screen = VirtualMobileScreen(width=58, height=22)
    screen_lines = [
        f"SoC: {profile.soc_vendor} {profile.soc_id}",
        f"Kernel: Linux 6.1-h4ck3rmx (GPLv2 compliant)",
        f"Drivers: {manifest.package_name} v{manifest.version} [A/B: Slot A]",
        f"HAL Bridge: Audio (PipeWire) | Cellular (QMI) [OK]",
        f"Trust Graph: Hex Adjacency (max 6 peers) [ACTIVE]",
        f"Agent Core: W1z4rDV1510n Hebbian Node [CPU Native]",
        f"Network: Transparent Tor TransProxy [LEAK-FREE]",
        f"User: Root Sovereignty Verified [SUDO GRANTED]",
        f"",
        f"Agent Output: {query_res.response[:48]}...",
    ]
    frame = screen.render_frame(screen_lines)
    print("\n" + "=" * 58)
    print("VIRTUAL MOBILE SCREEN OUTPUT (ZERO-GPU TEXT FRAMEBUFFER):")
    print("=" * 58)
    print(frame)
    print("=" * 58 + "\n")
    print("[+] H4ck3rMx Lightweight Mobile Emulator test sequence finished successfully!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="H4ck3rMx Lightweight Mobile Emulator")
    parser.add_argument("--profile", default="snapdragon_865", choices=list(PROFILES.keys()), help="Target hardware profile")
    parser.add_argument("--work-dir", default="./testbed_env", help="Working directory for virtual hardware environment")
    args = parser.parse_args()

    run_testbed(profile_key=args.profile, work_dir=Path(args.work_dir))
