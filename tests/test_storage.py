"""
Unit tests for H4ck3rMx Memory-Mapped Merkle Storage Engine.
"""

import unittest
import tempfile
import time
from pathlib import Path
from core.storage.merkle_engine import SovereignStorageEngine


class TestSovereignStorageEngine(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.engine = SovereignStorageEngine(self.tmp_dir.name, file_size_mb=1)

    def tearDown(self):
        self.engine.close()
        self.tmp_dir.cleanup()

    def test_write_and_read(self):
        data = b'{"battery": 92, "charging": true}'
        merkle_hash = self.engine.write("sys.power", data)
        self.assertEqual(len(merkle_hash), 32)

        read_data = self.engine.read("sys.power")
        self.assertEqual(read_data, data)

    def test_event_trigger(self):
        received = []

        def on_battery(key, val):
            received.append((key, val))

        self.engine.register_event_trigger("battery", on_battery)
        self.engine.write("sys.battery.level", b'{"percent": 45}')
        self.engine.write("sys.network.ip", b'{"ip": "10.0.0.1"}')

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "sys.battery.level")
        self.assertEqual(received[0][1], b'{"percent": 45}')

    def test_integrity_verification(self):
        self.engine.write("key1", b"value1")
        self.engine.write("key2", b"value2")
        valid, msg = self.engine.verify_integrity()
        self.assertTrue(valid)

    def test_time_trigger(self):
        fired = []

        def on_timer():
            fired.append(time.time())

        self.engine.schedule_time_trigger(0.05, on_timer)
        time.sleep(0.12)
        self.assertGreaterEqual(len(fired), 1)

    def test_duress_wipe(self):
        self.engine.write("secret.key", b"super_secret_payload")
        wipe_us = self.engine.duress_wipe()
        self.assertLess(wipe_us, 50000)  # Should wipe in well under 50ms
        self.assertIsNone(self.engine.read("secret.key"))


if __name__ == "__main__":
    unittest.main()
