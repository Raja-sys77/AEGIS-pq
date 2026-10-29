"""
Unit tests for Red-Team Cryptanalysis & Adversarial Injection Suite
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.redteam.redteam_suite import run_rsa_benchmark, shor_period_finder, calculate_shannon_entropy
from src.crypto.aead_cipher import AEGISAEADCipher
from src.common.protocol import build_deterministic_nonce

class TestRedTeamSuite(unittest.TestCase):
    def test_toy_rsa_factoring(self):
        results = run_rsa_benchmark()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r["status"], "FACTORED_BROKEN")
            self.assertIn("recovered_factor", r)

    def test_shors_period_finding(self):
        res = shor_period_finder(a=7, n=15)
        self.assertEqual(res["period_r"], 4)
        self.assertIn(3, res["factors_recovered"])
        self.assertIn(5, res["factors_recovered"])
        self.assertEqual(res["security_verdict"], "QUANTUM_VULNERABLE")

    def test_shannon_entropy_contrast(self):
        # Structured / repetitive data should have low entropy
        low_ent_data = b"A" * 1000
        self.assertLess(calculate_shannon_entropy(low_ent_data), 1.0)
        
        # Ciphertext from AES-256-GCM should have high entropy (close to 8.0)
        key = os.urandom(32)
        cipher = AEGISAEADCipher(key)
        nonce = build_deterministic_nonce(node_id=1, seq_num=1)
        ct = cipher.encrypt(nonce, b"Secret Medical Telemetry Stream Payload" * 50)
        high_ent = calculate_shannon_entropy(ct)
        self.assertGreater(high_ent, 7.8)

    def test_adversarial_bit_flip_rejected(self):
        key = os.urandom(32)
        cipher = AEGISAEADCipher(key)
        nonce = build_deterministic_nonce(node_id=1, seq_num=2)
        ct = bytearray(cipher.encrypt(nonce, b"AUTHENTIC_DATA_FRAME"))
        
        # Inject bit-flip
        ct[5] ^= 0x01
        with self.assertRaises(Exception):
            cipher.decrypt(nonce, bytes(ct), seq_num=2)

if __name__ == "__main__":
    unittest.main()
