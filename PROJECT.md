# AEGIS-PQ — Autonomous Inline Post-Quantum Cryptographic Offload Engine
## Master Architectural Blueprint & System Specification

**Document Version:** 1.1.0  
**Classification:** Technical Specification & Project Blueprint  
**Target Repository:** `https://github.com/Raja-sys77/AEGIS-pq`  
**Physical Target Hardware:** Tul PYNQ-Z2 (Xilinx Zynq-7000 XC7Z020-1CLG400C SoC)  
**Host & Red-Team Station:** Dual-Role Workstation (`192.168.0.5`)  
**Network Deployment Subnet:** `192.168.0.0/24` (Direct Ethernet / Bridged Wi-Fi)  
**UI Design Paradigm:** CY · FOCUS Dense Cybersecurity Operations Platform  

---

## 1. Executive Summary & Architectural Overview

The **AEGIS-PQ** project delivers an authentic, bump-in-the-wire post-quantum cryptographic (PQC) offload gateway engineered to protect legacy enterprise and industrial endpoints from Harvest-Now, Decrypt-Later (HNDL) quantum threats. Legacy cyber-physical infrastructure—including SCADA controllers, electrical substations, and FDA-cleared DICOM medical imaging scanners—cannot execute computationally intensive lattice cryptography due to severe processor, memory, and firmware re-certification constraints.

AEGIS-PQ transparently intercepts legacy unencrypted or classically secured network traffic, encapsulates it using NIST FIPS 203 (ML-KEM-512) lattice-based key encapsulation accelerated in programmable logic (PL), derives ephemeral session keys via RFC 5869 HKDF-SHA256, and encapsulates payloads within NIST SP 800-38D AES-256-GCM authenticated frames.

### 1.1 Architectural Topology & Storage-Constrained Workload Distribution

To strictly respect the **5.4 MB available root filesystem constraint** on the PYNQ-Z2 board, the full-stack architecture cleanly partitions workloads across physical nodes:

1. **Host Workstation (`192.168.0.5`):**
   - Hosts the **CY · FOCUS Frontend Web Interface** and the **Full-Stack Backend API Server**.
   - Handles all web tooling, UI asset rendering, heavy data storage, long-term event logging, and red-team cryptanalysis suites.
   - Eliminates any requirement for `node_modules`, npm, Webpack, or heavy dependencies on the embedded board.
2. **PYNQ-Z2 Hardware Node (`192.168.0.2`):**
   - Executes strictly an ultra-lightweight, zero-install in-memory **AEGIS Runtime Daemon** (`aegis_pynq_daemon.py`).
   - Interacts directly with the Artix-7 FPGA fabric via AXI DMA and the pre-synthesized `kyber_accelerator_top_0` IP.
   - Maintains zero disk writes to root flash, storing telemetry in memory queues and streaming directly over network sockets.
3. **Legacy Endpoint (`192.168.0.3` / Host Mock):**
   - Transmits standard legacy streams (DICOM medical scan tiles or SCADA telemetry) to the PYNQ-Z2 ingress listener.

```mermaid
graph TB
    subgraph Node1 ["Node 1: Legacy Client (Naved's Laptop / Mock)"]
        N1_App["Unmodified Legacy Client<br/>(DICOM Images / SCADA Stream)"]
        N1_Mock["Automated Client Mock<br/>(Byte-Identical Generator)"]
    end

    subgraph Node2 ["Node 2: AEGIS-PQ Hardware Gateway (PYNQ-Z2: 192.168.0.2)"]
        N2_Ingress["Legacy Ingress Listener (Port 5555)"]
        subgraph PYNQ_Runtime ["Ultra-Lightweight In-Memory Daemon (Zero Disk Installs)"]
            N2_Daemon["aegis_pynq_daemon.py<br/>(Python 3.8 + cryptography 2.8)"]
            N2_Watchdog["AXI DMA Watchdog (3.0s Timeout Protection)"]
            N2_MemQueue["In-Memory Telemetry Ring Buffer (Zero Flash Writes)"]
        end
        subgraph PL_Fabric ["Programmable Logic (Artix-7 FPGA @ 100MHz)"]
            PL_DMA["AXI DMA (axi_dma_0 @ 0x41E00000)"]
            PL_NTT["kyber_accelerator_top_0 (@ 0x40000000)<br/>Forward Cooley-Tukey NTT (256 mod 3329)<br/>Pointwise Multiplier (FIXED_SECRET = 3)<br/>Inverse Gentleman-Sande iNTT"]
        end
        N2_Egress["APBP-v1 Egress Client (Port 5556)"]
        N2_API_Agent["PYNQ RPC / Telemetry Agent (Port 5557)"]

        N2_Ingress --> N2_Daemon
        N2_Daemon <== "1024B Direct DMA" ==> PL_DMA
        PL_DMA <== "AXIS Stream" ==> PL_NTT
        N2_Daemon --> N2_Egress
        N2_Daemon --> N2_API_Agent
    end

    subgraph Node3 ["Node 3: Host Workstation (Raja's Laptop: 192.168.0.5)"]
        subgraph Backend_API ["AEGIS-PQ Full-Stack Backend API Server (Port 8000 / 5001)"]
            API_Core["REST API & SSE / WebSocket Engine"]
            API_SysInfo["/api/system/info"]
            API_Crypto["/api/crypto/operations (FIPS 203 + FPGA Status)"]
            API_FPGA["/api/hardware/fpga (Overlay, Clocks, Registers)"]
            API_Sessions["/api/network/sessions (Active Streams, Packets)"]
            API_Telemetry["/api/telemetry/benchmarks (27x Speedup Curves)"]
            API_Security["/api/security/testing (Toy RSA, Shor Sim, Tamper Rejection)"]
            API_Logs["/api/events/logs (Real-Time Forensic Audit Ledger)"]
            
            API_Core --- API_SysInfo
            API_Core --- API_Crypto
            API_Core --- API_FPGA
            API_Core --- API_Sessions
            API_Core --- API_Telemetry
            API_Core --- API_Security
            API_Core --- API_Logs
        end

        subgraph Frontend_UI ["CY · FOCUS Cybersecurity Operations UI (Dense Dark Canvas)"]
            UI_Sidebar["Persistent Operations Sidebar"]
            UI_Metrics["Real-Time Status & Speedup Metric Cards"]
            UI_Recon["64-Tile Live Medical Scan Reassembly Grid"]
            UI_Timeline["Cryptographic Event & Tamper Timeline"]
            UI_Terminal["Interactive Security Testing Console"]
        end

        subgraph Red_Team ["Independent Red-Team & Adversary Suite"]
            RT_Sniffer["Promiscuous Packet Tap & Shannon Entropy (H ≈ 8.0)"]
            RT_Injector["Adversarial Injector (Bit-Flips, Replays, Truncations)"]
            RT_RSA["Toy RSA (32/64/512-bit) Pollard's Rho Benchmark"]
            RT_Shor["Classical Shor's Algorithm Period-Finding Simulator"]
        end

        RecvSocket["APBP-v1 Ingress Listener (Port 5556)"]
        RecvSocket --> API_Core
        API_Core ==> Frontend_UI
        API_Core <--> Red_Team
    end

    N1_App -. "Plaintext TCP Stream" .-> N2_Ingress
    N1_Mock -. "Simulated Stream (Fallback)" .-> N2_Ingress
    N2_Egress == "APBP-v1 Encrypted & Authenticated Stream" ==> RecvSocket
    N2_API_Agent <== "Telemetry Sync" ==> API_Core
    N2_Egress -. "Passive Interception" .-> RT_Sniffer
    RT_Injector -. "Adversarial Frame Injection" .-> RecvSocket
```

---

## 2. Hardware & Cryptographic Engine Specifications

### 2.1 Hardware Platform & FPGA Microarchitecture

| Parameter | Specification | Live Physical Evidence |
|:---|:---|:---|
| **SoC Device** | Xilinx Zynq-7000 XC7Z020-1CLG400C | Tul PYNQ-Z2 Board (`192.168.0.2`), Kernel `5.4.0-xilinx-v2020.2` |
| **Processing System (PS)** | Dual-core ARM Cortex-A9 MPCore @ 666.67 MHz | 512 MB DDR3 Memory (330 MB available), Ubuntu 20.04 LTS |
| **Programmable Logic (PL)** | Artix-7 Equivalent FPGA Fabric | 85,000 Logic Cells, 220 DSP48E1 slices, 4.9 Mb Block RAM |
| **Fabric Clock (`FCLK0`)** | 100.00 MHz (10.0 ns period) | Driven by PS PLL, confirmed in `design_1.hwh` |
| **Hardware Core IP** | `kyber_accelerator_top_0` (v1.0) | Base: `0x40000000`, Range: 64 KB (`PQC Kyber/src/kyber_accelerator.cpp`) |
| **DMA Controller** | `axi_dma_0` (v7.1 Direct Register Mode) | Base: `0x41E00000`, Range: 64 KB, Scatter-Gather Disabled (`C_INCLUDE_SG=0`) |
| **DMA Buffer Format** | 1024 Bytes (256 × 32-bit words, unsigned) | Aligned contiguous physical memory via `pynq.allocate` |
| **PL Arithmetic Scope** | Forward NTT $\to$ Pointwise Multiply $\to$ Inverse NTT | Modulus $q = 3329$, Degree $n = 256$, fixed twiddle factors ($\zeta=17$) |
| **Static Secret Constant** | $FIXED\_SECRET = 3$ | Line 114 `kyber_accelerator.cpp`; computes $y \equiv 3x \pmod{3329}$ |
| **Arithmetic Acceleration** | **27.0x Speedup** over pure-Python ARM CPU | Hardware: 1.19 ms / transform; Pure-Python: 32.26 ms / transform |

### 2.2 Standard Post-Quantum Cryptographic Pipeline

Historical shortcuts—such as repeating raw polynomial coefficients mod 256 as an XOR keystream, or hashing raw NTT outputs—are strictly rejected. The AEGIS-PQ cryptographic pipeline enforces strict mathematical standards:

1. **Key Encapsulation Mechanism (ML-KEM-512 / NIST FIPS 203):**
   - Ring: $R_q = \mathbb{Z}_{3329}[X] / (X^{256} + 1)$, Rank $k = 2$.
   - Noise Samplers: Centered Binomial Distributions $\text{CBD}_3$ ($\eta_1=3$) for KeyGen and $\text{CBD}_2$ ($\eta_2=2$) for Encaps.
   - Public Encapsulation Key ($ek$): 800 bytes; Decapsulation Key ($dk$): 1632 bytes.
   - Ciphertext ($c$): 768 bytes; Shared Secret ($K$): 32 bytes (256 bits).
   - Core Arithmetic Partitioning: Forward and inverse polynomial transforms in $R_q$ offloaded to FPGA PL; hashing (SHAKE128/256), sampling, and Fujisaki-Okamoto verification executed in software.

2. **Session Key Derivation (RFC 5869 HKDF-SHA256):**
   - Pseudorandom Key extraction: $\text{PRK} = \text{HKDF-Extract}(\text{salt}=\text{transcript\_hash}, \text{IKM}=K)$.
   - Session Key expansion: $K_{\text{session}} = \text{HKDF-Expand}(\text{PRK}, \text{info}=\text{"AEGIS-PQ-SESSION-v1"}, L=32)$.

3. **Authenticated Payload Transport (NIST SP 800-38D AES-256-GCM):**
   - Cipher: 256-bit AES in Galois/Counter Mode.
   - Nonce / IV: 96-bit deterministic IV composed of Node Identifier (32 bits) and strictly monotonic Sequence Number (64 bits).
   - Authentication Tag: 128-bit GHASH authentication tag computed over Associated Data (APBP-v1 36-byte header) and ciphertext.
   - Replay Protection: Sliding window filter verifying sequence numbers; frames with duplicates or backward sequence numbers are dropped immediately.

---

## 3. CY · FOCUS Visual Design System & User Interface Architecture

Inspired directly by the high-density tactical interface patterns in workspace references `demo 1.webp` through `demo 5.webp`, the AEGIS-PQ user interface adheres strictly to the **CY · FOCUS** design philosophy. This aesthetic balances dense, information-rich cybersecurity operations telemetry with high-contrast legibility and rapid situational awareness.

### 3.1 Design Tokens & Color Palette

| Token Name | Hex Code | Visual Application & Purpose |
|:---|:---|:---|
| `--color-bg` | `#171615` | Global application deep background canvas |
| `--color-surf1` | `#211E1C` | Primary panel surface, persistent sidebar background |
| `--color-surf2` | `#292421` | Secondary nested container, table header, card body |
| `--color-elev` | `#332722` | Elevated modal, popover, hover state, card highlight |
| `--color-accent` | `#FF4B12` | Primary brand orange accent, active states, CTA buttons |
| `--color-hover` | `#FF652E` | Interactive hover accent state for buttons and links |
| `--color-text1` | `#F5F2EF` | Primary high-contrast readable typography (headers, key metrics) |
| `--color-text2` | `#B8B0AA` | Secondary muted metadata typography (subheadings, units, timestamps) |
| `--color-border` | `#443A34` | Crisp, low-contrast panel borders and structural grid dividers |
| `--color-success`| `#20C997` | Cryptographic verification pass, authentic frames, online status |
| `--color-warning`| `#F5B942` | High latency warning, software CPU fallback active, buffer alert |
| `--color-error`  | `#FF5252` | AEAD MAC tag failure, replay attack dropped, tamper detected |

### 3.2 Responsive Structural Layout

```text
+-----------------------------------------------------------------------------------------------------------+
| AEGIS-PQ :: CY · FOCUS OPS CONSOLE                                          NODE 2: 192.168.0.2 [ONLINE]  |
+-------------------+---------------------------------------------------------------------------------------+
|                   | [ OVERVIEW ]  [ CRYPTO ENGINE ]  [ FPGA HARDWARE ]  [ SESSIONS ]  [ SECURITY AUDIT ]  |
| [LOGO / BRAND]    +---------------------------------------------------------------------------------------+
| AEGIS-PQ v1.1.0   | METRIC CARDS                                                                          |
|                   | +------------------+ +------------------+ +------------------+ +------------------+   |
| [NAVIGATION]      | | HANDSHAKE STATUS | | FPGA ACCELERATION| | PACKETS SECURED  | | ADVERSARIAL DROPS|   |
| > System Overview | | ML-KEM-512 [OK]  | | 27.0x (1.19 ms)  | | 12,480 FRAMES    | | 42 DETECTED [OK] |   |
| > Live Reassembly | +------------------+ +------------------+ +------------------+ +------------------+   |
| > Crypto Metrics  |                                                                                       |
| > FPGA Telemetry  | LIVE PAYLOAD REASSEMBLY (64-TILE MEDICAL SCAN MATRIX)                                 |
| > Red-Team Suite  | +-----------------------------------------------+ +---------------------------------+ |
| > Audit Ledger    | | [TILE 00] [TILE 01] [TILE 02] ... [TILE 07]   | | RECONSTRUCTION METRICS        | |
|                   | | [TILE 08] [TILE 09] [TILE 10] ... [TILE 15]   | | Current Scan: DICOM-SCAN-04   | |
| [HARDWARE STATUS] | |  ...        ...       ...         ...     | | Tiles Received: 64 / 64       | |
| SoC: Zynq-7020    | | [TILE 56] [TILE 57] [TILE 58] ... [TILE 63]   | | Decryption: AES-256-GCM       | |
| PL Clock: 100MHz  | |                                               | | Integrity: 100% Valid MAC     | |
| DMA: Direct Reg   | | [LIVE IMAGE CANVAS 512x512 PIXELS]            | | Reassembly Time: 38.2 ms      | |
| Disk Free: 5.4MB  | +-----------------------------------------------+ +---------------------------------+ |
| (Zero-Install OK) |                                                                                       |
|                   | REAL-TIME CRYPTOGRAPHIC EVENT & SECURITY AUDIT TIMELINE                               |
| [ACTION BUTTON]   | +---------+------------------------+---------------------------------------+--------+ |
| [ RUN RED-TEAM ]  | | TIME    | EVENT TYPE             | SOURCE & DETAILS                      | STATUS | |
| [  INSPECTION  ]  | +---------+------------------------+---------------------------------------+--------+ |
|                   | | 19:30:12| ML-KEM-512 Handshake   | Node 2 -> Node 3 (Shared Secret Est.) | [200 OK| |
| [SYSTEM TIME]     | | 19:30:14| APBP-v1 Tile Frame #42 | Ingress 4096B (Seq: 1042, IV: Valid)  | [VERIF]| |
| 2026-10-30 01:05  | | 19:30:15| Active Bit-Flip Tamper | Red-Team Injector -> Node 3 Ingress   | [DROP] | |
|                   | | 19:30:16| GHASH Tag Mismatch     | Dropped invalid frame (MAC corrupted) | [ALERT]| |
+-------------------+---------------------------------------------------------------------------------------+
```

---

## 4. Full-Stack Backend API Specification (Port 8000 / 5001)

The backend server on Node 3 exposes authentic, live REST and streaming endpoints. Every endpoint surfaces genuine measurements with zero fabricated metrics:

### 4.1 Real Backend API Endpoints

1. **`GET /api/system/info`**
   - Returns host and target node architectures, IP mappings, uptime, OS versions, and storage constraints.
   - Specifically reports PYNQ-Z2 root filesystem available space (5.4 MB) and verifies Zero-Install operational health.

2. **`GET /api/crypto/operations`**
   - Surfaces active cryptographic algorithms: NIST FIPS 203 ML-KEM-512, RFC 5869 HKDF-SHA256, NIST SP 800-38D AES-256-GCM.
   - Reports the operational state of the hybrid engine: pure-Python reference vs. FPGA PL hardware acceleration status via `KyberHAL`.

3. **`GET /api/hardware/fpga`**
   - Telemetry from PYNQ-Z2 PL fabric: overlay loaded (`design_1.bit`), base addresses (`0x40000000` accelerator, `0x41E00000` DMA), fabric clock (100 MHz), DMA watchdog state, and PL temperature.

4. **`GET /api/network/sessions`**
   - Active APBP-v1 network sessions, sequence counter state, ingress/egress frame rates, bandwidth utilization, and link status to Node 1 (`192.168.0.3` / Mock) and Node 2 (`192.168.0.2`).

5. **`GET /api/telemetry/benchmarks`**
   - Rigorous benchmarking data: comparison of FPGA PL transform time (1.19 ms) vs. ARM Cortex-A9 CPU transform time (32.26 ms), demonstrating the verified **27.0x arithmetic speedup**.
   - End-to-end frame processing latency histograms and 64-tile image throughput curves.

6. **`GET /api/security/testing` & `POST /api/security/execute`**
   - Interactive security suite endpoints:
     - Execute Toy RSA Factoring (RSA-32, RSA-64, RSA-128, RSA-256, RSA-512) via Pollard's Rho and compare against ML-KEM lattice security.
     - Execute classical Shor's algorithm period-finding simulation ($N=15, 21, 35$).
     - Trigger active adversarial injection (single bit-flip in ciphertext, replay of previous sequence number, MAC tag truncation) and verify 100% rejection.

7. **`GET /api/events/logs` & `GET /api/events/stream` (SSE)**
   - Continuous forensic event stream logging every cryptographic transition, key generation, frame authentication, and dropped adversarial injection.

---

## 5. Feature Inventory & Milestone Allocation

All 22 core project capabilities are cataloged and allocated across six defined engineering milestones:

| Capability ID | Capability Name | Target Architectural Role | Milestone Assignment | Status Baseline |
|:---|:---|:---|:---|:---|
| **C01** | FPGA Forward NTT | PL Acceleration of Cooley-Tukey polynomial transform | **M0 / M1** | Implemented & Verified in PL |
| **C02** | FPGA Pointwise Multiply (PWM) | Ring arithmetic vector multiplication | **M0 / M1** | Implemented (Fixed $s=3$) |
| **C03** | FPGA Inverse NTT (iNTT) | Gentleman-Sande inverse transform with 3316 scaling | **M0 / M1** | Implemented & Verified in PL |
| **C04** | AXI DMA Transfer Pipeline | 1024-byte zero-copy streaming between PS and PL | **M0 / M1** | Implemented (Direct Mode) |
| **C05** | Montgomery Reduction in Fabric | Modulo 3329 modular reduction ($QINV=-3327, R=2285$) | **M0 / M1** | Implemented in HLS |
| **C06** | Barrett Reduction in Fabric | Constant modular reduction ($v=20159$) | **M0 / M1** | Implemented in HLS |
| **C07** | Pure-Python ML-KEM-512 KeyGen | FIPS 203 compliant public/private key generation | **M1** | Specified (Pure-Python) |
| **C08** | Hybrid ML-KEM-512 Encapsulation | FIPS 203 encapsulation with PL NTT polynomial offload | **M1 / M2** | Specified (Hybrid PS/PL) |
| **C09** | Pure-Python ML-KEM-512 Decaps | FIPS 203 decapsulation with FO transform validation | **M1** | Specified (Pure-Python) |
| **C10** | Software Keccak / SHAKE Engine | PRF & hash operations (SHA3-256, SHAKE128, SHAKE256) | **M1** | Standard Python `hashlib` |
| **C11** | Centered Binomial Sampler (CBD) | Noise sampling ($\text{CBD}_2, \text{CBD}_3$) | **M1** | Software Pure-Python |
| **C12** | Fujisaki-Okamoto (FO) Transform | Re-encryption check and implicit rejection for IND-CCA2 | **M1** | Software Pure-Python |
| **C13** | RFC 5869 HKDF-SHA256 KDF | Cryptographic session key expansion from shared secret | **M1 / M2** | Native in `cryptography 2.8` |
| **C14** | Authenticated AES-256-GCM | Symmetric payload encryption with 128-bit MAC tag | **M1 / M2** | Native in `cryptography 2.8` |
| **C15** | APBP-v1 Binary Wire Framing | Length-prefixed binary framing with 36-byte header | **M2 / M3** | Specified Protocol Contract |
| **C16** | 3-Node Physical / Mock Network | LAN routing across `192.168.0.2`, `.5`, and `.3` | **M0 / M2** | Verified Active Subnet |
| **C17** | Legacy Client Mock (`mock_client`)| Simulates Node 1 64-tile medical scan / SCADA telemetry | **M2** | Automated Python Daemon |
| **C18** | AEGIS-PQ Gateway Daemon | Board-hosted bump-in-the-wire proxy (`aegis_pynq_daemon`)| **M2** | Zero-Install Daemon |
| **C19** | Receiver Telemetry & CY · FOCUS UI | Host Backend API + Dark Ops Dashboard (Port 5001) | **M3** | Full-Stack Web App |
| **C20** | Red-Team HNDL Wiretap (Node 3B) | Promiscuous capture & Shannon entropy verification | **M4** | Python Raw Socket / Scapy |
| **C21** | Active Fault & Tamper Injector | Replay attack, bit-flip, and tag mutilation injector | **M4** | Adversarial Test Harness |
| **C22** | Toy RSA vs. PQC Red-Team Baseline| Factoring benchmark (RSA-32 to 512) & Shor's algorithm | **M4** | Mathematical Demonstrator |

---

## 6. Engineering Milestones & Verification Gates

```mermaid
gantt
    title AEGIS-PQ Phased Implementation Schedule
    dateFormat  YYYY-MM-DD
    section Milestone 0
    Reconnaissance & CI Baseline           :done, m0, 2026-10-29, 2026-10-30
    section Milestone 1
    Mathematical & Cryptographic Core       :active, m1, 2026-10-30, 2026-10-31
    section Milestone 2
    PYNQ-Z2 Zero-Disk Gateway Daemon       :m2, 2026-10-31, 2026-11-01
    section Milestone 3
    CY · FOCUS Full-Stack UI & Telemetry    :m3, 2026-11-01, 2026-11-02
    section Milestone 4
    Red-Team Cryptanalysis & Fault Harness :m4, 2026-11-02, 2026-11-03
    section Milestone 5
    End-to-End Live 3-Node Demonstration   :m5, 2026-11-03, 2026-11-04
```

### Milestone 0: Workspace Reconnaissance, Baseline Audit, and CI Sync (COMPLETED)
- **Objective:** Exhaustive read-only audit of workspace, physical PYNQ-Z2 hardware, network topology, and git synchronization.
- **Deliverables:** Technical reports `00` through `12` in `docs/reconnaissance/`, `PROJECT.md`, `.gitignore`, `docs/development/continuous_integration_log.md`.
- **Exit Gate:** 100% hash verification of bitstream, live board SSH verification, zero modifications to pre-existing code, remote sync to `https://github.com/Raja-sys77/AEGIS-pq`.

### Milestone 1: Mathematical & Protocol Core Engine
- **Objective:** Establish the post-quantum cryptographic primitives, KAT test harnesses, HKDF session expansion, and wire framing logic.
- **Deliverables:**
  - `src/crypto/mlkem512.py`: Pure-Python FIPS 203 ML-KEM-512 implementation (KeyGen, Encaps, Decaps, CBD, NTT, FO transform).
  - `src/crypto/aead_cipher.py`: AES-256-GCM AEAD encryption/decryption with replay protection.
  - `src/crypto/hkdf_kdf.py`: RFC 5869 session derivation engine.
  - `src/common/protocol.py`: APBP-v1 packet parsing, header packing/unpacking, and validation.
  - `tests/test_mlkem_kat.py`: NIST KAT validation test suite.
  - `tests/test_crypto_primitives.py`: Unit tests for AEAD, HKDF, and framing.
- **Exit Gate:** 100% pass on ML-KEM-512 KAT vectors, zero dependencies beyond Python 3 standard library and `cryptography 2.8`.

### Milestone 2: PYNQ-Z2 Zero-Disk Gateway Daemon & Client Mock
- **Objective:** Deploy the bump-in-the-wire hardware gateway daemon on the PYNQ-Z2 board and build the automated legacy client mock.
- **Deliverables:**
  - `src/mock_client/mock_legacy_client.py`: Multi-modal generator (64-tile medical scan, SCADA sensor arrays) emitting to Port 5555.
  - `src/gateway/aegis_pynq_daemon.py`: Lightweight gateway running strictly in memory on PYNQ-Z2; intercepts Port 5555, invokes `kyber_hal.py` DMA acceleration, encapsulates payloads via AES-256-GCM, and dispatches APBP-v1 frames to Port 5556.
  - `src/gateway/watchdog.py`: AXI DMA timeout monitor preventing board lockups.
- **Exit Gate:** Continuous execution over 1,000 frames without memory leaks; exactly 0 bytes written to board flash; coexistence with resident port 5000 server.

### Milestone 3: CY · FOCUS Full-Stack UI & Telemetry Engine
- **Objective:** Implement the authorized receiving station, full-stack REST API server, and CY · FOCUS dense cybersecurity web dashboard on Node 3.
- **Deliverables:**
  - `src/backend_api/app.py`: Full-stack Flask REST API + SSE engine serving all seven specified endpoints (`/api/system/info`, `/api/crypto/operations`, `/api/hardware/fpga`, `/api/network/sessions`, `/api/telemetry/benchmarks`, `/api/security/testing`, `/api/events/logs`).
  - `src/receiver/aegis_receiver.py`: Ingress socket listener on Port 5556, AEAD tag verification, frame reassembly.
  - `src/receiver/tile_reconstructor.py`: Real-time 64-tile matrix reassembler.
  - `src/frontend/templates/index.html`: Responsive CY · FOCUS dark operations console (#171615 canvas, persistent sidebar, metric cards, 64-tile grid, event timeline).
  - `src/frontend/static/css/cy_focus.css`: Complete CY · FOCUS design token implementation.
  - `src/frontend/static/js/ops_dashboard.js`: Live SSE event listener and Chart.js telemetry charts.
- **Exit Gate:** Flawless pixel-exact reconstruction of 64-tile medical scans; real-time telemetry updates (< 50 ms rendering latency); drop rate 0% on clean frames.

### Milestone 4: Independent Red-Team Cryptanalysis & Fault Injection Harness
- **Objective:** Build the independent red-team security auditing suite on Node 3B.
- **Deliverables:**
  - `src/red_team/sniffer.py`: Promiscuous packet capture engine computing Shannon entropy per frame ($H \approx 8.0\text{ bits/byte}$).
  - `src/red_team/injector.py`: Active adversary injector generating ciphertext bit-flips, authentication tag truncations, and frame replay attacks.
  - `src/red_team/toy_rsa_benchmark.py`: Empirical quantum vulnerability demonstrator benchmarking Pollard's Rho factoring on 32-bit to 512-bit RSA moduli vs. ML-KEM lattice security.
  - `src/red_team/shor_simulator.py`: Classical quantum emulator executing period-finding on small composite integers ($N=15, 21, 35$).
- **Exit Gate:** 100% rejection of tampered and replayed frames by Node 3A; empirical timing curves demonstrating exponential scaling of RSA factoring.

### Milestone 5: End-to-End Live 3-Node Demonstration & Final Attestation
- **Objective:** Full multi-system live demonstration over local physical LAN.
- **Deliverables:**
  - `docs/deployment/three_node_deployment_runbook.md`: Step-by-step operator guide for live demonstrations.
  - `tests/test_e2e_integration.py`: Automated multi-node integration test harness.
  - Final continuous integration commit and synchronized GitHub release on `https://github.com/Raja-sys77/AEGIS-pq`.
- **Exit Gate:** Complete live test passing across all three nodes under active red-team scrutiny without human intervention.

---

## 7. Target Code Layout & Workspace Organization

```text
D:\Raja\College projects\PQC - ORION Hack\
├── PROJECT.md                                # Master Architectural Blueprint (This Document)
├── README.md                                 # Project Overview & Quickstart Guide
├── .gitignore                                # Excludes caches, venvs, binaries; retains bitstream
│
├── docs/
│   ├── reconnaissance/                       # Complete 12-Report Reconnaissance Audit
│   │   ├── 00_master_reconnaissance_report.md
│   │   ├── 01_workspace_inventory.md
│   │   ├── 02_project_evolution.md
│   │   ├── 03_fpga_hardware_audit.md
│   │   ├── 04_existing_dashboard_audit.md
│   │   ├── 05_three_node_architecture_audit.md
│   │   ├── 06_cryptographic_design_review.md
│   │   ├── 07_system_boundaries_and_dependencies.md
│   │   ├── 08_network_and_deployment_review.md
│   │   ├── 09_capability_gap_matrix.md
│   │   ├── 10_validation_strategy.md
│   │   ├── 11_implementation_roadmap.md
│   │   └── 12_live_pynq_verification_log.md
│   │
│   └── development/                          # Engineering Logs & Runbooks
│       ├── continuous_integration_log.md     # Git Commits & Remote Sync Ledger
│       └── three_node_deployment_runbook.md  # Operator Execution Guide
│
├── PQC Kyber/                                # PRESERVED: Original Hardware & Legacy Dashboard
│   ├── bitstream/
│   │   ├── design_1.bit                      # Verified FPGA Bitstream (Zynq-7020)
│   │   └── design_1.hwh                      # Hardware Handoff XML
│   └── src/
│       ├── kyber_accelerator.cpp             # Original Vivado HLS C++ Core
│       ├── kyber_hal.py                      # Original Board Hardware Abstraction Layer
│       ├── app.py                            # Original Board Flask Dashboard (Port 5000)
│       └── templates/index.html              # Original Board UI Template
│
├── src/                                      # NEW: AEGIS-PQ Implementation Codebase
│   ├── common/                               # Shared Protocol Primitives
│   │   ├── __init__.py
│   │   ├── protocol.py                       # APBP-v1 Binary Header Packing & Parsing
│   │   └── types.py                          # Data Classes & Message Enums
│   │
│   ├── crypto/                               # Cryptographic Engine
│   │   ├── __init__.py
│   │   ├── mlkem512.py                       # NIST FIPS 203 ML-KEM-512 Implementation
│   │   ├── aead_cipher.py                    # AES-256-GCM Authenticated Encryption
│   │   ├── hkdf_kdf.py                       # RFC 5869 Session Key Expansion
│   │   └── ntt_reference.py                  # Software NTT/iNTT Reference Math
│   │
│   ├── gateway/                              # Node 2: PYNQ-Z2 Embedded Gateway Daemon
│   │   ├── __init__.py
│   │   ├── aegis_pynq_daemon.py              # Zero-Install In-Memory Gateway Service
│   │   ├── pl_accelerator.py                 # PYNQ DMA Hardware Driver Wrapper
│   │   └── watchdog.py                       # Threaded DMA Watchdog Timer
│   │
│   ├── mock_client/                          # Node 1: Legacy Client Generator (Fallback)
│   │   ├── __init__.py
│   │   ├── mock_legacy_client.py             # 64-Tile Medical Scan & SCADA Emitter
│   │   └── assets/                           # Test Patterns & DICOM Grayscale Slices
│   │
│   ├── backend_api/                          # Full-Stack REST & SSE API Server (Host)
│   │   ├── __init__.py
│   │   ├── app.py                            # Main API Server (Port 8000 / 5001)
│   │   ├── routes_system.py                  # System Info & Hardware Status
│   │   ├── routes_crypto.py                  # Cryptographic Telemetry & Verification
│   │   ├── routes_security.py                # Security Testing & Red-Team Injection
│   │   └── routes_telemetry.py               # Benchmarks & Live Frame Streams
│   │
│   ├── frontend/                             # CY · FOCUS Web Operations Console (Host)
│   │   ├── templates/
│   │   │   └── index.html                    # Responsive CY · FOCUS Operations Console
│   │   └── static/
│   │       ├── css/
│   │       │   └── cy_focus.css              # Dense Dark Ops Theme Tokens & Styles
│   │       └── js/
│   │           ├── ops_dashboard.js          # Live Telemetry & Event Stream Consumer
│   │           └── tile_matrix.js            # 64-Tile Medical Scan Reassembly Grid
│   │
│   └── red_team/                             # Node 3B: Independent Red-Team Suite
│       ├── __init__.py
│       ├── sniffer.py                        # Promiscuous Wiretap & Entropy Calculator
│       ├── injector.py                       # Adversarial Tamper & Replay Injector
│       ├── toy_rsa_benchmark.py              # Pollard's Rho vs. PQC Benchmark
│       └── shor_simulator.py                 # Classical Period-Finding Quantum Simulator
│
└── tests/                                    # Automated Verification Test Suite
    ├── test_crypto_primitives.py             # AEAD, HKDF, and APBP-v1 Unit Tests
    ├── test_mlkem_kat.py                     # NIST Known Answer Test (KAT) Runner
    ├── test_gateway_resilience.py            # DMA Watchdog & Buffer Invalidation Tests
    ├── test_red_team_attacks.py              # Active Fault Injection Validation Tests
    └── test_e2e_integration.py               # Full 3-Node End-to-End System Test
```

---

## 8. Anti-Cheating & Integrity Attestation

In accordance with strict project guidelines, the AEGIS-PQ implementation enforces the following integrity standards:
1. **Zero Hardcoding of Cryptographic Outputs:** All shared secrets, session keys, and ciphertexts are derived dynamically using true PRNG entropy and mathematical algorithms.
2. **Transparent Performance Representation:** The 27.0x speedup is explicitly documented as the arithmetic acceleration of the NTT-PWM-iNTT polynomial pipeline, not an end-to-end network handshake claim.
3. **Legitimate Red-Team Cryptanalysis:** Claims of breaking production RSA-2048 in seconds are rejected; red-team demonstrations utilize mathematically verified Toy RSA factoring (32-bit to 512-bit) and active AEAD tamper rejection.
4. **Authentic Hardware Interaction:** Hardware calls interact directly with the physical AXI DMA and PL registers at `0x40000000` on the PYNQ-Z2 board.
