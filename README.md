# AEGIS-PQ: Inline Post-Quantum Cryptographic Offload Engine
## Tactical Gateway for Legacy Infrastructure & Cyber-Physical Systems

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-18%2F18%20passing-success)
![Hardware Target](https://img.shields.io/badge/target-Tul%20PYNQ--Z2%20(Zynq--7000)-orange)
![Crypto Standard](https://img.shields.io/badge/PQC-NIST%20FIPS%20203%20ML--KEM--512-blue)
![AEAD](https://img.shields.io/badge/AEAD-AES--256--GCM-blueviolet)

---

## 1. Project Overview & Mission

**AEGIS-PQ** is an inline post-quantum cryptographic offload engine engineered to safeguard legacy enterprise networks and cyber-physical infrastructure (e.g., hospital DICOM medical scanners, SCADA electrical substations, industrial PLCs) from **Harvest-Now, Decrypt-Later (HNDL)** quantum threats.

Legacy endpoints frequently run on certified embedded systems or microcontrollers that cannot execute lattice-based post-quantum cryptography natively due to strict compute, memory, and regulatory re-certification barriers. AEGIS-PQ acts as a bump-in-the-wire transparent hardware/software gateway that encapsulates unencrypted legacy streams into authenticated, quantum-resistant envelopes using **NIST FIPS 203 ML-KEM-512**, **RFC 5869 HKDF-SHA256**, and **NIST SP 800-38D AES-256-GCM**.

---

## 2. System Architecture & Workload Partitioning

To strictly respect the **5.4 MB available root filesystem constraint** on the Tul PYNQ-Z2 board, workloads are partitioned:

1. **Host Workstation (`192.168.0.5`):**
   - **CY · FOCUS Tactical Operations Web Dashboard** (Port 8000).
   - **Mode A Legacy Receiver Service** (Port 5558).
   - **Mode B Secure APBP-v1 Receiver Service** (Port 5556).
   - **Full-Stack REST Backend** (`src/backend/app.py`).
2. **PYNQ-Z2 Hardware Node (`192.168.0.2`):**
   - **Ultra-lightweight Zero-Install Daemon** (`/dev/shm/aegis_pynq_daemon.py`, `<4.0 KB`).
   - Xilinx Zynq-7000 XC7Z020-1CLG400C SoC with 50.0 MHz PL clock.
   - `kyber_accelerator_top:1.0` IP at `0x40000000` via `axi_dma:7.1` Direct Register Mode DMA.
   - **Resident Dashboard Preservation:** Port 5000 (`app.py`) and Jupyter (Port 9090) remain preserved.
3. **Legacy Sender (`192.168.0.3` / Local Test Client):**
   - Transmits either unencrypted Mode A direct legacy streams or Mode B post-quantum encapsulated envelopes.

---

## 3. Two Transfer Modes: Direct vs. AEGIS-PQ

| Parameter | Mode A: Direct Legacy Transfer | Mode B: AEGIS-PQ Secure Transfer |
|:---|:---|:---|
| **Route** | Direct TCP connection to Port 5558 | Encapsulated APBP-v1 socket to Port 5556 |
| **Key Establishment** | None (Plaintext transmission) | **NIST FIPS 203 ML-KEM-512** (800B ek, 768B c) |
| **Session KDF** | None | **RFC 5869 HKDF-SHA256** (32B AES + 32B Aux) |
| **Payload Encryption** | None (Vulnerable to passive eavesdropping) | **NIST SP 800-38D AES-256-GCM** |
| **Integrity & Replay** | None | 128-bit GHASH tag + 1024 sliding-window replay filter |
| **Measured Latency** | Median: **14.25 ms** (Min: 1.89 ms, Max: 24.77 ms) | Median: **30.20 ms** (Min: 11.26 ms, Max: 45.91 ms) |
| **Security Verdict** | **Vulnerable to HNDL & Tamper** | **Quantum Resistant & Authenticated** |

---

## 4. Hardware Accelerator & Grounded Reality

- **FPGA Microarchitecture**: Forward Cooley-Tukey NTT $\to$ Pointwise Multiplier ($FIXED\_SECRET = 3$) $\to$ Inverse Gentleman-Sande iNTT on Artix-7 PL fabric at 50.0 MHz.
- **Audited Reality**: The existing hardware bitstream (`design_1.bit`) is an **isolated polynomial arithmetic accelerator**, *not* an autonomous ML-KEM implementation.
- **Speedup Grounding**: The reported **27.1x speedup** (1.19 ms vs 32.26 ms) represents the empirical ratio between the FPGA AXI DMA streaming pipeline and unvectorized, interpreted Python executing on the ARM Cortex-A9 CPU for 1000 polynomial transformations.

---

## 5. Getting Started & How to Run

### Prerequisites
- Python 3.8+ (tested on Python 3.8, 3.12, 3.13)
- `cryptography >= 2.8`
- `paramiko`
- `flask`
- `numpy`

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Raja-sys77/AEGIS-pq.git
   cd AEGIS-pq
   ```

2. **Run all automated tests (18 tests):**
   ```bash
   python -m unittest discover tests
   ```

3. **Start the CY · FOCUS Operations Platform & Backend:**
   ```bash
   python src/backend/app.py
   ```
   Open your browser to: **`http://localhost:8000`**

---

## 6. Project Structure

```text
├── deploy/
│   └── deployment_manifest.md      # PYNQ-Z2 zero-install RAM deployment manifest
├── docs/
│   ├── development/
│   │   └── continuous_integration_log.md  # Chronological Git commit audit ledger
│   └── reconnaissance/             # 13 technical audit reports (00 to 12)
├── src/
│   ├── backend/
│   │   ├── app.py                  # Full-Stack Flask REST API & UI engine
│   │   ├── legacy_receiver.py      # Mode A Direct Legacy listener (Port 5558)
│   │   ├── secure_receiver.py      # Mode B AEGIS-PQ APBP-v1 listener (Port 5556)
│   │   └── transfer_client.py      # Dual-mode socket transmission client
│   ├── common/
│   │   └── protocol.py             # APBP-v1 36-byte length-prefixed binary framing
│   ├── crypto/
│   │   ├── aead_cipher.py          # AES-256-GCM cipher with replay window
│   │   ├── hkdf_kdf.py             # RFC 5869 HKDF-SHA256 session expansion
│   │   └── mlkem512.py             # Pure-Python NIST FIPS 203 ML-KEM-512 core
│   ├── frontend/
│   │   ├── static/css/cyfocus.css  # CY · FOCUS tactical dark CSS tokens
│   │   ├── static/js/cyfocus.js    # Reactive UI & real-time transfer logic
│   │   └── templates/index.html    # Single-page operations dashboard
│   ├── pynq/
│   │   ├── aegis_pynq_daemon.py    # Zero-disk in-memory hardware daemon
│   │   └── pynq_client.py          # SSH & RPC hardware client adapter
│   └── redteam/
│       └── redteam_suite.py        # Pollard's rho & Shor's algorithm demonstrator
└── tests/
    ├── test_api.py                 # REST endpoint integration tests
    ├── test_crypto.py              # ML-KEM-512, HKDF, AEAD unit tests
    ├── test_redteam.py             # Quantum threat & tamper rejection tests
    └── test_transfers.py           # Mode A & Mode B end-to-end socket tests
```

---

## 7. License
Licensed under the Apache License, Version 2.0.
