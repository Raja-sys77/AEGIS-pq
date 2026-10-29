"""
Unit test for ML-KEM-512, HKDF, and AEAD components
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.crypto.mlkem512 import MLKEM512, ntt_poly, intt_poly, poly_mul_ntt, Q
from src.crypto.hkdf_kdf import derive_session_keys
from src.crypto.aead_cipher import AEGISAEADCipher
from src.common.protocol import APBPFrame, MsgType, build_deterministic_nonce, HEADER_SIZE

class TestCryptoCore(unittest.TestCase):
    def test_ntt_roundtrip(self):
        poly = [i % Q for i in range(256)]
        fwd = ntt_poly(poly)
        inv = intt_poly(fwd)
        self.assertEqual(poly, inv, "NTT / iNTT forward and inverse transform must match original polynomial")

    def test_mlkem512_keygen_encaps_decaps(self):
        ek, dk = MLKEM512.keygen()
        self.assertEqual(len(ek), 800, "ML-KEM-512 encapsulation key must be 800 bytes")
        self.assertEqual(len(dk), 1632, "ML-KEM-512 decapsulation key must be 1632 bytes")
        
        c, ss_enc = MLKEM512.encaps(ek)
        self.assertEqual(len(c), 768, "ML-KEM-512 ciphertext must be 768 bytes")
        self.assertEqual(len(ss_enc), 32, "Shared secret must be 32 bytes")
        
        ss_dec = MLKEM512.decaps(c, dk)
        self.assertEqual(len(ss_dec), 32)
        self.assertEqual(ss_enc, ss_dec, "Shared secret from encapsulation and decapsulation must match identically")

    def test_mlkem512_tampered_ciphertext(self):
        ek, dk = MLKEM512.keygen()
        c, ss_enc = MLKEM512.encaps(ek)
        # Flip one bit in ciphertext
        c_tampered = bytearray(c)
        c_tampered[42] ^= 0x01
        ss_tampered = MLKEM512.decaps(bytes(c_tampered), dk)
        self.assertNotEqual(ss_enc, ss_tampered, "Tampered ciphertext must implicitly reject and produce different secret")

    def test_hkdf_derivation(self):
        shared_secret = os.urandom(32)
        aes_key, aux_key = derive_session_keys(shared_secret)
        self.assertEqual(len(aes_key), 32)
        self.assertEqual(len(aux_key), 32)
        self.assertNotEqual(aes_key, aux_key)

    def test_aead_roundtrip_and_tamper(self):
        key = os.urandom(32)
        cipher = AEGISAEADCipher(key)
        nonce = build_deterministic_nonce(node_id=2, seq_num=100)
        ad = b"APBP-v1-HEADER-DATA"
        plaintext = b"CRITICAL_SCADA_PAYLOAD_TELEMETRY_12345678"
        
        ciphertext = cipher.encrypt(nonce, plaintext, associated_data=ad)
        decrypted = cipher.decrypt(nonce, ciphertext, associated_data=ad, seq_num=100)
        self.assertEqual(plaintext, decrypted)
        
        # Test replay detection
        with self.assertRaises(ValueError):
            cipher.decrypt(nonce, ciphertext, associated_data=ad, seq_num=100)
            
        # Test tamper detection
        nonce2 = build_deterministic_nonce(node_id=2, seq_num=101)
        ct2 = bytearray(cipher.encrypt(nonce2, plaintext, associated_data=ad))
        ct2[10] ^= 0x01
        with self.assertRaises(Exception):
            cipher.decrypt(nonce2, bytes(ct2), associated_data=ad, seq_num=101)

    def test_apbp_framing(self):
        nonce = build_deterministic_nonce(node_id=1, seq_num=42)
        payload = b"TEST_PAYLOAD_BINARY_BYTES"
        frame = APBPFrame(msg_type=MsgType.DATA_PAYLOAD_AEAD, seq_num=42, nonce=nonce, payload=payload)
        packed = frame.pack()
        self.assertEqual(len(packed), HEADER_SIZE + len(payload))
        
        unpacked_frame, remaining = APBPFrame.unpack(packed)
        self.assertEqual(unpacked_frame.seq_num, 42)
        self.assertEqual(unpacked_frame.msg_type, MsgType.DATA_PAYLOAD_AEAD)
        self.assertEqual(unpacked_frame.nonce, nonce)
        self.assertEqual(unpacked_frame.payload, payload)
        self.assertEqual(len(remaining), 0)

if __name__ == "__main__":
    unittest.main()
