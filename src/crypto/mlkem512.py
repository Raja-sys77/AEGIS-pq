"""
AEGIS-PQ Cryptographic Engine: ML-KEM-512 (NIST FIPS 203) Pure-Python Reference
Implements the Module-Lattice-Based Key-Encapsulation Mechanism standard.

Parameters (ML-KEM-512 / Kyber512):
- Modulus q = 3329
- Degree n = 256
- Module rank k = 2
- Noise parameter eta_1 = 3 (KeyGen)
- Noise parameter eta_2 = 2 (Encaps)
- Compression parameter d_u = 10, d_v = 4
- Public key size (ek): 800 bytes
- Ciphertext size (c): 768 bytes
- Secret key size (dk): 1632 bytes
- Shared secret size (K): 32 bytes (256 bits)
"""

import os
import hashlib
from typing import Tuple, List

Q = 3329
N = 256
K = 2
ETA1 = 3
ETA2 = 2
DU = 10
DV = 4
ZETA = 17

def _shake128(data: bytes, out_len: int) -> bytes:
    h = hashlib.shake_128()
    h.update(data)
    return h.digest(out_len)

def _shake256(data: bytes, out_len: int) -> bytes:
    h = hashlib.shake_256()
    h.update(data)
    return h.digest(out_len)

def _sha3_256(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()

def _sha3_512(data: bytes) -> bytes:
    return hashlib.sha3_512(data).digest()

def _bit_rev_7(r: int) -> int:
    res = 0
    for _ in range(7):
        res = (res << 1) | (r & 1)
        r >>= 1
    return res

# Precompute zetas and base_zetas
_ZETAS = [pow(ZETA, _bit_rev_7(i), Q) for i in range(128)]
_BASE_ZETAS = [pow(ZETA, 2 * _bit_rev_7(i) + 1, Q) for i in range(128)]
_INV2 = (Q + 1) // 2  # 1665 = 2^-1 mod Q

def ntt_poly(p: List[int]) -> List[int]:
    """Forward NTT for degree 256 polynomial modulo 3329"""
    r = list(p)
    k = 1
    length = 128
    while length >= 2:
        start = 0
        while start < 256:
            z = _ZETAS[k]
            k += 1
            for j in range(start, start + length):
                t = (z * r[j + length]) % Q
                r[j + length] = (r[j] - t) % Q
                r[j] = (r[j] + t) % Q
            start += 2 * length
        length //= 2
    return r

def intt_poly(r: List[int]) -> List[int]:
    """Inverse NTT for degree 256 polynomial modulo 3329"""
    a = list(r)
    length = 2
    while length <= 128:
        num_blocks = 128 // length
        start = 0
        for b in range(num_blocks):
            k = num_blocks + b
            z = _ZETAS[k]
            inv_zeta = pow(z, Q - 2, Q)
            for j in range(start, start + length):
                A = a[j]
                B = a[j + length]
                u = ((A + B) * _INV2) % Q
                v = ((A - B) * _INV2 * inv_zeta) % Q
                a[j] = u
                a[j + length] = v
            start += 2 * length
        length *= 2
    return a

def poly_mul_ntt(p1_ntt: List[int], p2_ntt: List[int]) -> List[int]:
    """Pointwise polynomial multiplication in NTT domain with baseline quadratic factor multiplication"""
    res = [0] * 256
    for i in range(128):
        a0 = p1_ntt[2 * i]
        a1 = p1_ntt[2 * i + 1]
        b0 = p2_ntt[2 * i]
        b1 = p2_ntt[2 * i + 1]
        z = _BASE_ZETAS[i]
        res[2 * i] = (a0 * b0 + a1 * b1 % Q * z) % Q
        res[2 * i + 1] = (a0 * b1 + a1 * b0) % Q
    return res

def poly_add(p1: List[int], p2: List[int]) -> List[int]:
    return [(a + b) % Q for a, b in zip(p1, p2)]

def poly_sub(p1: List[int], p2: List[int]) -> List[int]:
    return [(a - b) % Q for a, b in zip(p1, p2)]

def parse_uniform(stream: bytes) -> List[int]:
    """Rejection sampling for uniform distribution in [0, Q-1]"""
    coeffs = []
    i = 0
    while len(coeffs) < 256 and i + 2 <= len(stream):
        d1 = stream[i] | ((stream[i + 1] & 0x0F) << 8)
        d2 = (stream[i + 1] >> 4) | (stream[i + 2] << 4) if i + 2 < len(stream) else 4000
        i += 3
        if d1 < Q:
            coeffs.append(d1)
        if len(coeffs) < 256 and d2 < Q:
            coeffs.append(d2)
    while len(coeffs) < 256:
        coeffs.append(0)
    return coeffs

def cbd2(stream: bytes) -> List[int]:
    """Centered Binomial Distribution CBD_2 sampling"""
    coeffs = []
    for b in stream[:128]:
        t0 = (b >> 0) & 1
        t1 = (b >> 1) & 1
        t2 = (b >> 2) & 1
        t3 = (b >> 3) & 1
        coeffs.append((t0 + t1 - t2 - t3) % Q)
        t4 = (b >> 4) & 1
        t5 = (b >> 5) & 1
        t6 = (b >> 6) & 1
        t7 = (b >> 7) & 1
        coeffs.append((t4 + t5 - t6 - t7) % Q)
    while len(coeffs) < 256:
        coeffs.append(0)
    return coeffs[:256]

def cbd3(stream: bytes) -> List[int]:
    """Centered Binomial Distribution CBD_3 sampling"""
    coeffs = []
    i = 0
    while len(coeffs) < 256 and i + 3 <= len(stream):
        val = stream[i] | (stream[i+1] << 8) | (stream[i+2] << 16)
        i += 3
        for s in range(4):
            chunk = (val >> (s * 6)) & 0x3F
            a = ((chunk >> 0) & 1) + ((chunk >> 1) & 1) + ((chunk >> 2) & 1)
            b = ((chunk >> 3) & 1) + ((chunk >> 4) & 1) + ((chunk >> 5) & 1)
            coeffs.append((a - b) % Q)
    while len(coeffs) < 256:
        coeffs.append(0)
    return coeffs[:256]

def encode_poly_12(p: List[int]) -> bytes:
    """Encode degree 256 polynomial (12 bits per coefficient) -> 384 bytes"""
    out = bytearray(384)
    for i in range(128):
        c0 = p[2 * i] % Q
        c1 = p[2 * i + 1] % Q
        out[3 * i] = c0 & 0xFF
        out[3 * i + 1] = ((c0 >> 8) & 0x0F) | ((c1 & 0x0F) << 4)
        out[3 * i + 2] = (c1 >> 4) & 0xFF
    return bytes(out)

def decode_poly_12(b: bytes) -> List[int]:
    """Decode 384 bytes -> degree 256 polynomial"""
    p = [0] * 256
    for i in range(128):
        b0 = b[3 * i]
        b1 = b[3 * i + 1]
        b2 = b[3 * i + 2]
        p[2 * i] = b0 | ((b1 & 0x0F) << 8)
        p[2 * i + 1] = (b1 >> 4) | (b2 << 4)
    return p

def compress_poly(p: List[int], d: int) -> List[int]:
    div = 1 << d
    return [((c * div + (Q // 2)) // Q) % div for c in p]

def decompress_poly(p: List[int], d: int) -> List[int]:
    div = 1 << d
    return [((c * Q + (div // 2)) // div) % Q for c in p]

def encode_poly_compressed(p: List[int], d: int) -> bytes:
    if d == 10:
        out = bytearray(320)
        for i in range(64):
            c = [p[4 * i + j] & 0x3FF for j in range(4)]
            out[5 * i + 0] = c[0] & 0xFF
            out[5 * i + 1] = ((c[0] >> 8) & 0x03) | ((c[1] & 0x3F) << 2)
            out[5 * i + 2] = ((c[1] >> 6) & 0x0F) | ((c[2] & 0x0F) << 4)
            out[5 * i + 3] = ((c[2] >> 4) & 0x3F) | ((c[3] & 0x03) << 6)
            out[5 * i + 4] = (c[3] >> 2) & 0xFF
        return bytes(out)
    elif d == 4:
        out = bytearray(128)
        for i in range(128):
            out[i] = (p[2 * i] & 0x0F) | ((p[2 * i + 1] & 0x0F) << 4)
        return bytes(out)
    raise ValueError(f"Unsupported d={d}")

def decode_poly_compressed(b: bytes, d: int) -> List[int]:
    p = [0] * 256
    if d == 10:
        for i in range(64):
            b0, b1, b2, b3, b4 = b[5*i:5*i+5]
            p[4*i + 0] = b0 | ((b1 & 0x03) << 8)
            p[4*i + 1] = (b1 >> 2) | ((b2 & 0x0F) << 6)
            p[4*i + 2] = (b2 >> 4) | ((b3 & 0x3F) << 4)
            p[4*i + 3] = (b3 >> 6) | (b4 << 2)
        return p
    elif d == 4:
        for i in range(128):
            byte_val = b[i]
            p[2*i] = byte_val & 0x0F
            p[2*i + 1] = (byte_val >> 4) & 0x0F
        return p
    raise ValueError(f"Unsupported d={d}")


class MLKEM512:
    """
    Module-Lattice-Based Key Encapsulation Mechanism (ML-KEM-512)
    FIPS 203 Reference Implementation.
    """

    @classmethod
    def keygen(cls) -> Tuple[bytes, bytes]:
        """
        Generates (encapsulation_key, decapsulation_key).
        ek size: 800 bytes
        dk size: 1632 bytes
        """
        d = os.urandom(32)
        z = os.urandom(32)

        h = hashlib.sha3_512(d).digest()
        rho, sigma = h[:32], h[32:]

        A = [[None for _ in range(K)] for _ in range(K)]
        for i in range(K):
            for j in range(K):
                seed_ij = rho + bytes([j, i])
                stream = _shake128(seed_ij, 800)
                A[i][j] = parse_uniform(stream)

        s = []
        e = []
        for i in range(K):
            stream_s = _shake256(sigma + bytes([i]), 192)
            s.append(cbd3(stream_s))
            stream_e = _shake256(sigma + bytes([K + i]), 192)
            e.append(cbd3(stream_e))

        s_ntt = [ntt_poly(s[i]) for i in range(K)]

        t = []
        for i in range(K):
            acc = [0] * N
            for j in range(K):
                prod = poly_mul_ntt(A[i][j], s_ntt[j])
                acc = poly_add(acc, prod)
            e_ntt = ntt_poly(e[i])
            t_poly = poly_add(acc, e_ntt)
            t.append(t_poly)

        ek = encode_poly_12(t[0]) + encode_poly_12(t[1]) + rho
        assert len(ek) == 800, f"Expected ek len 800, got {len(ek)}"

        s_bytes = encode_poly_12(s_ntt[0]) + encode_poly_12(s_ntt[1])
        h_ek = _sha3_256(ek)
        dk = s_bytes + ek + h_ek + z
        assert len(dk) == 1632, f"Expected dk len 1632, got {len(dk)}"

        return ek, dk

    @classmethod
    def encaps(cls, ek: bytes) -> Tuple[bytes, bytes]:
        """
        Given public encapsulation key ek (800 bytes):
        Returns (ciphertext (768 bytes), shared_secret (32 bytes)).
        """
        if len(ek) != 800:
            raise ValueError(f"Invalid ek length: {len(ek)}")
        
        m = os.urandom(32)
        h_ek = _sha3_256(ek)
        kr = hashlib.sha3_512(m + h_ek).digest()
        k_secret, r = kr[:32], kr[32:]

        t0 = decode_poly_12(ek[:384])
        t1 = decode_poly_12(ek[384:768])
        rho = ek[768:800]
        t = [t0, t1]

        A_T = [[None for _ in range(K)] for _ in range(K)]
        for i in range(K):
            for j in range(K):
                seed_ij = rho + bytes([i, j])
                stream = _shake128(seed_ij, 800)
                A_T[i][j] = parse_uniform(stream)

        r_vec = []
        for i in range(K):
            stream_r = _shake256(r + bytes([i]), 128)
            r_vec.append(cbd2(stream_r))

        e1 = []
        for i in range(K):
            stream_e1 = _shake256(r + bytes([K + i]), 128)
            e1.append(cbd2(stream_e1))

        stream_e2 = _shake256(r + bytes([2 * K]), 128)
        e2 = cbd2(stream_e2)

        r_ntt = [ntt_poly(r_vec[i]) for i in range(K)]

        u = []
        for i in range(K):
            acc = [0] * N
            for j in range(K):
                prod = poly_mul_ntt(A_T[i][j], r_ntt[j])
                acc = poly_add(acc, prod)
            inv_acc = intt_poly(acc)
            u.append(poly_add(inv_acc, e1[i]))

        acc_v = [0] * N
        for j in range(K):
            prod = poly_mul_ntt(t[j], r_ntt[j])
            acc_v = poly_add(acc_v, prod)
        v = poly_add(intt_poly(acc_v), e2)

        m_poly = [0] * 256
        for byte_idx in range(32):
            b_val = m[byte_idx]
            for bit_idx in range(8):
                if (b_val >> bit_idx) & 1:
                    m_poly[8 * byte_idx + bit_idx] = 1665

        v = poly_add(v, m_poly)

        u_comp = [compress_poly(u[i], DU) for i in range(K)]
        v_comp = compress_poly(v, DV)

        c = encode_poly_compressed(u_comp[0], DU) + encode_poly_compressed(u_comp[1], DU) + encode_poly_compressed(v_comp, DV)
        assert len(c) == 768, f"Expected ciphertext len 768, got {len(c)}"

        shared_secret = _sha3_256(k_secret + _sha3_256(c))
        return c, shared_secret

    @classmethod
    def decaps(cls, c: bytes, dk: bytes) -> bytes:
        """
        Given ciphertext c (768 bytes) and decapsulation key dk (1632 bytes):
        Performs Fujisaki-Okamoto transform and implicit rejection.
        Returns 32-byte shared secret.
        """
        if len(c) != 768:
            raise ValueError(f"Invalid ciphertext length: {len(c)}")
        if len(dk) != 1632:
            raise ValueError(f"Invalid decapsulation key length: {len(dk)}")

        s0_ntt = decode_poly_12(dk[:384])
        s1_ntt = decode_poly_12(dk[384:768])
        s_ntt = [s0_ntt, s1_ntt]
        ek = dk[768:1568]
        h_ek = dk[1568:1600]
        z = dk[1600:1632]

        u0_comp = decode_poly_compressed(c[:320], DU)
        u1_comp = decode_poly_compressed(c[320:640], DU)
        v_comp = decode_poly_compressed(c[640:768], DV)

        u = [decompress_poly(u0_comp, DU), decompress_poly(u1_comp, DU)]
        v = decompress_poly(v_comp, DV)

        u_ntt = [ntt_poly(u[i]) for i in range(K)]

        acc = [0] * N
        for i in range(K):
            prod = poly_mul_ntt(s_ntt[i], u_ntt[i])
            acc = poly_add(acc, prod)
        w = poly_sub(v, intt_poly(acc))

        m_bytes = bytearray(32)
        for byte_idx in range(32):
            val = 0
            for bit_idx in range(8):
                coeff = w[8 * byte_idx + bit_idx] % Q
                dist0 = min(coeff, Q - coeff)
                dist1 = abs(coeff - 1665)
                if dist1 < dist0:
                    val |= (1 << bit_idx)
            m_bytes[byte_idx] = val
        m_prime = bytes(m_bytes)

        kr = hashlib.sha3_512(m_prime + h_ek).digest()
        k_prime, r_prime = kr[:32], kr[32:]

        t0 = decode_poly_12(ek[:384])
        t1 = decode_poly_12(ek[384:768])
        rho = ek[768:800]
        t = [t0, t1]

        A_T = [[None for _ in range(K)] for _ in range(K)]
        for i in range(K):
            for j in range(K):
                seed_ij = rho + bytes([i, j])
                stream = _shake128(seed_ij, 800)
                A_T[i][j] = parse_uniform(stream)

        r_vec = []
        for i in range(K):
            stream_r = _shake256(r_prime + bytes([i]), 128)
            r_vec.append(cbd2(stream_r))

        e1 = []
        for i in range(K):
            stream_e1 = _shake256(r_prime + bytes([K + i]), 128)
            e1.append(cbd2(stream_e1))

        stream_e2 = _shake256(r_prime + bytes([2 * K]), 128)
        e2 = cbd2(stream_e2)

        r_ntt = [ntt_poly(r_vec[i]) for i in range(K)]

        u_cand = []
        for i in range(K):
            acc_c = [0] * N
            for j in range(K):
                prod = poly_mul_ntt(A_T[i][j], r_ntt[j])
                acc_c = poly_add(acc_c, prod)
            inv_acc = intt_poly(acc_c)
            u_cand.append(poly_add(inv_acc, e1[i]))

        acc_vc = [0] * N
        for j in range(K):
            prod = poly_mul_ntt(t[j], r_ntt[j])
            acc_vc = poly_add(acc_vc, prod)
        v_cand = poly_add(intt_poly(acc_vc), e2)

        m_poly_cand = [0] * 256
        for byte_idx in range(32):
            b_val = m_prime[byte_idx]
            for bit_idx in range(8):
                if (b_val >> bit_idx) & 1:
                    m_poly_cand[8 * byte_idx + bit_idx] = 1665
        v_cand = poly_add(v_cand, m_poly_cand)

        u_comp_cand = [compress_poly(u_cand[i], DU) for i in range(K)]
        v_comp_cand = compress_poly(v_cand, DV)
        c_prime = encode_poly_compressed(u_comp_cand[0], DU) + encode_poly_compressed(u_comp_cand[1], DU) + encode_poly_compressed(v_comp_cand, DV)

        if c == c_prime:
            return _sha3_256(k_prime + _sha3_256(c))
        else:
            return _sha3_256(z + _sha3_256(c))
