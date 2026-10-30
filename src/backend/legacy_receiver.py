"""
AEGIS-PQ Dedicated Legacy Receiver Service
Listens for direct unencrypted / legacy-encrypted payload transfers (Mode A).
Default port: 5558.
"""

import socket
import threading
import time
import json
import hashlib
from typing import Dict, Any, List

class LegacyReceiverServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5558):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.received_transfers: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

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
        try:
            # Protocol: 4 bytes length prefix (big-endian), followed by JSON metadata header, then payload bytes
            raw_len = conn.recv(4)
            if not raw_len or len(raw_len) < 4:
                conn.close()
                return
            
            import struct
            header_len = struct.unpack("!I", raw_len)[0]
            header_bytes = conn.recv(header_len)
            header = json.loads(header_bytes.decode("utf-8"))
            
            payload_len = header.get("payload_len", 0)
            received_bytes = bytearray()
            while len(received_bytes) < payload_len:
                chunk = conn.recv(min(4096, payload_len - len(received_bytes)))
                if not chunk:
                    break
                received_bytes.extend(chunk)
                
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            payload_sha256 = hashlib.sha256(received_bytes).hexdigest()
            
            # Send ACK
            ack = {
                "status": "RECEIVED",
                "transfer_id": header.get("transfer_id"),
                "bytes_received": len(received_bytes),
                "sha256": payload_sha256,
                "elapsed_ms": round(elapsed_ms, 3)
            }
            conn.sendall(json.dumps(ack).encode("utf-8"))
            
            with self.lock:
                self.received_transfers.append({
                    "transfer_id": header.get("transfer_id"),
                    "mode": "LEGACY_DIRECT",
                    "sender": addr[0],
                    "timestamp": time.strftime("%H:%M:%S"),
                    "payload_len": len(received_bytes),
                    "sha256": payload_sha256,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "authenticated": False, # Explicit honesty: Mode A provides ZERO PQC/AEAD authentication
                    "encryption": "NONE (Plaintext Wiretap Vulnerable)"
                })
        except Exception as e:
            pass
        finally:
            conn.close()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
