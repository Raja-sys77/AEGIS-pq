"""
Integration test suite for Mode A and Mode B REST endpoints in app.py
"""

import sys
import os
import unittest
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend.app import app

class TestAppAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Transfer Lab", res.data)
        self.assertIn(b"CY \xc2\xb7 FOCUS", res.data)

    def test_legacy_transfer_endpoint(self):
        res = self.client.post("/api/transfers/execute", json={
            "mode": "LEGACY_DIRECT",
            "message": "UNPROTECTED_LEGACY_STREAM_DATA"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["mode"], "LEGACY_DIRECT")
        self.assertFalse(data["authenticated"])
        self.assertIn("latency_ms", data)

    def test_secure_transfer_endpoint(self):
        res = self.client.post("/api/transfers/execute", json={
            "mode": "AEGIS_PQ_SECURE",
            "message": "PROTECTED_PQC_AUTHENTICATED_STREAM_DATA"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["mode"], "AEGIS_PQ_SECURE")
        self.assertTrue(data["authenticated"])
        self.assertIn("timings_breakdown_ms", data)

    def test_transfers_results_endpoint(self):
        res = self.client.get("/api/transfers/results")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("results", data)
        self.assertGreaterEqual(data["total_transfers"], 2)

    def test_security_execute_bitflip(self):
        res = self.client.post("/api/security/execute", json={"attack_type": "bit_flip"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["outcome"], "TAMPER_DETECTED_AND_DROPPED")

if __name__ == "__main__":
    unittest.main()
