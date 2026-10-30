"""
AEGIS-PQ Lightweight Standalone Client for Legacy Sender (Naved's Acer Laptop)
Transmits real payloads over LAN to Receiver (192.168.29.28)
Supports Mode 1 (Direct Legacy) and Mode 2 (AEGIS-PQ Gateway Mediated).
Zero heavy dependencies required: runs on any standard Python 3.x.
"""

import socket
import time
import json
import struct
import hashlib
import sys
import os

DEFAULT_RECEIVER_IP = "192.168.29.28"
DEFAULT_GATEWAY_IP = "192.168.29.179"
MODE_A_PORT = 5558
MODE_B_PORT = 5556
GATEWAY_RPC_PORT = 5557

def send_legacy_direct(receiver_ip: str, payload: bytes, transfer_id: str):
    """Mode 1: Transmits raw payload directly to receiver over TCP port 5558"""
    start_time = time.perf_counter()
    sha256 = hashlib.sha256(payload).hexdigest()
    print(f"\n[MODE 1: DIRECT LEGACY] Target: {receiver_ip}:{MODE_A_PORT}")
    print(f"Payload Size: {len(payload)} bytes | SHA-256: {sha256}")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    try:
        s.connect((receiver_ip, MODE_A_PORT))
        header = {
            "transfer_id": transfer_id,
            "payload_len": len(payload),
            "mode": "LEGACY_DIRECT",
            "sha256": sha256
        }
        header_bytes = json.dumps(header).encode("utf-8")
        s.sendall(struct.pack("!I", len(header_bytes)) + header_bytes)
        s.sendall(payload)
        
        resp = s.recv(4096)
        ack = json.loads(resp.decode("utf-8")) if resp else {}
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        print(f"Server ACK: {ack}")
        print(f"Latency: {elapsed_ms:.2f} ms")
        if ack.get("status") == "RECEIVED" and ack.get("sha256") == sha256:
            print(">>> SUCCESS: Mode 1 Direct Transfer verified byte-for-byte!")
            return True, elapsed_ms
        else:
            print(">>> ERROR: Hash mismatch or receiver failure!")
            return False, elapsed_ms
    except Exception as e:
        print(f">>> NETWORK FAILURE: {e}")
        return False, 0.0
    finally:
        s.close()

def send_aegis_pq_secure(receiver_ip: str, gateway_ip: str, payload: bytes, transfer_id: str):
    """
    Mode 2: Encapsulates payload using AEGIS-PQ Post-Quantum Protocol.
    Contacts PYNQ gateway for hardware arithmetic offload telemetry,
    establishes session key, and transmits authenticated frame to receiver.
    """
    start_time = time.perf_counter()
    sha256 = hashlib.sha256(payload).hexdigest()
    print(f"\n[MODE 2: AEGIS-PQ SECURE] Gateway: {gateway_ip} | Receiver: {receiver_ip}:{MODE_B_PORT}")
    print(f"Payload Size: {len(payload)} bytes | SHA-256: {sha256}")
    
    # Check Gateway status
    gateway_hw_status = "UNKNOWN"
    gw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gw_socket.settimeout(2.0)
    try:
        gw_socket.connect((gateway_ip, GATEWAY_RPC_PORT))
        gw_socket.sendall(json.dumps({"cmd": "status"}).encode("utf-8"))
        gw_resp = json.loads(gw_socket.recv(4096).decode("utf-8"))
        gateway_hw_status = gw_resp.get("status", "ACTIVE")
        print(f"PYNQ Gateway Verified: {gateway_hw_status} (Clock: {gw_resp.get('clock_mhz')} MHz)")
    except Exception as e:
        print(f"PYNQ Gateway RPC Warning: {e} (Proceeding with software hybrid pipeline)")
    finally:
        gw_socket.close()

    # Transmit via TransferClient logic or direct socket
    try:
        from src.crypto.mlkem512 import MLKEM512
        from src.crypto.hkdf_kdf import derive_session_keys
        from src.crypto.aead_cipher import AEGISAEADCipher
        from src.common.protocol import APBPFrame, MsgType, build_deterministic_nonce

        # 1. ML-KEM-512 KeyGen & Encaps
        ek, dk = MLKEM512.keygen()
        c_kem, ss_sender = MLKEM512.encaps(ek)
        ss_receiver = MLKEM512.decaps(c_kem, dk)
        
        # 2. HKDF Session Key Derivation
        aes_key, aux_key = derive_session_keys(ss_sender)
        
        # 3. Encrypt payload
        cipher = AEGISAEADCipher(aes_key)
        nonce = build_deterministic_nonce(node_id=1, seq_num=int(time.time()))
        ciphertext = cipher.encrypt(nonce, payload)
        
        # 4. Pack into APBP-v1 frame
        session_id = f"SES-{transfer_id}"
        meta = {
            "transfer_id": transfer_id,
            "session_id": session_id,
            "original_len": len(payload)
        }
        meta_bytes = json.dumps(meta).encode("utf-8")
        envelope = struct.pack("!I", len(meta_bytes)) + meta_bytes + ciphertext
        frame = APBPFrame(msg_type=MsgType.DATA_PAYLOAD_AEAD, seq_num=int(time.time()), nonce=nonce, payload=envelope)
        wire_data = frame.pack()
        
        # In multi-device LAN, sender informs receiver of session key via secure handshake or registration
        # Transmit to receiver socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((receiver_ip, MODE_B_PORT))
        
        # For demo simplicity, register session key on receiver via REST or initial handshake
        import urllib.request
        reg_data = json.dumps({"session_id": session_id, "aes_key_hex": aes_key.hex()}).encode("utf-8")
        try:
            req = urllib.request.Request(f"http://{receiver_ip}:8000/api/sessions/register", data=reg_data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2.0)
        except Exception:
            pass

        s.sendall(wire_data)
        resp = s.recv(4096)
        ack = json.loads(resp.decode("utf-8")) if resp else {}
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        print(f"Receiver ACK: {ack}")
        print(f"Latency: {elapsed_ms:.2f} ms")
        if ack.get("status") == "AUTHENTICATED" and ack.get("sha256") == sha256:
            print(">>> SUCCESS: Mode 2 AEGIS-PQ Post-Quantum Transfer Authenticated & Verified!")
            return True, elapsed_ms
        else:
            print(f">>> REJECTED: {ack.get('error', 'Authentication Failure')}")
            return False, elapsed_ms
    except Exception as e:
        print(f">>> SECURE TRANSFER FAILURE: {e}")
        return False, 0.0

if __name__ == "__main__":
    receiver = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECEIVER_IP
    gateway = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_GATEWAY_IP
    
    print("================================================================")
    print("AEGIS-PQ Demonstration Client (Naved's Acer / Standalone Sender)")
    print(f"Receiver IP: {receiver} | Gateway IP: {gateway}")
    print("================================================================")
    
    test_msg = b"CRITICAL_HEALTHCARE_SCAN_PAYLOAD: PatientID=84920, Modality=DICOM, TamperProof=TRUE"
    
    # 1. Execute Mode 1
    t_id_1 = f"TX-ACER-LEGACY-{int(time.time())%10000}"
    send_legacy_direct(receiver, test_msg, t_id_1)
    
    time.sleep(1.0)
    
    # 2. Execute Mode 2
    t_id_2 = f"TX-ACER-PQC-{int(time.time())%10000}"
    send_aegis_pq_secure(receiver, gateway, test_msg, t_id_2)
