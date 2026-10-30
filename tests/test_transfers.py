"""
Unit and integration tests for Mode A (Legacy) and Mode B (AEGIS-PQ Secure) transfers
"""

import sys
import os
import unittest
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend.legacy_receiver import LegacyReceiverServer
from src.backend.secure_receiver import SecureReceiverServer
from src.backend.transfer_client import TransferClient

class TestEndToEndTransfers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start receivers on localhost test ports
        cls.legacy_receiver = LegacyReceiverServer(host="127.0.0.1", port=5568)
        cls.legacy_receiver.start()
        
        cls.secure_receiver = SecureReceiverServer(host="127.0.0.1", port=5566)
        cls.secure_receiver.start()
        
        time.sleep(0.2)
        cls.client = TransferClient(
            legacy_host="127.0.0.1",
            legacy_port=5568,
            secure_host="127.0.0.1",
            secure_port=5566
        )

    @classmethod
    def tearDownClass(cls):
        cls.legacy_receiver.stop()
        cls.secure_receiver.stop()

    def test_mode_a_legacy_transfer(self):
        payload = b"CRITICAL_UNENCRYPTED_TELEMETRY_PAYLOAD_12345"
        res = self.client.send_legacy_direct(payload, transfer_id="TX-LEGACY-001")
        self.assertTrue(res["success"])
        self.assertEqual(res["bytes_transferred"], len(payload))
        self.assertEqual(res["authenticated"], False)
        self.assertEqual(res["receiver_ack"]["status"], "RECEIVED")
        self.assertEqual(res["receiver_ack"]["sha256"], res["sha256"])

    def test_mode_b_secure_transfer(self):
        payload = b"PATIENT_CONFIDENTIAL_MEDICAL_SCAN_FRAME_DATA" * 10
        res = self.client.send_aegis_pq_secure(
            payload=payload,
            transfer_id="TX-SECURE-001",
            session_id="SES-TEST-001",
            register_key_callback=self.secure_receiver.register_session
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["authenticated"])
        self.assertEqual(res["receiver_ack"]["status"], "AUTHENTICATED")
        self.assertEqual(res["receiver_ack"]["sha256"], res["sha256"])
        self.assertIn("timings_breakdown_ms", res)
        self.assertGreater(res["timings_breakdown_ms"]["mlkem_keygen"], 0.0)

    def test_mode_b_tamper_rejection(self):
        # Transmit with invalid session key to simulate tampering
        payload = b"TAMPER_PAYLOAD"
        res = self.client.send_aegis_pq_secure(
            payload=payload,
            transfer_id="TX-TAMPER-001",
            session_id="SES-TAMPERED-UNREGISTERED",
            register_key_callback=None
        )
        self.assertFalse(res["success"])
        self.assertFalse(res["authenticated"])
        self.assertEqual(res["receiver_ack"]["status"], "REJECTED")

if __name__ == "__main__":
    unittest.main()
