"""
Integration and End-to-End API test suite for AEGIS-PQ backend
"""

import sys
import os
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend.app import app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"AEGIS", res.data)
        self.assertIn(b"CY \xc2\xb7 FOCUS", res.data)

    def test_system_info_endpoint(self):
        res = self.app.get("/api/system/info")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["version"], "1.1.0")
        self.assertIn("target_hardware", data)
        self.assertEqual(data["storage_budget"]["root_filesystem_free"], "5.4 MB")

    def test_crypto_operations_endpoint(self):
        res = self.app.get("/api/crypto/operations")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["standard"], "NIST FIPS 203 (ML-KEM-512)")
        self.assertEqual(data["public_key_bytes"], 800)
        self.assertEqual(data["ciphertext_bytes"], 768)

    def test_benchmarks_endpoint(self):
        res = self.app.get("/api/telemetry/benchmarks")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["fpga_pl_transform_ms"], 1.19)
        self.assertEqual(data["pure_python_arm_ms"], 32.26)
        self.assertAlmostEqual(data["speedup_ratio"], 27.11, places=1)

    def test_crypto_execute_op_endpoint(self):
        payload = {"message": "DICOM-DIAGNOSTIC-SCAN-FRAME-PAYLOAD" * 30}
        res = self.app.post("/api/crypto/execute-op", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertTrue(data["shared_secret_match"])
        self.assertGreater(data["entropy"], 7.0)

    def test_security_adversarial_injection(self):
        res = self.app.post("/api/security/execute", json={"attack_type": "bit_flip"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["outcome"], "TAMPER_DETECTED_AND_DROPPED")
        self.assertFalse(data["authenticated"])

if __name__ == "__main__":
    unittest.main()
