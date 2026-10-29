"""
AEGIS-PQ Cryptographic Engine: Authenticated Encryption with Associated Data (AEAD)
Implements NIST SP 800-38D AES-256-GCM with replay protection sliding window.
"""

import os
from typing import Optional, Set
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class ReplayProtectionWindow:
    """
    Sliding window replay protection filter for packet sequence numbers.
    Maintains the highest seen sequence number and a bitmask/set of received sequences.
    """
    def __init__(self, window_size: int = 1024):
        self.window_size = window_size
        self.max_seq: int = -1
        self.seen_seqs: Set[int] = set()

    def check_and_update(self, seq_num: int) -> bool:
        """
        Returns True if sequence number is valid and fresh.
        Returns False if sequence number is a replay or too old.
        """
        if seq_num < 0:
            return False
            
        if self.max_seq == -1:
            self.max_seq = seq_num
            self.seen_seqs.add(seq_num)
            return True

        if seq_num > self.max_seq:
            # Advance window
            self.max_seq = seq_num
            self.seen_seqs.add(seq_num)
            # Evict sequences outside sliding window
            cutoff = self.max_seq - self.window_size
            self.seen_seqs = {s for s in self.seen_seqs if s > cutoff}
            return True

        # seq_num <= self.max_seq
        if seq_num in self.seen_seqs:
            # Replay detected
            return False
        
        if seq_num <= self.max_seq - self.window_size:
            # Sequence is too old
            return False

        self.seen_seqs.add(seq_num)
        return True


class AEGISAEADCipher:
    """
    AES-256-GCM cipher wrapper with automatic authentication tag handling
    and Associated Data (AD) binding.
    """
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError(f"AES-256 key must be exactly 32 bytes, got {len(key)}")
        self.key = key
        self.aesgcm = AESGCM(key)
        self.replay_filter = ReplayProtectionWindow()

    def encrypt(self, nonce: bytes, plaintext: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Encrypts plaintext with AES-256-GCM using the 12-byte nonce.
        Appends the 16-byte GHASH authentication tag directly to ciphertext.
        """
        if len(nonce) != 12:
            raise ValueError(f"AES-GCM nonce must be 12 bytes, got {len(nonce)}")
        return self.aesgcm.encrypt(nonce, plaintext, associated_data)

    def decrypt(self, nonce: bytes, ciphertext_with_tag: bytes, associated_data: Optional[bytes] = None, seq_num: Optional[int] = None) -> bytes:
        """
        Decrypts and authenticates ciphertext_with_tag.
        If seq_num is provided, validates replay protection.
        Raises InvalidTag from cryptography if authentication fails.
        Raises ValueError if replay attack is detected.
        """
        if seq_num is not None:
            if not self.replay_filter.check_and_update(seq_num):
                raise ValueError(f"Replay attack detected or sequence too old: seq_num={seq_num}")

        if len(nonce) != 12:
            raise ValueError(f"AES-GCM nonce must be 12 bytes, got {len(nonce)}")
        
        return self.aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data)
