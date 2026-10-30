"""
AEGIS-PQ Wire Protocol Definition (APBP-v1)
AEGIS-PQ Bump-in-the-wire Protocol version 1

Binary Header Specification (36 Bytes Total, Big-Endian):
- Magic (4 bytes): 0x41 0x45 0x47 0x53 ('AEGS')
- Version (2 bytes): 0x00 0x01
- Message Type (2 bytes)
- Sequence Number (8 bytes)
- Nonce / IV (12 bytes)
- Payload Length (4 bytes)
- Reserved / Flags (4 bytes)
"""

import struct
from enum import IntEnum
from typing import Tuple, Optional

APBP_MAGIC = b"AEGS"
APBP_VERSION = 1

# Explicit 36-byte header packing:
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
    def unpack_header(cls, header_bytes: bytes) -> Tuple[int, int, int, bytes, int, int]:
        """
        Unpack just the 36-byte header.
        Returns: (version, msg_type, seq_num, nonce, payload_len, flags)
        """
        if len(header_bytes) < HEADER_SIZE:
            raise ValueError(f"Header length {len(header_bytes)} < {HEADER_SIZE}")
        magic, version, msg_type_val, seq_num, nonce, payload_len, flags = HEADER_STRUCT.unpack(header_bytes[:HEADER_SIZE])
        if magic != APBP_MAGIC:
            raise ValueError(f"Invalid APBP magic bytes: {magic!r}")
        if version != APBP_VERSION:
            raise ValueError(f"Unsupported APBP version: {version}")
        return version, msg_type_val, seq_num, nonce, payload_len, flags

    @classmethod
    def unpack(cls, data: bytes) -> Tuple["APBPFrame", bytes]:
        """
        Unpack a single APBPFrame from raw bytes.
        Returns (frame, remaining_bytes).
        """
        version, msg_type_val, seq_num, nonce, payload_len, flags = cls.unpack_header(data)
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
