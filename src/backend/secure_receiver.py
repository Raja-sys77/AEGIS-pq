"""
AEGIS-PQ Dedicated Secure APBP-v1 Receiver Service
Listens for authenticated post-quantum secure payload transfers (Mode B).
Default port: 5556.
"""

import socket
import threading
import time
import json
import hashlib
from typing import Dict, Any, List

from src.common.protocol import APBPFrame, MsgType, HEADER_SIZE
from src.crypto.aead_cipher import AEGISAEADCipher

class SecureReceiverServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5556):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.received_transfers: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.active_sessions: Dict[str, bytes] = {} # session_id -> aes_key

    def register_session(self, session_id: str, aes_key: bytes):
        with self.lock:
            self.active_sessions[session_id] = aes_key

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()
            except Exception:
                break

    def _handle_conn(self, conn: socket.socket, addr):
        start_time = time.perf_counter()
        meta = {}
        auth_success = False
        decrypted_payload = b""
        error_msg = ""
        ciphertext = b""
        try:
            # 1. Read exactly HEADER_SIZE bytes
            header_buffer = bytearray()
            while len(header_buffer) < HEADER_SIZE:
                chunk = conn.recv(HEADER_SIZE - len(header_buffer))
                if not chunk:
                    conn.close()
                    return
                header_buffer.extend(chunk)
                
            version, msg_type, seq_num, nonce, payload_len, flags = APBPFrame.unpack_header(header_buffer)
            
            # 2. Read exactly payload_len bytes
            payload_data = bytearray()
            while len(payload_data) < payload_len:
                chunk = conn.recv(min(4096, payload_len - len(payload_data)))
                if not chunk:
                    break
                payload_data.extend(chunk)
                
            raw_payload = bytes(payload_data)
            
            # The payload format: meta_len (4 bytes) + meta (JSON) + ciphertext
            import struct
            meta_len = struct.unpack("!I", raw_payload[:4])[0]
            meta = json.loads(raw_payload[4:4+meta_len].decode("utf-8"))
            ciphertext = raw_payload[4+meta_len:]
            
            session_id = meta.get("session_id")
            aes_key = self.active_sessions.get(session_id)
            
            if not aes_key:
                error_msg = "UNKNOWN_SESSION_KEY"
            else:
                cipher = AEGISAEADCipher(aes_key)
                try:
                    decrypted_payload = cipher.decrypt(nonce, ciphertext, seq_num=seq_num)
                    auth_success = True
                except Exception as e:
                    error_msg = str(e)
                    
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            sha256 = hashlib.sha256(decrypted_payload).hexdigest() if auth_success else "AUTH_FAILED"
            
            # Send ACK back to sender
            ack = {
                "status": "AUTHENTICATED" if auth_success else "REJECTED",
                "transfer_id": meta.get("transfer_id"),
                "sha256": sha256,
                "error": error_msg,
                "elapsed_ms": round(elapsed_ms, 3)
            }
            conn.sendall(json.dumps(ack).encode("utf-8"))
            
            with self.lock:
                self.received_transfers.append({
                    "transfer_id": meta.get("transfer_id"),
                    "session_id": meta.get("session_id"),
                    "mode": "AEGIS_PQ_SECURE",
                    "sender": addr[0],
                    "timestamp": time.strftime("%H:%M:%S"),
                    "payload_len": len(decrypted_payload) if auth_success else len(ciphertext),
                    "sha256": sha256,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "authenticated": auth_success,
                    "error": error_msg if not auth_success else None,
                    "encryption": "NIST FIPS 203 ML-KEM-512 + AES-256-GCM"
                })
        except Exception as e:
            try:
                err_ack = {
                    "status": "REJECTED",
                    "transfer_id": meta.get("transfer_id", "UNKNOWN"),
                    "error": str(e),
                    "sha256": "AUTH_FAILED"
                }
                conn.sendall(json.dumps(err_ack).encode("utf-8"))
            except Exception:
                pass
        finally:
            conn.close()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
