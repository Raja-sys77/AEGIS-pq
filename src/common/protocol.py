"""
AEGIS-PQ Wire Protocol Definition (APBP-v1)
AEGIS-PQ Bump-in-the-wire Protocol version 1

Binary Header Specification (36 Bytes Total, Big-Endian):
- Magic (4 bytes): 0x41 0x45 0x47 0x53 ('AEGS')
- Version (2 bytes): 0x00 0x01
- Message Type (2 bytes):
    0x0001: PQC_KEYGEN_PUBKEY (Client -> Gateway / Gateway -> Receiver)
    0x0002: PQC_ENCAPS_CIPHERTEXT (Gateway -> Client / Receiver)
    0x0003: DATA_PAYLOAD_AEAD (AES-256-GCM Encrypted Payload)
    0x0004: TELEMETRY_HEARTBEAT (FPGA & Gateway Status)
    0x0005: ERROR_NOTIFICATION (Protocol/Crypto Error)
- Sequence Number (8 bytes): 64-bit uint strictly increasing (replay protection)
- Nonce / IV (12 bytes): 96-bit AES-GCM IV (4-byte node ID + 8-byte seq)
- Payload Length (4 bytes): 32-bit uint payload byte count
- Reserved / Flags (4 bytes): Flag bits (e.g., bit 0: FPGA_ACCELERATED, bit 1: REDTEAM_TAMPER)

Followed immediately by:
- Payload (Payload Length bytes)
- If DATA_PAYLOAD_AEAD: AEAD Tag is the last 16 bytes of Payload (or appended)
"""

import struct
import time
from enum import IntEnum
from typing import Tuple, Optional

APBP_MAGIC = b"AEGS"
APBP_VERSION = 1
HEADER_FORMAT = "!4sHHQQ12sII"  # Adjusted to match 36-byte clean layout or explicit struct

# Explicit 36-byte header packing:
# magic: 4s (4B)
# version: H (2B)
# msg_type: H (2B)
# seq_num: Q (8B)
# nonce: 12s (12B)
# payload_len: I (4B)
# flags: I (4B)
# Sum: 4 + 2 + 2 + 8 + 12 + 4 + 4 = 36 Bytes
HEADER_STRUCT = struct.Struct("!4sHHQ12sII")
HEADER_SIZE = HEADER_STRUCT.size
assert HEADER_SIZE == 36, f"Header size must be exactly 36 bytes, got {HEADER_SIZE}"

class MsgType(IntEnum):
    PQC_KEYGEN_PUBKEY = 0x0001
    PQC_ENCAPS_CIPHERTEXT = 0x0002
    DATA_PAYLOAD_AEAD = 0x0003
    TELEMETRY_HEARTBEAT = 0x0004
    ERROR_NOTIFICATION = 0x0005
    PING_PONG = 0x0006

class FlagBits(IntEnum):
    NONE = 0x00000000
    FPGA_ACCELERATED = 0x00000001
    REDTEAM_TAMPER = 0x00000002
    REPLAY_FRAME = 0x00000004
    END_OF_STREAM = 0x00000008

class APBPFrame:
    def __init__(self,
                 msg_type: MsgType,
                 seq_num: int,
                 nonce: bytes,
                 payload: bytes,
                 flags: int = 0,
                 version: int = APBP_VERSION):
        self.magic = APBP_MAGIC
        self.version = version
        self.msg_type = MsgType(msg_type)
        self.seq_num = seq_num
        if len(nonce) != 12:
            raise ValueError(f"Nonce must be 12 bytes, got {len(nonce)}")
        self.nonce = nonce
        self.payload = payload
        self.payload_len = len(payload)
        self.flags = flags

    def pack(self) -> bytes:
        header = HEADER_STRUCT.pack(
            self.magic,
            self.version,
            int(self.msg_type),
            self.seq_num,
            self.nonce,
            self.payload_len,
            self.flags
        )
        return header + self.payload

    @classmethod
    def unpack(cls, data: bytes) -> Tuple["APBPFrame", bytes]:
        """
        Unpack a single APBPFrame from raw bytes.
        Returns (frame, remaining_bytes).
        Raises ValueError if data is incomplete or invalid.
        """
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Data length {len(data)} is less than header size {HEADER_SIZE}")
        
        magic, version, msg_type_val, seq_num, nonce, payload_len, flags = HEADER_STRUCT.unpack(data[:HEADER_SIZE])
        
        if magic != APBP_MAGIC:
            raise ValueError(f"Invalid APBP magic bytes: {magic!r}")
        if version != APBP_VERSION:
            raise ValueError(f"Unsupported APBP version: {version}")
        
        total_len = HEADER_SIZE + payload_len
        if len(data) < total_len:
            raise ValueError(f"Incomplete frame: expected {total_len} bytes, got {len(data)}")
        
        payload = data[HEADER_SIZE:total_len]
        remaining = data[total_len:]
        
        frame = cls(
            msg_type=MsgType(msg_type_val),
            seq_num=seq_num,
            nonce=nonce,
            payload=payload,
            flags=flags,
            version=version
        )
        return frame, remaining

def build_deterministic_nonce(node_id: int, seq_num: int) -> bytes:
    """
    Construct a 96-bit (12-byte) deterministic nonce for AES-GCM:
    4 bytes Node ID + 8 bytes Sequence Number.
    """
    return struct.pack("!IQ", node_id & 0xFFFFFFFF, seq_num & 0xFFFFFFFFFFFFFFFF)
