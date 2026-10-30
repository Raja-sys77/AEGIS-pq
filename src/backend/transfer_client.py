"""
AEGIS-PQ Transfer Client (Sender)
Executes Mode A (Direct Legacy Transfer) and Mode B (AEGIS-PQ Secure Transfer)
over actual TCP network sockets.
"""

import socket
import time
import json
import struct
import hashlib
from typing import Dict, Any, Optional

from src.crypto.mlkem512 import MLKEM512
from src.crypto.hkdf_kdf import derive_session_keys
from src.crypto.aead_cipher import AEGISAEADCipher
from src.common.protocol import APBPFrame, MsgType, build_deterministic_nonce

class TransferClient:
    def __init__(self,
                 legacy_host: str = "127.0.0.1",
                 legacy_port: int = 5558,
                 secure_host: str = "127.0.0.1",
                 secure_port: int = 5556):
        self.legacy_host = legacy_host
        self.legacy_port = legacy_port
        self.secure_host = secure_host
        self.secure_port = secure_port
        self.seq_num = 1

    def send_legacy_direct(self, payload: bytes, transfer_id: str) -> Dict[str, Any]:
        """
        Mode A: Direct legacy transfer without AEGIS-PQ protection.
        Transmits raw unencrypted payload directly to receiver.
        """
        start_time = time.perf_counter()
        payload_sha256 = hashlib.sha256(payload).hexdigest()
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        try:
            s.connect((self.legacy_host, self.legacy_port))
            header = {
                "transfer_id": transfer_id,
                "payload_len": len(payload),
                "mode": "LEGACY_DIRECT",
                "sha256": payload_sha256
            }
            header_bytes = json.dumps(header).encode("utf-8")
            s.sendall(struct.pack("!I", len(header_bytes)) + header_bytes)
            s.sendall(payload)
            
            resp = s.recv(4096)
            ack = json.loads(resp.decode("utf-8")) if resp else {}
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            return {
                "transfer_id": transfer_id,
                "mode": "LEGACY_DIRECT",
                "bytes_transferred": len(payload),
                "sha256": payload_sha256,
                "receiver_ack": ack,
                "latency_ms": round(elapsed_ms, 3),
                "authenticated": False,
                "security_level": "NONE (Vulnerable to Eavesdropping & Tampering)",
                "provenance": "LIVE SOFTWARE SOCKET TRANSFER",
                "success": (ack.get("status") == "RECEIVED" and ack.get("sha256") == payload_sha256)
            }
        except Exception as e:
            return {
                "transfer_id": transfer_id,
                "mode": "LEGACY_DIRECT",
                "bytes_transferred": len(payload),
                "error": str(e),
                "success": False,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
            }
        finally:
            s.close()

    def send_aegis_pq_secure(self,
                              payload: bytes,
                              transfer_id: str,
                              session_id: str,
                              register_key_callback = None) -> Dict[str, Any]:
        """
        Mode B: Secure transfer through AEGIS-PQ post-quantum authenticated envelope.
        Performs ML-KEM-512 KeyGen -> Encaps -> Decaps -> HKDF -> AES-256-GCM.
        """
        start_time = time.perf_counter()
        original_sha256 = hashlib.sha256(payload).hexdigest()
        
        # 1. PQC Key Establishment (FIPS 203 ML-KEM-512)
        t0 = time.perf_counter()
        ek, dk = MLKEM512.keygen()
        t_keygen_ms = (time.perf_counter() - t0) * 1000.0
        
        t0 = time.perf_counter()
        ciphertext_kem, ss_sender = MLKEM512.encaps(ek)
        t_encaps_ms = (time.perf_counter() - t0) * 1000.0
        
        t0 = time.perf_counter()
        ss_receiver = MLKEM512.decaps(ciphertext_kem, dk)
        t_decaps_ms = (time.perf_counter() - t0) * 1000.0
        
        assert ss_sender == ss_receiver, "ML-KEM-512 Shared Secret Mismatch"
        
        # 2. Key Derivation (RFC 5869 HKDF-SHA256)
        aes_key, aux_key = derive_session_keys(ss_sender)
        
        # Register session with secure receiver if callback provided
        if register_key_callback:
            register_key_callback(session_id, aes_key)
            
        # 3. Authenticated Encryption (NIST SP 800-38D AES-256-GCM)
        cipher = AEGISAEADCipher(aes_key)
        self.seq_num += 1
        nonce = build_deterministic_nonce(node_id=1, seq_num=self.seq_num)
        
        t0 = time.perf_counter()
        ciphertext_payload = cipher.encrypt(nonce, payload)
        t_encrypt_ms = (time.perf_counter() - t0) * 1000.0
        
        # 4. Pack into APBP-v1 frame
        meta = {
            "transfer_id": transfer_id,
            "session_id": session_id,
            "original_len": len(payload)
        }
        meta_bytes = json.dumps(meta).encode("utf-8")
        envelope = struct.pack("!I", len(meta_bytes)) + meta_bytes + ciphertext_payload
        
        frame = APBPFrame(
            msg_type=MsgType.DATA_PAYLOAD_AEAD,
            seq_num=self.seq_num,
            nonce=nonce,
            payload=envelope
        )
        wire_data = frame.pack()
        
        # 5. Transmit over network socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        try:
            s.connect((self.secure_host, self.secure_port))
            s.sendall(wire_data)
            
            resp = s.recv(4096)
            ack = json.loads(resp.decode("utf-8")) if resp else {}
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            return {
                "transfer_id": transfer_id,
                "session_id": session_id,
                "mode": "AEGIS_PQ_SECURE",
                "bytes_transferred": len(wire_data),
                "original_bytes": len(payload),
                "sha256": original_sha256,
                "receiver_ack": ack,
                "latency_ms": round(elapsed_ms, 3),
                "authenticated": (ack.get("status") == "AUTHENTICATED"),
                "security_level": "NIST FIPS 203 ML-KEM-512 + AES-256-GCM (Quantum Resistant)",
                "provenance": "LIVE SOFTWARE SOCKET TRANSFER",
                "timings_breakdown_ms": {
                    "mlkem_keygen": round(t_keygen_ms, 3),
                    "mlkem_encaps": round(t_encaps_ms, 3),
                    "mlkem_decaps": round(t_decaps_ms, 3),
                    "aes_gcm_encrypt": round(t_encrypt_ms, 3),
                    "total_network_e2e": round(elapsed_ms, 3)
                },
                "success": (ack.get("status") == "AUTHENTICATED" and ack.get("sha256") == original_sha256)
            }
        except Exception as e:
            return {
                "transfer_id": transfer_id,
                "mode": "AEGIS_PQ_SECURE",
                "error": str(e),
                "success": False,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
            }
        finally:
            s.close()
