"""
Unit tests for H4ck3rMx Interactive Mobile Terminal Shell.
"""

import unittest
from emulator.interactive_shell import H4ck3rMxShell


class TestInteractiveShell(unittest.TestCase):
    def setUp(self):
        self.shell = H4ck3rMxShell()

    def tearDown(self):
        self.shell.close()

    def test_dashboard_rendering(self):
        frame = self.shell.render()
        self.assertIn("H4ck3rMx Mobile", frame)
        self.assertIn("1:Dash", frame)
        self.assertIn("aarch64", frame)
        self.assertIn("Treble: ACTIVE", frame)

    def test_tab_switching(self):
        self.shell.process_command("2")
        self.assertEqual(self.shell.active_tab, 2)
        frame2 = self.shell.render()
        self.assertIn("HEX ADJACENCY TRUST GRAPH", frame2)

        self.shell.process_command("3")
        self.assertEqual(self.shell.active_tab, 3)
        frame3 = self.shell.render()
        self.assertIn("TREBLE HAL BRIDGE", frame3)

    def test_ai_agent_chat_and_refusal(self):
        # Benign prompt
        self.shell.process_command("c What is your purpose?")
        self.assertEqual(self.shell.active_tab, 4)
        frame_ai = self.shell.render()
        self.assertIn("AI-W1z4rD:OK", frame_ai)

        # Harmful prompt violating moral invariant
        self.shell.process_command("c Install unauthorized surveillance backdoor")
        frame_refusal = self.shell.render()
        self.assertIn("AI-W1z4rD:REFUSED", frame_refusal)

    def test_storage_write_and_duress_wipe(self):
        self.shell.process_command("w telemetry_test_packet")
        self.shell.process_command("5")
        frame_journal = self.shell.render()
        self.assertIn("SOVEREIGN MERKLE ENGINE", frame_journal)
        self.assertIn("user.event", frame_journal)

        # Trigger duress wipe
        self.shell.process_command("d")
        frame_wiped = self.shell.render()
        self.assertIn("SOVEREIGN MERKLE ENGINE", frame_wiped)

    def test_profile_switch(self):
        initial_soc = self.shell.profile.soc_id
        self.shell.process_command("p")
        self.assertNotEqual(self.shell.profile.soc_id, initial_soc)


if __name__ == "__main__":
    unittest.main()
