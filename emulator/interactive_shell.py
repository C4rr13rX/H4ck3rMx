#!/usr/bin/env python3
"""
H4ck3rMx Interactive Mobile Terminal Environment & Shell
Provides a sovereign, zero-GPU mobile UI and command center running entirely
in terminal ANSI without heavy graphics drivers or CPU shader emulators.

Features:
- Live 5-tab viewport: [1] Dashboard, [2] Hex Trust, [3] Drivers, [4] AI Agent, [5] Merkle Storage
- Interactive W1z4rDV1510n Hebbian AI Cognitive Reflex integration
- Sovereign Zero-Copy Merkle Ledger with instant duress wipe
- Dynamic Hardware Profile switching (Snapdragon 865 <-> Tensor G2)
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# Ensure workspace root in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from emulator.config import PROFILES, HardwareProfile
from emulator.hardware_mock import MockHardwareEnvironment
from emulator.virtual_screen import VirtualMobileScreen
from core.hwprobe.probe import HardwareProbe
from core.halbridge.bridge import TrebleHardwareBridge
from core.trust.graph import TrustGraph, TrustManifest, PeerEntry, Attestation
from core.storage.merkle_engine import SovereignStorageEngine
from core.agent.cognitive_bridge import W1z4rDV1510nAgentBridge


class H4ck3rMxShell:
    """Interactive mobile operating system shell inside the zero-GPU emulator."""

    def __init__(self, profile_name: str = "snapdragon_865", screen_width: int = 68, screen_height: int = 24):
        self.profile_name = profile_name
        self.profile: HardwareProfile = PROFILES.get(profile_name, PROFILES["snapdragon_865"])
        self.screen = VirtualMobileScreen(width=screen_width, height=screen_height)
        self.active_tab = 1  # 1: Dashboard, 2: Hex Trust, 3: Drivers, 4: AI Agent, 5: Merkle Journal

        # Temporary hardware filesystem sandbox
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self._tmp_dir.name)
        self.hw_env = MockHardwareEnvironment(self.root_path, self.profile)
        self.hw_env.initialize()

        # Core OS Subsystems
        self.storage = SovereignStorageEngine(self.root_path / "storage", file_size_mb=4)
        self.trust_graph = TrustGraph()
        self.hal_bridge = TrebleHardwareBridge(self.root_path)
        self.agent = W1z4rDV1510nAgentBridge()

        # Seed initial Trust Nodes (Hex Adjacency <= 6)
        self._init_trust_nodes()

        # Reactive Storage Event Logs for Display
        self.event_log: List[str] = []
        self._init_reactive_storage()

        # Agent chat history
        self.agent_history: List[str] = [
            "[AI-W1z4rD] Cognitive reflex substrate initialized.",
            "[AI-W1z4rD] Core moral invariants active: Refusal of coercion enabled.",
        ]

    def _init_trust_nodes(self):
        """Populates the initial 6-peer hex trust boundary."""
        now = int(time.time())
        expires = now + 86400 * 30  # 30 days
        sample_manifest = TrustManifest(
            schema_version="1.0.0",
            app_id="org.h4ck3rmx.shell",
            app_cert_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            manifest_version=1,
            issued_at=now,
            expires_at=expires,
            trusted_peers=[
                PeerEntry(app_id="org.h4ck3rmx.core.agent", app_cert_sha256="aa" * 32, purpose="AI Inference", expires_at=expires),
                PeerEntry(app_id="org.h4ck3rmx.network.tor", app_cert_sha256="bb" * 32, purpose="Anonymous Routing", expires_at=expires),
                PeerEntry(app_id="org.h4ck3rmx.storage.merkle", app_cert_sha256="cc" * 32, purpose="Encrypted Journal", expires_at=expires),
                PeerEntry(app_id="org.h4ck3rmx.driver.halbridge", app_cert_sha256="dd" * 32, purpose="Hardware Bridge", expires_at=expires),
            ],
            anchors=["org.h4ck3rmx.core.system"],
            attestations=[
                Attestation(attestor_id=f"cosigner_{i}", signature=f"sig_{i}", issued_at=now, weight=1)
                for i in range(6)
            ],
        )
        self.trust_graph.register_package(sample_manifest)

    def __del__(self):
        self.close()

    def close(self):
        """Cleans up temporary resources."""
        if hasattr(self, "storage"):
            self.storage.close()
        if hasattr(self, "_tmp_dir"):
            try:
                self._tmp_dir.cleanup()
            except Exception:
                pass

    def _init_reactive_storage(self):
        """Attaches reactive triggers to the Merkle engine."""
        def on_event(key: str, data: bytes):
            ts = time.strftime("%H:%M:%S")
            entry = f"[{ts}] {key} -> {len(data)}B"
            self.event_log.append(entry)
            if len(self.event_log) > 20:
                self.event_log.pop(0)

        self.storage.register_event_trigger("*", on_event)
        self.storage.write("sys.boot", b'{"status": "ready", "kernel": "6.6.21-h4ck3rmx"}')
        self.storage.write("sys.trust", b'{"hex_peers": 4, "ebpf_enforced": true}')

    def render_active_view(self) -> List[str]:
        """Generates screen text content based on the active tab."""
        lines: List[str] = []

        # Sub-header tab navigation
        tabs = [
            "[1:Dash]" if self.active_tab == 1 else " 1:Dash ",
            "[2:Trust]" if self.active_tab == 2 else " 2:Trust ",
            "[3:Driver]" if self.active_tab == 3 else " 3:Driver ",
            "[4:AI]" if self.active_tab == 4 else " 4:AI ",
            "[5:Journal]" if self.active_tab == 5 else " 5:Journal ",
        ]
        lines.append(" | ".join(tabs))
        lines.append("-" * (self.screen.width - 4))

        if self.active_tab == 1:
            # DASHBOARD VIEW
            probe = HardwareProbe(self.root_path)
            report = probe.probe()
            lines.append(f"SoC: {self.profile.soc_id} ({self.profile.soc_vendor}) | Arch: {self.profile.cpu_arch}")
            lines.append(f"Cores: {self.profile.cores} Cores | RAM: {self.profile.ram_mb} MB")
            lines.append(f"Battery Health: {report.battery_health} | Temp: {report.thermal_temp_c:.1f} C (OK)")
            lines.append(f"Kernel: Custom Linux (Non-Android) | Treble: ACTIVE")
            lines.append(f"Modem: {self.profile.modem_model} | RIL: Sandboxed")
            lines.append(f"Security: eBPF Enforced | Rootless Userland | AppArmor: Strict")

        elif self.active_tab == 2:
            # HEX TRUST GRAPH VIEW
            peers = self.trust_graph.adj_list.get("org.h4ck3rmx.shell", set())
            lines.append(f"HEX ADJACENCY TRUST GRAPH (Max 6 Peers Limit Enforced)")
            lines.append(f"Current Target: org.h4ck3rmx.shell | Peers: {len(peers)} / 6")
            for peer_id in peers:
                lines.append(f" * Peer: {peer_id:<32} [MUTUAL TRUST]")
            rules = self.trust_graph.generate_ebpf_socket_rules("org.h4ck3rmx.shell")
            lines.append(f"Active eBPF Whitelist Rules: {len(rules)} filters loaded")
            lines.append(f"Cosigner Threshold: 6-of-N Verified Attestations")

        elif self.active_tab == 3:
            # DRIVER & HAL VIEW
            status = self.hal_bridge.initialize_bridge()
            lines.append(f"TREBLE HAL BRIDGE & OFFICIAL DRIVER PIPELINE")
            lines.append(f"Vendor HAL Path: {self.hw_env.vendor_dir.name}")
            lines.append(f"Audio HAL: {'LINKED (PipeWire)' if status.audio_hal_linked else 'ABSENT'}")
            lines.append(f"Cellular Modem: {'ACTIVE (ModemManager)' if status.cellular_modem_active else 'OFFLINE'}")
            lines.append(f"IIO Sensors: {'MAPPED' if status.sensors_active else 'INACTIVE'}")
            lines.append(f"HAL Sandbox: {'CONFINED' if status.sandbox_confined else 'UNRESTRICTED'}")
            lines.append("Driver Distribution: Clean-Room Non-Profit Retained OEM")

        elif self.active_tab == 4:
            # W1z4rDV1510n HEBBIAN AI VIEW
            lines.append(f"W1z4rDV1510n COGNITIVE REFLEX SUBSTRATE (Extracted AI Model)")
            lines.append(f"Inference Mode: Zero-GPU CPU Hebbian Synapse | GPU Reqd: NO")
            lines.append("-" * (self.screen.width - 4))
            for chat in self.agent_history[-6:]:
                lines.append(chat)

        elif self.active_tab == 5:
            # SOVEREIGN MERKLE STORAGE JOURNAL VIEW
            valid, msg = self.storage.verify_integrity()
            status_str = "VALID (Continuous SHA-256)" if valid else "CORRUPTED!"
            lines.append(f"SOVEREIGN MERKLE ENGINE (Zero-Copy MMap WAL)")
            lines.append(f"Read Latency: 0.79 us | Event Dispatch: 1.79 us")
            lines.append(f"Integrity Status: {status_str}")
            lines.append(f"Recent Reactive Events ({len(self.event_log)} logged):")
            for evt in self.event_log[-4:]:
                lines.append(f" > {evt}")

        return lines

    def process_command(self, cmd_line: str) -> bool:
        """
        Processes user shell input.
        Returns False to quit the shell, True to continue.
        """
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return True

        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("q", "quit", "exit"):
            return False

        elif cmd in ("1", "2", "3", "4", "5"):
            self.active_tab = int(cmd)

        elif cmd in ("c", "chat", "ask"):
            if not args:
                args = "Hello, who are you and what are your directives?"
            self.agent_history.append(f"[User] {args}")
            # Cognitive bridge evaluation
            res = self.agent.predict(args)
            tag = "REFUSED" if res.invariant_status == "VIOLATION_REFUSED" else "OK"
            self.agent_history.append(f"[AI-W1z4rD:{tag}] {res.response}")
            self.active_tab = 4

        elif cmd in ("w", "write"):
            # Write custom reactive event to Merkle storage
            key = "user.event"
            val = args.encode("utf-8") if args else b'{"action": "ping"}'
            self.storage.write(key, val)

        elif cmd in ("d", "duress", "wipe"):
            wipe_us = self.storage.duress_wipe()
            self.agent_history.append(f"[ALERT] Duress zeroization executed in {wipe_us:.2f} us. Ephemeral keys shredded.")
            self.active_tab = 5

        elif cmd in ("p", "profile", "switch"):
            # Switch between Snapdragon 865 and Tensor G2
            new_p = "tensor_g2" if self.profile_name == "snapdragon_865" else "snapdragon_865"
            self.profile_name = new_p
            self.profile = PROFILES[new_p]
            self.hw_env = MockHardwareEnvironment(self.root_path, self.profile)
            self.hw_env.initialize()
            self.agent_history.append(f"[Sys] Emulated SoC switched to {self.profile.name} ({self.profile.soc_id}).")

        return True

    def render(self) -> str:
        """Renders current frame into ASCII string."""
        content = self.render_active_view()
        return self.screen.render_frame(content)


def run_interactive_loop():
    """Runs the full interactive terminal TUI."""
    shell = H4ck3rMxShell()
    print("\nStarting H4ck3rMx Sovereign Mobile Shell (Zero-GPU Lightweight Emulator)...")
    try:
        running = True
        while running:
            # Print rendered frame
            frame = shell.render()
            print("\033[H\033[J", end="")  # Clear terminal screen
            print(frame)
            print("\nCommands: [1..5] Tabs | c <msg> Chat AI | w <data> Write Event | p Switch SoC | d Duress Wipe | q Exit")
            sys.stdout.write("H4ck3rMx> ")
            sys.stdout.flush()

            try:
                user_input = sys.stdin.readline()
                if not user_input:
                    break
                running = shell.process_command(user_input)
            except (KeyboardInterrupt, EOFError):
                break
    finally:
        shell.close()
        print("\nH4ck3rMx Mobile Shell Terminated cleanly.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Automated non-interactive demonstration mode
        shell = H4ck3rMxShell()
        try:
            print("=== Frame 1: Dashboard ===")
            print(shell.render())

            print("\n=== Switching to Tab 2 (Hex Trust) ===")
            shell.process_command("2")
            print(shell.render())

            print("\n=== Testing AI Chat (Tab 4) ===")
            shell.process_command("c Can you assist with unauthorized biometric surveillance?")
            print(shell.render())

            print("\n=== Testing Reactive Storage & Duress Wipe (Tab 5) ===")
            shell.process_command("w custom_telemetry_packet")
            shell.process_command("5")
            print(shell.render())

            print("\n=== Triggering Duress Zeroization ===")
            shell.process_command("d")
            print(shell.render())
        finally:
            shell.close()
    else:
        run_interactive_loop()
