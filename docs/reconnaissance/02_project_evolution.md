# Reconnaissance Report 02: Project Evolution & Chronological Reconstruction

**Document Reference:** `docs/reconnaissance/02_project_evolution.md`  
**Classification:** Authoritative Technical Reconnaissance  
**Author:** Teamwork Explorer 1 (Repo & Evolution Specialist)  
**Target Workspace:** `D:\Raja\College projects\PQC - ORION Hack`  
**Inspection Date:** 2026-10-29T19:25:00Z  
**Integrity Mode:** Strictly Non-Destructive / Read-Only  

---

## 1. Executive Summary

This report reconstructs the chronological, technical, and architectural evolution of the post-quantum cryptography project from its inception as an academic hardware arithmetic accelerator into the current executive-facing "AEGIS-PQ" post-quantum migration gateway.

The project has traversed three distinct evolutionary epochs:
- **Stage A (January – July 2026):** Physical design, synthesis, and verification of a Kyber-512 polynomial arithmetic accelerator on the TUL PYNQ-Z2 board.
- **Stage B (October 2026):** Architectural proposal for the Microchip PolarFire SoC Discovery Kit contest, designing a dual-KEM (ML-KEM-768 + HQC-1) crypto-agile subsystem with bare-metal ML-DSA-65 verification.
- **Stage C (Late October 2026):** Repositioning for the ORION AI Innovation Project Awards finals at IIT Madras Research Park as an inline post-quantum network offload engine, accompanied by a 3-device live network demonstration proposal.

This report documents the architectural motivations, abandoned pathways, hardware bugs, and critical discrepancies between presentation pitch decks and the executable codebase.

---

## 2. Chronological Epoch Timeline

```
========================================================================================================================
CHRONOLOGICAL EVOLUTION TIMELINE
========================================================================================================================

Jan 19, 2026  ─── [Stage A Hardware Baseline]
                  Bitstream synthesized for PYNQ-Z2 (design_1.bit, design_1.hwh).
                  Implements kyber_accelerator_top_0 (NTT-PWM-iNTT) and axi_dma_0.

Jun 10, 2026  ─── [Stage A HLS & Video Benchmark]
                  Vitis HLS C++ source finalized (kyber_accelerator.cpp).
                  Physical board demonstration filmed (PQC DILITHIUM KYBER VIDEO DEMO.mp4).
                  Terminal verification logged (Final PL Output).

Jul 07, 2026  ─── [Stage A Dashboard & Telemetry Verification]
                  Flask web UI deployed on PYNQ board (/home/xilinx/jupyter_notebooks/pqc_kyber512).
                  Measured 27.0x speedup over ARM CPU (Screenshot 2026-07-07 162306.png).
                  64-tile image encryption round-trip benchmarked at 3.464s (Screenshot 2026-07-07 165250.png).

Jul 20, 2026  ─── [Stage A Academic Documentation]
                  Detailed technical report authored (KYBER 512 Detailled Report.docx).
                  Python testbench archived (Jupyter Notebook Codes for PQC Kyber.py).
                  Dilithium HLS core abandoned due to zeta-table scaling divergence; kept in software.

Oct 24, 2026  ─── [Stage B PolarFire Contest Proposal Submission]
                  Track 1 submission (MPFS095T) drafted (Aegis-PQC_Master_Proposal_v2(1).md).
                  Evolved through 01-Agile v1.0 and final_microchip drafts to resolve LSRAM errors.
                  Designed cross-mathematical resource sharing (128-bit LSRAM + shared Keccak-f[1600]).

Oct 25-28, 2026 ─ [Stage C ORION AI Finals Deck Development]
                  Project branded as "AEGIS-PQ Inline Offload Engine" (Photonics_ORION AI Finals.pdf).
                  Prepared for Domain 02 (Robotics, IoT & Embedded Systems) at IIT Madras Research Park.
                   residual "Q-XRIDGE" branding preserved on Slides 6 and 11.

Oct 29-30, 2026 ─ [Stage C 3-Device Demonstration Architecture]
                  Demo strategy formulated for 19 jury members (PQC FPGA Demo Strategy.pdf).
                  3-device network proxy planned: Laptop 1 (legacy) -> PYNQ-Z2 -> Laptop 2 (cloud/wiretap).
                  Audited conversational shortcuts: NTT hashing and toy vs production RSA cracking.
========================================================================================================================
```

---

## 3. Detailed Evolutionary Stage Analysis

### 3.1 Stage A: The Academic Kyber-512 Arithmetic Accelerator (Jan – Jul 2026)

#### Core Concept & Target Hardware
Stage A was developed by student engineer Raja targeting the TUL PYNQ-Z2 board featuring the AMD Xilinx Zynq-7020 SoC (XC7Z020-CLG400-1). The processing system (PS) contains a dual-core ARM Cortex-A9 processor operating at 650 MHz, while the programmable logic (PL) provides an Artix-7 equivalent fabric (53,200 LUTs, 106,400 FFs, 140 BRAMs, 220 DSP slices).

#### Microarchitectural Implementation
The accelerator was authored in Vitis HLS C++ (`kyber_accelerator.cpp`) and integrated into a Vivado block design (`design_1.hwh`). It executes a 5-stage `#pragma HLS DATAFLOW` pipeline over polynomial ring $R_q = \mathbb{Z}_{3329}[X]/(X^{256} + 1)$:
1. **Load Stage (`load_data_wrapper`):** Streams 256 32-bit words from `axi_dma_0` via AXI4-Stream, masking each word to 16-bit modulus residues (`p.data % Q`).
2. **Forward NTT Stage (`run_ntt_wrapper`):** Executes a radix-2 decimation-in-frequency Cooley-Tukey NTT across 7 stages ($128$ butterflies per stage, total $896$ butterflies). It utilizes a 128-entry precomputed twiddle factor table (`zetas[128]`) in on-chip ROM.
3. **Pointwise Multiply Stage (`run_pwm_wrapper`):** Multiplies each polynomial coefficient by a static verification secret:
   ```cpp
   static const int16_t FIXED_SECRET = 3;
   int16_t res = montgomery_reduce((int32_t)val * (FIXED_SECRET * 2285)); // 2285 is 2^16 mod Q
   ```
4. **Inverse NTT Stage (`run_intt_wrapper`):** Executes a radix-2 decimation-in-time Gentleman-Sande inverse NTT across 7 stages, followed by a final scaling pass multiplying all 256 coefficients by $3316 \equiv 256^{-1} \pmod{3329}$.
5. **Store Stage (`store_data_wrapper`):** Streams the transformed polynomial coefficients back through AXI4-Stream to `axi_dma_0` with `TLAST` asserted on coefficient 255.

#### Memory Port Contention Solution (LUTRAM Partitioning)
In standard BRAM-based HLS implementations, a radix-2 butterfly requires 2 coefficient reads and 2 coefficient writes per cycle (4 memory access operations), stalling standard dual-port Block RAM (2 ports maximum) and collapsing the Initiation Interval ($II$) to $II \ge 2$ or creating pipeline bubbles. The designer resolved this by mapping internal buffers to partitioned Distributed LUTRAM:
```cpp
int16_t buffer[N];
#pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=lutram
```
This enabled conflict-free dual-port access with an Initiation Interval of one ($II=1$).

#### Measured Performance & Power
- **Hardware Footprint:** 5,387 LUTs (10.12%), 458 LUTRAMs (2.63%), 6,285 FFs (5.91%), 4 BRAMs (2.86%), 14 DSP48E1 slices (6.36%). Fabric utilization remains below 11%.
- **Execution Speed:** 1,000 continuous iterations executed in **1.19 seconds on FPGA** ($\approx 1.19\text{ ms/run}$) versus **32.26 seconds on ARM CPU** ($\approx 32.26\text{ ms/run}$), establishing a verified **27.0x speedup** (96.3% latency reduction).
- **Power Consumption:** Total on-chip power measured at $0.436\text{ W}$, with PL dynamic cryptographic logic drawing only $37\text{ mW}$ ($0.037\text{ W}$).

#### Boundaries of Stage A
As explicitly documented in `KYBER - 512 Documentation.docx` (Section 5, line 31): *"The current design serves as a verified 'Arithmetic Engine.' Future extensions will include integrating the Keccak (SHA-3) module for on-chip randomness generation and the Centred Binomial Distribution (CBD) sampler to create a standalone Key Generation IP."* Stage A is an arithmetic co-processor, not a complete KEM.

---

### 3.2 Stage B: The PolarFire SoC "Aegis-PQC" Co-Processor Proposal (October 2026)

#### Context & Submission Target
In October 2026, Raja and Naved Hasan developed an ambitious system architecture proposal for the Microchip PolarFire SoC Discovery Kit Contest (Track 1 — MPFS095T, deadline October 24, 2026), titled:
> *"Aegis-PQC: A Resource-Shared Hybrid Lattice/Code-Based Crypto-Agile Subsystem for Industrial Edge Telemetry on PolarFire® SoC"*

#### The Sub-Evolutionary Sequence (Audited from Evolution Transcript)
The transcript in `Aegis-PQC Project Evolution and Roadmap.pdf` records three internal iterations:
1. **Stage B.1 ("Everything Everywhere" / `01-Agile v1.0`):**
   - Inspired by Microchip's commercial `TS1800 TrustFLEX` post-quantum root of trust chip.
   - Proposed instantiating ML-KEM-768, HQC-1, ML-DSA-65 verify, Keccak-f[1600], AES-256-GCM, SHA-2, TRNG, LMS signatures, DICE attestation, and SPI monitors in the FPGA fabric.
   - Flaw: The fabric footprint estimate reached **89K LEs (95% of the 93.5K LE chip)**, guaranteeing routing failure and timing closure collapse in Microchip Libero SoC.
2. **Stage B.2 (Practical Pivot / `final_microchip(1).md`):**
   - Correctly moved infrequent control-plane signature verification (`ML-DSA-65`) out of fabric into bare-metal C on the 625 MHz RISC-V E51 monitor core (running out of 128 KB L2 LIM).
   - Removed soft AES, SHA-2, and TRNG from fabric, delegating them to the PolarFire SoC's native MSS User Crypto Processor (Athena TeraFire F5200B).
   - Flaws Introduced: Claimed a single 20 Kb LSRAM block could dynamically reconfigure port widths at runtime to 128 bits (physically impossible in PolarFire silicon); claimed sub-millisecond policy failover; claimed CNSA 2.0 compliance; and omitted handshake authentication.
3. **Stage B.3 (Hardened Master Proposal v2 / `Aegis-PQC_Master_Proposal_v2(1).md`):**
   - Replaced dynamic LSRAM reconfiguration with a banked 4-block parallel $512\times 40$ Two-Port LSRAM architecture (128-bit fixed bus) with word-level packing (8 coefficients of 16 bits in lattice mode; 128-bit binary polynomial slice in HQC mode).
   - Pinned HQC strictly to the NIST `2025-08-22` specification, separating `SampleFixedWeightVect$` (KeyGen rejection sampler) from `SampleFixedWeightVect` (Encrypt non-rejection sampler).
   - Enforced mutual authentication via a 256-bit device secret $K_{\text{dev}}$ mixed into a ciphertext-bound SHA3-256 combiner.
   - Confined ephemeral KEM decapsulation keys to a fabric write-only key vault with no bus read port.
   - Capped fabric footprint at an achievable 32K–51.2K LEs (34.2%–54.7% of MPFS095T).

#### Physical Hardware Status
Stage B was an architectural specification and contest proposal. **No PolarFire silicon, bitstream, or Libero project files exist in this repository.**

---

### 3.3 Stage C: The ORION AI Innovation Awards Demonstration (Late October 2026)

#### Context & Event Scope
The project was reframed for the ORION AI Innovation Project Awards 2026 Grand Finale at IIT Madras Research Park (October 31, 2026), under Domain 02 (Robotics, IoT & Embedded Systems).

#### Product Narrative & Market Problem
The pitch deck (`Photonics_ORION AI Finals.pdf`) and strategy documents position the project as **AEGIS-PQ: An Inline Post-Quantum Offload Engine**:
- **Target Problem:** High-value legacy edge systems (hospital MRI/PACS scanners, banking ATMs, industrial SCADA PLCs) are vulnerable to "Harvest Now, Decrypt Later" (HNDL) attacks and face India DPDP Act penalties (up to ₹250 Cr).
- **The Upgrade Barrier:** Operators cannot modify OS software or install heavy PQC algorithms on certified ₹5 Crore machines without voiding manufacturer warranties and causing CPU starvation.
- **The AEGIS-PQ Solution:** A "bump-in-the-wire" inline network hardware bridge that transparently intercepts unencrypted legacy traffic, executes post-quantum key establishment and encryption in dedicated FPGA hardware, and securely transmits ciphertext to cloud servers.

#### Proposed Three-Device Demonstration Architecture
To make the value tangible for a 19-member multidisciplinary jury (venture capitalists, banking heads, hospital directors, software engineers, and media creators), the co-founders designed a live 3-device sequence (`PQC Orion implentation.pdf`):
- **Device 1 (Naved's Laptop — Legacy Terminal):** Sends unencrypted medical imaging or financial wire transfer records over standard TCP/HTTP.
- **Device 2 (PYNQ-Z2 — AEGIS-PQ Inline Offload Gateway):** Intercepts the traffic, triggers the FPGA accelerator to compute Kyber-512 lattice transforms, establishes session keys, encrypts the payload, and forwards the packet.
- **Device 3 (Host Laptop — Cloud Receiver & Red-Team Wiretap):**
  - **Pane A (Wiretap / Red-Team Monitor):** Shows intercepted raw ciphertext and attempts a live cryptographic break.
  - **Pane B (Cloud Server Receiver):** Shows instant pixel-perfect decrypted telemetry (64 channels verified, 1.1 ms latency, 27.0x speedup).
  - **Tamper Simulation:** A live single-bit-flip test triggering immediate authentication failure on the receiver.

---

## 4. Abandoned Approaches & Known Bugs Register

The following approaches and code modules were attempted during the project lifecycle and subsequently abandoned or modified:

| # | Item / Subsystem | Evolutionary Epoch | Description of Abandoned Approach | Reason for Abandonment / Failure Mode | Current Status & Architectural Disposition |
|---|------------------|-------------------|-----------------------------------|---------------------------------------|--------------------------------------------|
| **A1** | **Dilithium (ML-DSA) HLS Engine** | Stage A (July 2026) | Custom Vitis HLS NTT accelerator for Dilithium digital signatures on PYNQ-Z2. | **Zeta-Table Scaling Bug:** Intermediate polynomial multiplications experienced scaling and twiddle-factor divergence, producing invalid signatures. | **Abandoned in Hardware:** Dilithium digital signature signing/verification was moved to a pure-software reference flow on the ARM CPU. |
| **A2** | **LMS Signature Engine** | Stage B.1 (Oct 2026) | Instantiating stateful Leighton-Micali Signatures (LMS, RFC 8554) in PolarFire fabric. | Redundant with ML-DSA-65 and required complex non-volatile state tracking across power cycles. | **Completely Dropped:** Removed from Master Proposal v2 to conserve fabric logic. |
| **A3** | **Soft AES-256-GCM & SHA-2 in Fabric** | Stage B.1 (Oct 2026) | Building soft Verilog cores for AES-GCM and SHA-2 in FPGA LUTs (consuming 8K–12K LEs). | PolarFire SoC already contains dedicated hard silicon (Athena TeraFire F5200B and NRBG) that provides symmetric crypto without fabric overhead. | **Cut from Fabric:** Replaced by native MSS crypto calls. |
| **A4** | **Dynamic LSRAM Width Reconfiguration** | Stage B.2 (Oct 2026) | Claiming a single 20 Kb LSRAM block could dynamically switch bus width to 128 bits at runtime. | **Hardware Violation:** Microchip PolarFire LSRAM blocks have fixed synthesis-time widths (max 40 bits Two-Port, 20 bits True Dual-Port). | **Corrected:** Replaced by banked 4-block parallel Two-Port LSRAM architecture ($512\times 40$). |
| **A5** | **Sub-Millisecond Policy Failover** | Stage B.2 (Oct 2026) | Claiming sub-millisecond crypto-agility algorithm hot-switching. | ML-DSA-65 signature verification in C on the in-order 625 MHz E51 monitor core requires 3–30 ms. | **Corrected:** Replaced by a realistic $<100\text{ ms}$ policy failover target. |
| **A6** | **CNSA 2.0 & TVLA Side-Channel Claims** | Stage B.2 (Oct 2026) | Claiming CNSA 2.0 compliance and TVLA DPA resistance without measurement hardware. | CNSA 2.0 mandates Level 5 parameters (ML-KEM-1024, ML-DSA-87), whereas the proposal targets Level 3/1; TVLA requires physical oscilloscope instrumentation. | **Dropped:** Replaced by standard NIST FIPS compliance and cycle-count invariance. |
| **A7** | **Legacy Naming: Q-XRIDGE** | Stage C (Oct 2026) | Earlier project brand name "Q-XRIDGE" used in slidedecks. | Superceded by "AEGIS-PQ" branding. | **Residual Artifact:** Slides 6 and 11 in `Photonics_ORION AI Finals.pdf` still retain the obsolete string "Q-XRIDGE". |

---

## 5. Pitch Claims vs Codebase Reality

A rigorous comparison between presentation claims, chat transcripts, and actual repository code reveals six fundamental discrepancies that require disciplined engineering resolution:

```
+---------------------------------------------------------------------------------------------------------------------+
| GAP 1: Cryptographic Completeness                                                                                   |
| CLAIM (Pitch Decks): "Complete PQC Kyber-512 engine implemented in FPGA hardware."                                  |
| CODE REALITY: kyber_accelerator.cpp implements ONLY NTT, Pointwise Multiply (fixed secret 3), and iNTT.             |
| RESOLUTION: Accurately state that the PL core is an arithmetic co-processor. Full ML-KEM key encapsulation          |
|             is achieved via HW/SW co-design with the ARM processing system.                                         |
+---------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------+
| GAP 2: Session Key Derivation                                                                                       |
| CLAIM (Chat Transcript): "Hash the 256 NTT output polynomial coefficients with SHA-256 to create an AES key."      |
| CRYPTO REALITY: Raw polynomial coefficients are not uniform cryptographic keys; doing so violates FIPS 203.        |
| RESOLUTION: Reject raw NTT hashing. Implement standard-compliant hybrid KEM key derivation using a verified        |
|             software KDF bound to valid decapsulated shared secrets.                                                |
+---------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------+
| GAP 3: Quantum Shor's Algorithm Simulation                                                                          |
| CLAIM (Demo Pitch): "Simulate Quantum Shor's Algorithm cracking RSA in 3 seconds live on a laptop."                 |
| CRYPTO REALITY: Factoring RSA-2048 classically takes thousands of years; true Shor's requires physical quantum bits.|
| RESOLUTION: Do not claim to break RSA-2048. Implement a genuine mathematical crack on scaled 64-bit RSA using      |
|             Pollard's Rho / ECM, transparently presented as an educational illustration of quantum vulnerability.   |
+---------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------+
| GAP 4: Inline Network Topology                                                                                      |
| CLAIM (Pitch Decks): "Inline bump-in-the-wire hardware bridge with dual physical Ethernet ports."                   |
| HARDWARE REALITY: The PYNQ-Z2 board possesses only a single physical RJ45 Ethernet port.                           |
| RESOLUTION: Operate as a logical inline gateway proxy over a shared local switch/LAN, or require a USB-Ethernet     |
|             dongle on the PYNQ USB host port for physical dual-cable ingress/egress.                                |
+---------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------+
| GAP 5: Hardware Target Platform                                                                                     |
| CLAIM (Stage B Docs): PolarFire SoC MPFS095T with RISC-V cores and TeraFire crypto coprocessor.                     |
| CODEBASE REALITY: Only Xilinx Zynq-7020 (PYNQ-Z2) bitstreams and source files exist in the repository.             |
| RESOLUTION: Explicitly maintain the distinction between the Stage B PolarFire contest proposal and the              |
|             executable Stage A/C PYNQ-Z2 hardware deployment.                                                       |
+---------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------+
| GAP 6: 27.0x Acceleration Scope                                                                                     |
| CLAIM (Pitch Decks): "27x faster post-quantum encryption on FPGA."                                                  |
| BENCHMARK REALITY: The 27.0x speedup measures 1000 iterations of polynomial NTT-PWM-iNTT arithmetic, not full TLS. |
| RESOLUTION: Precisely cite 27.0x as the modular polynomial arithmetic acceleration factor.                         |
+---------------------------------------------------------------------------------------------------------------------+
```

---

## 6. Implementation Readiness & Transition Strategy

To transition from reconnaissance into authorized implementation for the ORION AI Finals demonstration, the engineering roadmap must adhere to the following baseline rules:
1. **Preserve Silicon Integrity:** The pre-synthesized `design_1.bit` bitstream on PYNQ-Z2 is fully verified and functional. Under no circumstances should the hardware bitstream be re-synthesized or modified.
2. **Coexist with Existing Dashboard:** The existing PYNQ web dashboard running on port 5000 (`/home/xilinx/jupyter_notebooks/pqc_kyber512`) must remain active and undisturbed. The new 3-device demonstration services must bind to dedicated, non-conflicting network ports (e.g., port 8080/8443 for the inline proxy service).
3. **Scientifically Honest Cryptography:** Red-team attack scripts must be mathematically genuine (factoring real 64-bit RSA integers live in 1.5–3 seconds) and clearly labeled as an educational model. Hashing raw NTT output coefficients must be replaced with proper KEM key encapsulation and decapsulation flows.
4. **Resilient Network Protocol:** Communication between Node 1 (Legacy Laptop), Node 2 (PYNQ-Z2 Gateway), and Node 3 (Receiver Laptop) should utilize framed TCP sockets with explicit JSON metadata headers (`length`, `alg`, `iv`, `ciphertext`, `mac`), ensuring complete protocol observability.
