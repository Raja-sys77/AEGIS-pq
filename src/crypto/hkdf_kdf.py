"""
AEGIS-PQ Cryptographic Engine: RFC 5869 HKDF-SHA256
Derives symmetric cryptographic keys from an established PQC shared secret.
"""

from typing import Tuple, Optional
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

AEGIS_SESSION_INFO = b"AEGIS-PQ-SESSION-v1"

def derive_session_keys(shared_secret: bytes, salt: Optional[bytes] = None, info: bytes = AEGIS_SESSION_INFO) -> Tuple[bytes, bytes]:
    """
    Given a 32-byte shared secret (from ML-KEM-512 decapsulation/encapsulation),
    derives a 32-byte AES-256 key and a 32-byte MAC/verification subkey using HKDF-SHA256.
    
    Output:
    (aes_key_32B, aux_key_32B)
    """
    if len(shared_secret) != 32:
        raise ValueError(f"Shared secret must be 32 bytes, got {len(shared_secret)}")
    
    # Expand 64 bytes total: 32 bytes for AES-256-GCM, 32 bytes for auxiliary integrity checks
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=salt if salt is not None else b"\x00" * 32,
        info=info,
        backend=default_backend()
    )
    key_material = hkdf.derive(shared_secret)
    aes_key = key_material[:32]
    aux_key = key_material[32:]
    return aes_key, aux_key
