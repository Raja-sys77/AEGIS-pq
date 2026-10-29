# Aegis-PQC: A Resource-Shared Hybrid Lattice/Code-Based Crypto-Agile Subsystem for Industrial Edge Telemetry on PolarFire® SoC

> **Internal master document (v2).** Do not upload this file to the contest portal. Upload only the block-diagram PDF; paste the two plain-text blocks from Section 7 into the portal forms. Evidence tags: numbers marked *estimated* are targets until measured on hardware.

**Target Track:** Track 1 — PolarFire® SoC Discovery Kit (MPFS095T)

**Submission Deadline:** October 24, 2026, 11:59 PM PDT (October 25, 12:29 PM IST)

**Final Competition Window:** November 30, 2026 – March 27, 2027

---

## 1. Executive Summary & Architectural Thesis

Long-lifecycle industrial IoT (IIoT), smart-grid, and aerospace telemetry nodes deployed today will remain in the field for 15–25 years, well into the era of cryptanalytically relevant quantum computers (CRQCs) and tightening post-quantum migration timelines set by governments and standards bodies (**NIST PQC standards**). While organizations are migrating to lattice-based **ML-KEM (FIPS 203)** as their primary PQC key encapsulation mechanism, NIST selected the code-based **Hamming Quasi-Cyclic (HQC)** algorithm in March 2025 as the official backup KEM specifically because its mathematical hardness—Quasi-Cyclic Syndrome Decoding (QCSD)—is completely independent of structured lattices.

However, deploying both ML-KEM and HQC on resource-constrained embedded SoCs presents two practical engineering bottlenecks:

1. **Software Execution Overhead:** Executing HQC-1 in software on a 625 MHz in-order RISC-V core (SiFive U54) requires millions of clock cycles ($\approx 20\text{–}60\text{ ms}$ per operation), consuming substantial CPU bandwidth and dynamic energy during frequent session re-keying or multi-sensor aggregation.
2. **FPGA Fabric Area Bloat:** Instantiating independent hardware accelerators for ML-KEM, HQC, digital signatures, and classical encryption easily exhausts the logic elements (LEs) of mid-range FPGAs like the 93K LE PolarFire SoC Discovery Kit, leaving insufficient fabric for industrial I/O or edge processing.

**Aegis-PQC** solves both bottlenecks through a **Hardware-Software Co-Design and Cross-Mathematical Resource-Sharing Architecture** tailored specifically to the PolarFire SoC (MPFS095T):

* **In the FPGA Fabric (PL — Data Plane):** We design a unified **ML-KEM-768 + HQC-1 Dual-KEM Co-Processor** occupying an estimated **32K–51K LEs ($34\%\text{–}55\%$ utilization)**. Both engines share a single high-throughput **Keccak-f[1600] sponge core** (saving $\approx 5.5\text{K–}7.5\text{K LEs}$, or $\approx 50\%$ of the hashing subsystem area) and a unified **128-bit Banked LSRAM Vector Memory Subsystem** (packing eight 16-bit aligned ML-KEM coefficients per 128-bit word during lattice mode, and 128-bit binary polynomial slices during code-based mode).
* **In the Microprocessor Subsystem (PS — Control & Session Plane):** We leverage the PolarFire SoC’s Asymmetric Multiprocessing (AMP) architecture and native hard silicon:
* **Hart 0 (E51 Bare-Metal Security Monitor):** Runs out of a **PMP-isolated 128 KB slice of L2 Loosely Integrated Memory (LIM)**. It verifies **FIPS 204 ML-DSA-65** signed cryptographic policy advisories and gateway public-key certificates in bare-metal software (estimated 3–30 ms, to be measured), manages anti-rollback counters in the native **56 KB sNVM**, controls the key-slot lifecycle (ephemeral KEM keys are generated inside the fabric and never leave it), and hot-switches the fabric between **ML-KEM-768**, **HQC-1**, or **Hybrid (ML-KEM + HQC)** modes with a target of under **100 ms end-to-end** (to be measured) without rebooting Linux.
* **Harts 1–4 (U54 Linux Telemetry & Protocol Node):** Acquires live environmental and power telemetry via the 40-pin Raspberry Pi header, orchestrates mutually authenticated PQC key exchanges with a remote PC gateway using opaque key handles, and offloads symmetric **AES-256-GCM** session encryption and **SHA-256/SHA-384** hashing to the MSS’s hard **Athena TeraFire F5200B User Crypto Processor**.



---

## 2. Comprehensive Decision & Verification Matrix

The table below documents every architectural modification made from our initial concept and our internal technical audit, detailing both the **Technical Engineering Reasoning** and the **Strategic Contest Rubric Justification**.

| # | Design Area | Initial / Draft Concept | Final Verified Decision | Technical Engineering Reasoning | Strategic / Contest Rubric Justification |
| --- | --- | --- | --- | --- | --- |
| **D1** | **Control-Plane Signature Verification (`ML-DSA-65`)** | Implement custom `ML-DSA-65` verify engine in FPGA fabric ($6\text{K–}15\text{K LEs}$); also include `LMS`. | **Move `ML-DSA-65` (FIPS 204) verification to bare-metal C on the E51 core (running in 128 KB L2 LIM); drop `LMS` completely.** | Policy advisory and gateway certificate verifications are infrequent control-plane events. Running clean C `FIPS 204 ML-DSA-65` on the 625 MHz E51 takes $\approx 1.8\text{M cycles}$ (the E51 has no L1 data cache, so the naive 1.8M-cycle figure is optimistic: estimated 3–30 ms, to be measured; fallback: run the monitor on a bare-metal U54 hart with a data cache), saves $6\text{K–}15\text{K LEs}$, eliminates our unresolved Dilithium hardware NTT zeta-table bug, and removes the redundant SHA-256-based LMS code path. | Code & Implementation (35%): Eliminates the #1 schedule killer and prevents fabric congestion while demonstrating smart HW/SW partitioning on the E51 monitor core.

 |
| **D2** | **Classical Crypto (`AES-256-GCM`, `SHA-2`, `TRNG`)** | Implement custom AES-256-GCM, SHA-2, and ring-oscillator TRNG in FPGA fabric ($8\text{K–}12\text{K LEs}$). | **Cut from FPGA fabric; use the native PolarFire SoC MSS User Crypto Processor (TeraFire F5200B), NRBG, and 56 KB sNVM.** | The MPFS095T already contains hard silicon for AES-256-GCM, SHA-2, true random number generation (NRBG), and PUF-backed sNVM. Rebuilding these in soft LUTs wastes $\approx 10\%$ of the FPGA and duplicates hard silicon. | Technical Feasibility (35%): Judges specifically score *"Appropriate use of the selected FPGA kit and peripherals"*. Using native MSS security blocks proves mastery of the PolarFire SoC datasheet.

 |
| **D3** | **LSRAM Memory Architecture for 128-bit Datapath** | Claim a single 20 Kb LSRAM block supports 128-bit width and dynamic runtime width reconfiguration. | **Use a 4-Block Two-Port ($512\times 40$) or 7-Block Dual-Port ($1\text{K}\times 20$) Banked LSRAM Array (128-bit fixed bus) with word-level packing.** | PolarFire LSRAM blocks have fixed synthesis-time port widths up to 40 bits (Two-Port) or 20 bits (True Dual-Port). Concatenating 4 Two-Port blocks yields a 160-bit bus (128 data bits). In ML-KEM mode, each 128-bit word stores **eight 16-bit aligned coefficients** ($8\times 16 = 128\text{ bits}$); in HQC mode, it stores a **128-bit binary polynomial slice**. Total usage is 24–32 LSRAMs ($<11\%$ of 308 blocks). | Technical Feasibility (35%): Eliminates a fatal hardware specification error that Microchip engineers would immediately penalize, while retaining genuine cross-algorithm memory sharing.

 |
| **D4** | **ML-KEM NTT & Multiplier Implementation** | Synthesize ML-KEM NTT via SmartHLS C++; assume 2 MACC blocks per butterfly with $v=20,159$. | **Write ML-KEM NTT in Verilog RTL with Ping-Pong Dual-LSRAM banks; allocate 3–4 MACC18x18 blocks per butterfly; verify across all $3329^2$ pairs.** | A radix-2 butterfly requires 2 reads and 2 writes per cycle (4 memory accesses), causing SmartHLS port conflicts on single 2-port LSRAMs. Ping-pong RTL banking achieves $II=1$. Furthermore, $24\times 15$-bit Barrett reduction ($v = \lfloor 2^{26}/3329 \rfloor = 20,158$ or rounded $20,159$) exceeds one $18\times 18$ signed MACC, requiring 3–4 MACCs total per butterfly ($<3\%$ of 292 MACCs). | Code & Implementation (35%): Resolves the team's previous Kyber HLS bottleneck and demonstrates rigorous RTL + DSP microarchitecture.

 |
| **D5** | **HQC Specification Version & Sampler / FO Details** | Generic HQC description mixing 2023 and 2025 specs (`G(m || ek[0..31] || salt)` and single sampler). | **Pin strictly to HQC `2025-08-22` spec: implement both `SampleFixedWeightVect$` (KeyGen) and `SampleFixedWeightVect` (Encrypt), plus $G(H(ek_{\text{KEM}}) \parallel m \parallel \text{salt})$.** | The `2025-08-22` HQC spec uses uniform rejection sampling (`SampleFixedWeightVect$`) in `KeyGen` and constant-time 24-bit division-free sampling (`SampleFixedWeightVect`) in `Encrypt`, and hashes the full 2,241-byte $ek_{\text{KEM}}$ via SHA3-256 ($H$) before deriving $(K,\theta)$ via SHA3-512 ($G$). Both U54 Linux and the PC peer run the `2025-08-22` C reference. | Code & Implementation (35% Final): Guarantees 100% Known Answer Test (KAT) and PC interoperability without spec-mismatch failures.

 |
| **D6** | **Key Isolation & Bus Protection Mechanism** | Claim "MSS MPU blocks U54 Linux from reading PL key vault" and imply session keys stay in PL. | **Enforce CPU isolation via RISC-V PMP (configured by E51 in M-mode) + Hardware Write-Only Key-Slot RAM; use ephemeral per-session KEM keys generated inside the fabric (no software path) and distinguish them from $K_{\text{session}}$.** | In PolarFire SoC, **RISC-V PMP** isolates U54 CPU contexts, while the **AXI MPU** polices fabric DMA masters. To make DMA key theft physically impossible, the PL Key-Slot RAM has an **E51-only APB Write Port** and **no bus Read Port** (wired strictly internally to the KEM decapsulators). Ephemeral per-session $dk_{\text{KEM}}$ keys are generated inside the PL and destroyed after one decapsulation, so a compromised Linux cannot use the engine as a long-lived decapsulation oracle; only $K_{\text{session}}$ is passed to Linux/MSS Crypto for session traffic. | Innovation & Creativity (25%): Hardware-enforced write-only key slots + RISC-V PMP isolation is a genuinely strong, defensible security architecture.

 |
| **D7** | **Handshake Authentication & Hybrid Combiner** | Unauthenticated KEM combiner with a coined "Context-Bound Split-PRF" name. | **Mutually authenticated hybrid handshake: ephemeral ML-KEM + HQC keys per session, per-device 256-bit authentication secret mixed into a ciphertext- and key-bound SHA3-256 combiner, HMAC key confirmation both ways; ML-DSA-65 used for policy advisories and an optional pinned gateway certificate (verified once).** | KEM combiners alone do not authenticate peers. Binding a quantum-safe symmetric device secret and both ciphertexts and public-key hashes into the key derivation defeats public-key substitution and keeps the slow E51 signature check off the per-handshake critical path. The construction follows the style of Giacon–Heuer–Poettering (PKC 2018) and IETF CFRG hybrid-KEM work (exact draft names and versions to be verified); it requires a written design review before implementation. | Problem Statement & Clarity (20%): closes the man-in-the-middle gap with a single, fully specified protocol (Section 3.2, item 4). |
| **D8** | **Track 1 Alignment, Timing/Failover & Energy Claims** | Claim "$<1\ \mu\text{s}$ bare-metal jitter", "sub-ms failover", "TVLA side-channel resistance", and "CNSA 2.0". | **Use 2-Context AMP (E51 Monitor + U54 Linux Sensor Node); claim a $<100\text{ ms}$ policy-failover target (measured), Cycle-Count Invariance, and 1,000-loop INA219 energy integration.** | Drops unprovable oscilloscope jitter and TVLA claims, removes CNSA 2.0 claims and states NIST PQC alignment only, and accounts for the INA219's $532\ \mu\text{s}$ ADC sample period by integrating power over 1,000-iteration KEM batches. | Video Demo (20%) & Documentation (20%): Every single claim in the proposal is 100% measurable with the hardware on our desk.

 |

---

## 3. System Architecture: PS (RISC-V MSS) vs. PL (FPGA Fabric)

### 3.1 High-Level Partitioning & Trust Boundaries

The system is partitioned across the PolarFire SoC (MPFS095T) into two hardware-enforced RISC-V Physical Memory Protection (PMP) contexts managed by **Hart Software Services (HSS)**, paired with the custom AXI4/APB PQC Co-Processor in the FPGA fabric:

```
+---------------------------------------------------------------------------------------------------+
|                             MICROCHIP POLARFIRE SoC (MPFS095T)                                    |
|                                                                                                   |
|  +---------------------------------------------+   +-------------------------------------------+  |
|  | HART 0: E51 MONITOR CORE (PMP-Isolated)    |   | HARTS 1-4: U54 APPLICATION CORES (Linux)  |  |
|  | - 128 KB PMP-Isolated L2 LIM Execution RAM  |   | - Industrial Telemetry & TLS/KEM Client   |  |
|  | - FIPS 204 ML-DSA-65 Verifier (Pure C)      |   | - 40-Pin RPi Header (BME280 + INA219 I2C) |  |
|  | - Policy Engine & Anti-Rollback Logic       |   | - Holds Opaque Key Handles Only           |  |
|  | - Native 56 KB sNVM & PUF Root Key Access   |   | - Uses MSS TeraFire F5200B for AES-GCM    |  |
|  +----------------------+----------------------+   +---------------------+---------------------+  |
|                         |                                                |                        |
|         PMP-Restricted  | APBControl & Key-Load Bus                      | 64-bit AXI4 Data Bus   |
|         Aperture (0x400)| (Blocked from U54 & DMA via PMP/MPU)           | (Public ct / ek / K_s) |
|                         v                                                v                        |
|  +---------------------------------------------------------------------------------------------+  |
|  |                         FPGA FABRIC (PL): AEGIS-PQC CO-PROCESSOR (~42K LEs)                 |  |
|  |                                                                                             |  |
|  |  +---------------------------------------+    +------------------------------------------+  |  |
|  |  | WRITE-ONLY KEY-SLOT LSRAM VAULT       |    | AXI4 DMA & CONTROL/STATUS REGISTERS      |  |  |
|  |  | - APB Write Port (E51 Only)           |    | - Cycle Counter (rdcycle / HW Timer)     |  |  |
|  |  | - NO Bus Read Port (Zero Exfiltration)|    | - Mode Mux (0: ML-KEM, 1: HQC, 2: Hybrid)|  |  |
|  |  +-------------------+-------------------+    +--------------------+---------------------+  |  |
|  |                      | Internal-Only dk_KEM Wire                   |                        |  |
|  |                      v                                             v                        |  |
|  |  +---------------------------------------------------------------------------------------+  |  |
|  |  |               SHARED RESOURCE LAYER (CROSS-MATHEMATICAL MULTIPLEXING)                 |  |  |
|  |  |  1. Unified Keccak-f[1600] Core (1 Round/Cycle, 24 Cycles/Perm: SHA3-256/512, SHAKE)  |  |  |
|  |  |  2. Unified 128-bit Banked LSRAM Vector Memory (4x 512x40 Two-Port Banks per Buffer)  |  |  |
|  |  +-----------------------------------+---------------------------------------------------+  |  |
|  |                                      |                                                      |  |
|  |            +-------------------------+-------------------------+                            |  |
|  |            v                                                   v                            |  |
|  |  +---------------------------------------+   +-------------------------------------------+  |  |
|  |  | ENGINE A: ML-KEM-768 (FIPS 203)       |   | ENGINE B: HQC-1 (2025-08-22 Spec)         |  |  |
|  |  | - Radix-2 NTT/INTT (Ping-Pong LSRAMs) |   | - Dual Sampler (SampleFixedWeightVect$/V) |  |  |
|  |  | - 3-4 MACC18x18 Modular Butterfly     |   | - 128-bit Bit-Parallel Cyclic Multiplier  |  |  |
|  |  | - CBD Sampler & Compress/Decompress   |   | - Concatenated RM(1,7) + RS[46,16] Codec  |  |  |
|  |  +-------------------+-------------------+   +---------------------+---------------------+  |  |
|  |                      | K_1 (32B)                                   | K_2 (32B)              |  |
|  |                      +----------------------+----------------------+                        |  |
|  |                                             v                                               |  |
|  |  +---------------------------------------------------------------------------------------+  |  |
|  |  |             CIPHERTEXT-BOUND HYBRID KEM COMBINER (VIA SHARED KECCAK)                  |  |  |
|  |  |      K_session = SHA3-256(K_1 || K_2 || ct_1 || ct_2 || H(ek_1) || H(ek_2) || label)  |  |  |
|  |  +---------------------------------------------------------------------------------------+  |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+

```

### 3.2 Detailed Component Specifications

#### **1. Shared Resource Layer (PL Fabric)**

* **Unified Keccak-f[1600] Sponge Core:**
* Implements the full 1600-bit state permutation in Verilog RTL at **1 round per clock cycle** (24 cycles per permutation at $100\text{ MHz} = 240\text{ ns}$).
* Supports configurable rate/capacity padding and domain separation for `SHA3-256` ($r=1088$), `SHA3-512` ($r=576$), `SHAKE128` ($r=1344$), and `SHAKE256` ($r=1088$).
* **Quantified Resource Savings:** A standalone high-speed Keccak-f[1600] core with rate buffers and padding logic consumes **5,000–7,500 LEs**. Sharing one physical core across ML-KEM-768, HQC-1, and the Hybrid KEM Combiner eliminates a second redundant Keccak instance, cutting **$\approx 50\%$ of the hashing/XOF subsystem logic** and **$\approx 15\%$ of the overall PQC co-processor fabric area**.


* **Unified 128-Bit Banked LSRAM Vector Memory:**
* Configured using **4 parallel $512\times 40$ Two-Port LSRAM blocks per 128-bit wide vector buffer** (providing 160 physical bits per word; 128 bits active, 32 bits spare/parity), or **2 parallel $1\text{K}\times 20$ True Dual-Port LSRAM blocks per 32-bit ping-pong NTT bank**.
* **Word-Level Cross-Family Packing (No Runtime Width Reconfiguration):** During HQC-1 execution, each 128-bit word stores a 128-bit slice of a length-$17,669$ binary polynomial over $\mathbb{F}_2[X]/(X^n - 1)$ ($\lceil 17,669 / 128 \rceil = 139\text{ words}$ per vector). During ML-KEM-768 execution (or ciphertext/public-key buffering), each 128-bit word packs **eight 16-bit aligned coefficients** ($8 \times 16 = 128\text{ bits}$, holding 12-bit $\mathbb{Z}_{3329}$ residues).



#### **2. Engine A: ML-KEM-768 Accelerator (FIPS 203 Compliant)**

* **Ping-Pong Dual-LSRAM NTT Architecture:**
* Each degree-255 polynomial ($N=256$ coefficients in $\mathbb{Z}_{3329}$) is partitioned across **two True Dual-Port LSRAM banks (Ping and Pong)**, with two coefficients packed per 32-bit word.
* In each NTT stage ($7\text{ stages} \times 128\text{ butterflies} = 896\text{ operations}$), the butterfly unit reads two coefficients from the Ping bank, performs the Cooley-Tukey (forward NTT) or Gentleman-Sande (inverse NTT) butterfly, and writes two updated coefficients into the Pong bank on every clock cycle ($\text{Initiation Interval } II = 1$). Roles swap between stages, completely eliminating the 4-port memory contention that stalls naive HLS synthesis.


* **Verified Modular Arithmetic & DSP Allocation:**
* Modulo $q = 3329$ reduction uses Barrett reduction with precomputed constant $v = \lfloor 2^{26}/3329 + 0.5 \rfloor = 20,159$ (or floor $20,158$ with conditional single subtraction).
* Because multiplying the 24-bit product $z = a \cdot b$ by the 15-bit constant $v$ requires a $24 \times 15$-bit multiplier—exceeding a single PolarFire $18\times 18$ signed MACC block ($17\times 17$ unsigned)—each butterfly unit instantiates **3 to 4 MACC18x18 blocks** (1 MACC for $\zeta \cdot b$ and 2–3 cascaded MACCs for the high-word Barrett multiply), consuming $<3\%$ of the MPFS095T's 292 MACC blocks. The RTL module is verified via an exhaustive simulation testbench across all $3,329^2 = 11,082,241$ input pairs.



#### **3. Engine B: HQC-1 Accelerator (Pinned to `2025-08-22` Specification)**

* **Dual Fixed-Weight Samplers (`SampleFixedWeightVect$` and `SampleFixedWeightVect`):**
* Directly implements the `2025-08-22` specification split:
1. **`SampleFixedWeightVect$` (for `KeyGen` secret vectors $\mathbf{x}, \mathbf{y}$ of weight $\omega = 66$):** Generates uniform random positions in $[0, n-1]$ ($n=17,669$) via rejection sampling over 16-bit SHAKE256 output streams, rejecting values $\ge \lfloor 2^{16}/n \rfloor \cdot n = 53,007$.
2. **`SampleFixedWeightVect` (for `Encrypt` random vectors $\mathbf{r}_1, \mathbf{r}_2$ of weight $\omega_r = 75$ and $\mathbf{e}$ of weight $\omega_e = 75$):** Implements constant-time, non-rejection sampling generating 24-bit random integers $\text{rand}_{24}$ from SHAKE256 and computing support indices via fixed-point multiplication $\text{ctx}[i] = i + \lfloor \text{rand}_{24} \cdot (n - i) / 2^{24} \rfloor$ using 1 MACC block, followed by a constant-time backward sweep to resolve index collisions.


* **Data-Independent Latency:** In `Encaps` and `Decaps`, the hardware is designed to execute a fixed number of clock cycles independent of secret vector bit positions and of the number of decoding errors, verified with hardware cycle counters over valid and invalid ciphertexts. This addresses the rejection-sampling timing attack documented in prior HQC literature. It is a timing property only, not a power or electromagnetic side-channel claim. `KeyGen` uses rejection sampling by design and is excluded.


* **128-Bit Bit-Parallel Cyclic Sparse Multiplier over $\mathbb{F}_2[X]/(X^{17669}-1)$:**
* Computes products of a dense polynomial ($\mathbf{h}, \mathbf{s}, \mathbf{u}$) and a sparse fixed-weight polynomial ($\mathbf{y}, \mathbf{r}_2$) represented by its $\omega$ non-zero support indices ($66$ or $75$).
* For each support index $idx_j$, the dense vector is cyclically shifted and XOR-accumulated across $139$ words of 128 bits using a single-cycle barrel-shifter + XOR pipeline. Each multiplication completes in $\omega \times 139 \approx 10,425\text{ cycles}$ ($0.104\text{ ms}$ at $100\text{ MHz}$) using **zero DSP blocks**.


* **Concatenated Reed-Muller / Reed-Solomon Codec:**
* **Encoding:** Encodes a 16-byte message $m$ into a 46-byte codeword via shortened $\text{RS}[46, 16, 31]$ over $\mathbb{F}_{2^8}$, then encodes each byte via duplicated first-order Reed-Muller $\text{RM}(1,7)$ (multiplicity $3$, length $384\text{ bits}$), yielding $46 \times 384 = 17,664\text{ bits}$ (padded to $n=17,669$).
* **Decoding:** Uses a 7-stage Fast Hadamard Transform (FHT) butterfly in fabric for soft-decision $\text{RM}(1,7)$ decoding followed by Berlekamp-Massey + Chien search + Forney's algorithm for $\text{RS}[46,16]$ error correction.


* **Salted Fujisaki-Okamoto ($\text{SFO}^{\not\perp}_m$) Transform:**
* Implements the exact `2025-08-22` KEM wrapper: hashes the full 2,241-byte encapsulation key $ek_{\text{KEM}}$ via $H(ek_{\text{KEM}}) = \text{SHA3-256}(ek_{\text{KEM}})$, derives $(K, \theta) \leftarrow G(H(ek_{\text{KEM}}) \parallel m \parallel \text{salt})$ via `SHA3-512` (where $K$ and $\theta$ are 32 bytes each and $\text{salt}$ is 16 bytes), and performs implicit rejection via $K \leftarrow J(H(ek_{\text{KEM}}) \parallel \sigma \parallel c_{\text{KEM}})$ if re-encrypted ciphertext $c'_{\text{PKE}} \ne c_{\text{PKE}}$ (evaluated via a constant-time 128-bit XOR-OR reduction tree across all 4,417 bytes of $c_{\text{PKE}}$).



#### **4. E51 Security Monitor & Mutually Authenticated Hybrid Handshake**

* **Key containment (what is and is not claimed):**
  * Ephemeral per-session KEM decapsulation keys (`dk_ML-KEM`, `dk_HQC`, including the HQC implicit-rejection secret) are generated **inside the fabric** and written directly into the key-slot LSRAM vault. Neither the E51 nor Linux ever sees them. The vault has **no APB or AXI read port**; its read side is wired only to the decapsulation engines. Keys are destroyed after one decapsulation.
  * **RISC-V PMP** (configured by HSS in Machine Mode) denies the U54 Linux harts access to the key-control APB aperture, the E51 L2 LIM partition and the MSS sNVM/system-service registers. Exact PMP/MPU configuration and register addresses are **to be verified** against the MSS documentation and Microchip's AMP/PMP reference examples.
  * **Not claimed:** protection against a compromised Linux using the engines as a decapsulation oracle during the one-shot window of a live handshake, protection of `K_session` (which Linux/MSS crypto must hold to run AES-256-GCM), or any power/EM side-channel resistance.
* **Handshake protocol (v2, to be frozen in Week 1–2):**

| Step | Direction | Content |
| --- | --- | --- |
| Provisioning (once) | Offline | 256-bit device authentication secret `K_dev` written to sNVM (E51-only); hash of the ML-DSA-65 root public key pinned in sNVM. |
| M1 | Gateway → Board | `nonce_g`, supported modes, optional ML-DSA-65-signed policy advisory. |
| M2 | Board → Gateway | E51 selects the mode allowed by the current policy epoch; fabric generates ephemeral key pair(s). Sends `nonce_b`, epoch, mode, `ek` value(s) and `MAC_b = HMAC-SHA256(K_dev, transcript)`. |
| M3 | Gateway → Board | Verifies `MAC_b`, encapsulates to each `ek` (liboqs ML-KEM; HQC 2025-08-22 reference), derives `K_session` and `K_confirm`, sends ciphertext(s) and `MAC_g = HMAC-SHA256(K_confirm, transcript)`. |
| M4 | Board | Fabric decapsulates with vault keys; combiner outputs `K_session` and `K_confirm`; board verifies `MAC_g`; ephemeral keys destroyed; only `K_session` passes to Linux / MSS crypto for AES-256-GCM. |

  * The E51 verifies `ML-DSA-65` only for **policy advisories** and an optional **gateway certificate checked once and pinned**, so the slow E51 verification is not on the per-handshake path.
  * **Combiner:** in single-KEM modes the unused secret field is a fixed 32-byte constant and a mode byte is included. All fields are fixed-length.

$$K_{\text{session}} = \text{SHA3-256}\left(\text{label} \parallel K_{\text{dev}} \parallel K_{\text{ML-KEM}} \parallel K_{\text{HQC}} \parallel ct_{\text{ML-KEM}} \parallel ct_{\text{HQC}} \parallel H(ek_{\text{ML-KEM}}) \parallel H(ek_{\text{HQC}}) \parallel nonce_g \parallel nonce_b\right)$$

  * Properties targeted: both-way authentication through a quantum-safe symmetric secret; forward secrecy from ephemeral KEM keys; confidentiality if **either** KEM, or the device secret, remains secure. Fleet key provisioning and revocation are out of prototype scope and stated as such.
  * This construction follows the style of published KEM-combiner work (Giacon–Heuer–Poettering, PKC 2018) and IETF CFRG hybrid-KEM drafts. It is not claimed to be proven; a one-page written design review against those references is a Week 1–2 deliverable.

---

## 4. Quantitative Feasibility, Area, Latency & Energy Derivations

### 4.1 PolarFire SoC Discovery Kit (MPFS095T) Resource Budget

**Available Resources on MPFS095T:** $93,516\text{ Logic Elements (4-input LUT + DFF)}$, $292\text{ MACC18x18 DSPs}$, $308\text{ LSRAMs (20 Kb each)}$.

| Hardware Module (PL Fabric) | Implementation Style | Est. LEs (Low) | Est. LEs (High) | MACC18x18 | LSRAM (20 Kb) | Notes & Verification Basis |
| --- | --- | --- | --- | --- | --- | --- |
| **Shared Keccak-f[1600] Core** | Verilog RTL (1 rnd/cyc) | 4,800 | 7,200 | 0 | 2 | State register (1600 FF) + theta/rho/pi/chi/iota + SHA3/SHAKE rate/pad mux |
| **Unified 128-Bit Vector RAM & Arbiter** | Libero LSRAM Macros + RTL | 1,200 | 2,000 | 0 | 16 | Four 128-bit vector buffers ($\mathbf{h}, \mathbf{s}/\mathbf{u}, \mathbf{v}, \text{temp}$), each using $4\times (512\times 40)$ Two-Port LSRAMs |
| **ML-KEM-768 Engine (NTT + CBD + Codec)** | Verilog RTL | 7,500 | 12,500 | 4 | 6 | 1 Radix-2 butterfly (3–4 MACCs) + Ping-Pong Dual-Port LSRAMs + Compress/Decompress |
| **HQC-1 Dual Sampler + 128-b Multiplier** | Verilog RTL | 8,500 | 13,500 | 1 | 4 | `SampleFixedWeightVect$/V` (1 MACC for $\times(n-i)$) + 128-bit barrel shifter & XOR accumulator |
| **HQC-1 RM(1,7) FHT + RS[46,16] Codec** | SmartHLS / RTL Hybrid | 6,500 | 10,500 | 0 | 4 | 7-stage FHT butterfly + $\mathbb{F}_{2^8}$ Berlekamp-Massey, Chien search, and Forney syndrome unit |
| **Write-Only Key Vault + AXI4/APB Wrapper** | Verilog RTL + SmartDesign | 3,500 | 5,500 | 0 | 2 | E51-only APB control slave, AXI4 DMA interface, cycle counters, constant-time comparator |
| **TOTAL AEGIS-PQC FABRIC FOOTPRINT** | **Hybrid RTL + SmartHLS** | **32,000** | **51,200** | **5** | **34** | **34.2% – 54.7% LEs | 1.7% MACCs | 11.0% LSRAMs** |

* **Timing Closure Margin:** Capping utilization below $55\%$ LEs and $12\%$ LSRAMs at a conservative **$100\text{ MHz}$ fabric clock** guarantees single-pass place-and-route timing closure in Libero SoC without routing congestion (**Confidence: High**).

### 4.2 Hardware Cycle-Count & Latency Derivations (at $100\text{ MHz}$ PL Clock)

#### **A. ML-KEM-768 Hardware Latency**

* **Matrix $\mathbf{A}$ Generation ($3\times 3$ polynomials via SHAKE128):** $9 \times 3\text{ blocks} \times 24\text{ cycles} \approx 648\text{ cycles}$.
* **NTT / INTT ($896\text{ cycles}$ per transform at $II=1$):**
* `Encaps`: 3 forward NTTs + 4 INTTs + base multiplications + hashing $\approx \mathbf{14,500\text{ cycles}} = \mathbf{0.145\text{ ms}}$.
* `Decaps`: 1 INTT + 1 re-encryption (`Encaps`) + SHA3-512 ($G$) + SHAKE256 ($J$) $\approx \mathbf{19,200\text{ cycles}} = \mathbf{0.192\text{ ms}}$.
* *(Note: NTT/INTT account for roughly 40–45% of Encaps cycles in this model; the hashing and sampling share will be measured, not assumed.)**

* **SHA3-256 of $ek_{\text{KEM}}$ ($2,241\text{ bytes} = 17\text{ blocks of } 136\text{ bytes}$):** $17 \times 24 = 408\text{ cycles}$.
* **Fixed-Weight Sampling (`SampleFixedWeightVect` for $\mathbf{r}_1, \mathbf{r}_2, \mathbf{e}$, weight $75$ each):** $3 \times (6\text{ SHAKE256 blocks} \times 24 + 150\text{ index-gen/sweep cycles}) \approx 882\text{ cycles}$.
* **128-Bit Sparse Polynomial Multiplication ($139\text{ words} \times \omega$):**
* Weight $\omega_r = 75$ (`Encaps` products $\mathbf{h}\cdot\mathbf{r}_2$ and $\mathbf{s}\cdot\mathbf{r}_2$): $75 \times 139 = 10,425\text{ cycles}$ per multiply ($0.104\text{ ms}$).
* Weight $\omega = 66$ (`KeyGen` product $\mathbf{h}\cdot\mathbf{y}$ and `Decaps` product $\mathbf{u}\cdot\mathbf{y}$): $66 \times 139 = 9,174\text{ cycles}$ per multiply ($0.092\text{ ms}$).


* **RM(1,7) + RS[46,16] Encoding / Decoding:**
* Encoding: $\approx 1,200\text{ cycles}$ ($0.012\text{ ms}$).
* Decoding (46 blocks of 128-point FHT + RS Berlekamp-Massey/Chien/Forney): $\approx 5,800\text{ cycles}$ ($0.058\text{ ms}$).


* **Total HQC-1 Cycle Breakdown:**
* **`KeyGen`:** $\text{Seed expand} + 2\times\text{SampleFixedWeightVect\$} (\approx 1,100) + 1\times\text{Mult}_{66} (9,174) + H(ek) (408) \approx \mathbf{11,200\text{ cycles}} = \mathbf{0.112\text{ ms}}$ *(Multiply is $82\%$ of cycles; Keccak/Sampling is $18\%$)*.
* **`Encaps`:** $H(ek) + G (456) + 3\times\text{SampleFixedWeightVect} (882) + 2\times\text{Mult}_{75} (20,850) + \text{Encode} (1,200) \approx \mathbf{23,800\text{ cycles}} = \mathbf{0.238\text{ ms}}$ *(Multiply is $87\%$ of cycles; Keccak/Sampling is $6\%$)*.
* **`Decaps`:** $1\times\text{Mult}_{66} (9,174) + \text{Decode} (5,800) + \text{Re-Encrypt} (23,800) + \text{CT Compare \& Implicit Reject} (850) \approx \mathbf{39,624\text{ cycles}} = \mathbf{0.396\text{ ms}}$.



#### **C. End-to-End Speedup vs. U54 Software Baseline ($625\text{ MHz}$)**

* On an in-order 625 MHz RV64GC U54 core without carry-less multiplication (`Zbc`) or vector extensions, scalar C reference `HQC-1 Decaps` requires $\approx 22\text{M–}35\text{M cycles}$ ($\mathbf{35\text{–}56\text{ ms}}$).
* Aegis-PQC hardware `HQC-1 Decaps` ($0.396\text{ ms}$ + $\approx 0.05\text{ ms}$ AXI4 DMA transfer $\approx \mathbf{0.45\text{ ms}}$) achieves an **$\approx 80\times\text{–}120\times$ latency speedup**.
* Full **Hybrid (ML-KEM-768 + HQC-1) Decapsulation + Combiner** completes in $0.192 + 0.396 + 0.015\text{ (Combiner)} + 0.08\text{ (DMA)} \approx \mathbf{0.68\text{ ms}}$.

---

## 5. Comprehensive 20-Item Risk Register & Mitigation Matrix

To maximize our score on the **Technical Feasibility (35%)** rubric, all hardware, software, cryptographic, and measurement risks are tracked below with concrete engineering mitigations:

| # | Risk Description | Prob. | Impact | Concrete Engineering Mitigation |
| --- | --- | --- | --- | --- |
| **R1** | **HQC Spec Version Drift (Draft FIPS 207 vs. 2025-08-22)** | High | Med | Pin both FPGA hardware and U54/PC C reference strictly to the `2025-08-22` specification package; parameterize hash domain-separation bytes and weights ($\omega=66, \omega_r=75$) in RTL headers. |
| **R2** | **PC Peer vs. Board Interoperability Mismatch** | Med | High | Do not use outdated `liboqs` HQC builds (which track the 2023/04/30 spec). Compile the official `2025-08-22` HQC reference C code into the Python/C gateway peer on the PC and the baseline benchmark binary on U54 Linux. |
| **R3** | **HQC Reed-Solomon ($\text{RS}[46,16]$) Decoder RTL Complexity** | Med-High | High | Write the control-heavy Berlekamp-Massey and Forney solver in **SmartHLS C++** (verified against Python step-by-step intermediate vectors) while keeping the bit-parallel $\text{RM}(1,7)$ Fast Hadamard Transform in **Verilog RTL**. Fallback: run outer RS[46,16] decoding (46 bytes) in software on a U54 if HLS area or timing slips at Week 7; software decoding gives up data-independent latency for that stage, and the claim must then be narrowed. |
| **R4** | **ML-KEM NTT LSRAM Port Contention** | Low-Med | High | Bypass SmartHLS for the NTT; implement a **Ping-Pong Dual-LSRAM RTL architecture** (2 reads from Ping, 2 writes to Pong per cycle at $II=1$). |
| **R5** | **Barrett Modular Multiplier Overflow / Corner-Case Bug** | Low | High | Allocate 3–4 MACC18x18 blocks per butterfly to handle the full $24\times 15$-bit product ($v=20,159$) and run an exhaustive automated Verilator/ModelSim testbench across all $3,329^2 = 11,082,241$ input pairs in Week 2. |
| **R6** | **HQC Sampler Timing Variance** | Med | Med | Use the non-rejection `SampleFixedWeightVect` for all `Encaps`/`Decaps` operations per the `2025-08-22` spec and verify identical cycle counts across 10,000 random valid and invalid ciphertexts with varying error weights. `KeyGen` uses the rejection sampler by design and is excluded from the invariance claim. |
| **R7** | **E51 Stack Overflow During `ML-DSA-65` Verification** | Med | High | The E51's 8 KB DTIM is too small for naive Dilithium stack frames. Configure **128 KB of the 2 MB L2 cache as Loosely Integrated Memory (LIM)** assigned exclusively to Hart 0 (E51) in the MSS Configurator, and use the streaming-matrix `PQClean` C implementation. |
| **R8** | **HSS / PMP / Yocto AMP Configuration Complexity (running user code beside HSS on the E51 is invasive)** | High | High | Start from Microchip's AMP/PMP reference examples for the same Linux release (exact package to be verified in Week 1) using 2 contexts. Decision gate at Week 5: if HSS integration on the E51 is not working, move the security monitor to a bare-metal U54 hart (PMP-isolated from the Linux harts, with a data cache), keeping the E51 on stock HSS. |
| **R9** | **DMA Exfiltration of KEM Private Keys / Decapsulation Oracle Misuse** | Low | High | Ephemeral keys generated and held inside the fabric vault with **zero bus read ports**; one-shot key slots destroyed after one decapsulation; E51 policy limits decapsulations per session. |
| **R10** | **Fabric Area Overrun / Timing Closure Degradation** | Low-Med | High | Hard budget cap of $55\text{K LEs}$ ($<60\%$ of MPFS095T) and $100\text{ MHz}$ target clock. Offloading `ML-DSA-65`, `AES-256-GCM`, and `SHA-2` to the MSS keeps expected utilization at $32\text{K–}51\text{K LEs}$. |
| **R11** | **INA219 I2C Conversion Latency ($532\ \mu\text{s}$) vs. Fast HW KEM ($<0.5\text{ ms}$)** | High | Med | Do not attempt single-shot power reads. Execute continuous loops of $N = 1,000$ back-to-back KEM operations ($\approx 450\text{ ms}$ window), sample INA219 power at $1\text{ kHz}$, subtract baseline idle power, and divide total integrated energy by $1,000$. |
| **R12** | **40-Pin Raspberry Pi Header Pinout / Voltage Mismatch** | Low | Med | Verify bank I/O voltage ($3.3\text{V}$) and MSS I2C0 / Fabric GPIO pin mapping against the PolarFire SoC Discovery Kit schematic before wiring the INA219 and BME280 sensors. |
| **R13** | **Unauthenticated Handshake MITM Vulnerability** | Low | Med | Mutual authentication with a per-device 256-bit secret mixed into the combiner and HMAC key confirmation both ways (Section 3.2, item 4); optional pinned ML-DSA-65 gateway certificate. |
| **R14** | **Advisory Signing Root Key Compromise (Key Custody)** | Low | Med | Provision a primary and backup `ML-DSA-65` root public key hash in read-only eNVM/sNVM at manufacturing time, supporting signed root-key rotation and monotonic anti-rollback counters in sNVM. |
| **R15** | **Live Demo Hardware / Network Failure During Video Recording** | Med | High | Build a deterministic Python CLI/GUI fault-injection script over local Ethernet/UART, keep a pre-flashed backup microSD card and eNVM image, and record modular demo segments by Week 15. |
| **R16** | **E51 Data-Memory Latency Makes ML-DSA-65 Verify Much Slower Than the 1.8M-Cycle Estimate (no L1 data cache)** | High | Med | Measure in Week 3. The failover target is under 100 ms. If verify exceeds 50 ms, relocate the monitor to a bare-metal U54 hart. |
| **R17** | **Linux Access to the MSS User Crypto Processor Unavailable** | Med | Low-Med | Check driver and access path in Week 1. Fallback: software AES-256-GCM on the U54 cores (telemetry data rate is low). |
| **R18** | **Per-Device Secret Provisioning and Fleet Key Management** | Med | Low-Med | Out of prototype scope. Provision a test secret per board, document the production approach (OEM root-derived per-device keys), and state the limitation. |
| **R19** | **Variable-Latency KeyGen Misread as a Timing Leak** | Med | Low | Define the invariance scope (Encaps/Decaps), document the KeyGen exception, and show both measurements. |
| **R20** | **Team Capacity Over 17 Weeks** | Med | High | MVP freeze at Week 8; cut order: stretch items, energy claim, hybrid-certificate option, then E51 integration (fall back to U54 monitor). |

---

## 6. 17-Week Execution Roadmap (Nov 30, 2026 – Mar 27, 2027)

Assuming a 3-person engineering split:

* **Lead A (Lattice & Shared RTL):** Shared `Keccak-f[1600]`, 128-bit Banked LSRAM arbiter, `ML-KEM-768` Ping-Pong NTT & codec, Hybrid Combiner FSM.
* **Lead B (Code-Based RTL/HLS):** `HQC-1` dual fixed-weight samplers (`SampleFixedWeightVect$` & `SampleFixedWeightVect`), 128-bit sparse multiplier, `RM(1,7)` FHT RTL, `RS[46,16]` SmartHLS/RTL codec.
* **Lead C (MSS Embedded, Security & Telemetry):** HSS/PMP 2-context setup, E51 bare-metal `FIPS 204 ML-DSA-65` verifier in L2 LIM, sNVM anti-rollback counter, U54 Linux UIO/char driver, MSS User Crypto `AES-256-GCM` integration, INA219/BME280 telemetry & PC dashboard.

| Weeks | Dates (2026–2027) | Primary Engineering Deliverables & Verification Gate |
| --- | --- | --- |
| **W1–W2** | Nov 30 – Dec 13 | Pin `2025-08-22` HQC C reference & FIPS 203/204 `PQClean` on U54 Linux and PC; export NIST KAT intermediate test vectors; verify exhaustive $3329^2$ Barrett multiplier testbench; boot Linux + E51 PMP reference design on Discovery Kit; freeze the handshake protocol and combiner design review. |
| **W3–W5** | Dec 14 – Jan 3 | **Lead A:** Shared `Keccak-f[1600]` RTL + `ML-KEM-768` Ping-Pong NTT passes 100% NIST KATs in simulation. **Lead B:** `HQC-1` dual samplers + 128-bit cyclic multiplier pass intermediate KATs. **Lead C:** E51 runs `ML-DSA-65` verify in 128 KB L2 LIM (measure; gate $<50\text{ ms}$) and writes sNVM counter. |
| **W6–W8** | Jan 4 – Jan 24 | **Lead B:** Complete `RM(1,7) + RS[46,16]` codec and FO wrapper; full `HQC-1` passes 100% NIST KATs. **Lead A:** Integrate `ML-KEM-768` + `HQC-1` + Shared Keccak + Write-Only Key Vault in Libero SmartDesign. **MILESTONE 1 (MVP Freeze):** Single bitstream synthesized ($<55\%$ LEs, $100\text{ MHz}$) executing hardware Dual-KEM handshake with PC peer. |
| **W9–W11** | Jan 25 – Feb 14 | **Lead C:** Implement E51 IPI policy daemon and hot-failover mux control; verify PMP/Write-Only Key-Slot protection (demonstrate U54 read trap `0x5`/`0x7`); integrate MSS User Crypto `AES-256-GCM` session encryption of BME280 sensor stream. |
| **W12–W14** | Feb 15 – Mar 7 | **All:** Hardware verification & benchmarking: verify cycle-count invariance across 10,000 decapsulations; wire INA219 current sensor on 40-pin header and run 1,000-iteration batch energy integration (HW vs. U54 SW baseline across Modes 0, 1, and 2). |
| **W15–W16** | Mar 8 – Mar 21 | **All:** Author 10-page IEEE/Microchip Final Technical Report, clean and document Verilog/SmartHLS/C repositories with build scripts, and film the 3–5 minute split-screen demonstration video.

 |
| **W17** | Mar 22 – Mar 27 | Final QA, third-party/AI tool disclosure check (Rule 8), and portal upload before **March 27, 2027, 11:59 PM PDT**.

 |

---

## 7. Official Contest Portal Submission Text Blocks

The two sections below are written in **strict plain text (zero LaTeX markup)** and have been word-count verified to sit comfortably inside the contest limits (**300 words max** for Project Overview; **250 words max** for Innovation & Expected Impact).

### 7.1 Project Overview (Max 300 Words — Actual Count: 265 Words)

> Problem. Industrial, utility and aerospace edge nodes stay in service for 15 to 25 years, so the keys they exchange today must resist future quantum computers. NIST standardized lattice-based ML-KEM (FIPS 203) for key establishment and, in 2025, selected the code-based HQC as a backup because its hardness is independent of lattices. Running both in software on an embedded RISC-V core takes tens of milliseconds per HQC operation, and a separate FPGA accelerator for every algorithm adds significant fabric area.

> Solution. Aegis-PQC is a hardware-software co-designed, crypto-agile security subsystem on the PolarFire SoC Discovery Kit (MPFS095T). In fabric, a dual-KEM co-processor implements ML-KEM-768 and HQC-1 (pinned to the 2025-08-22 specification) over one shared Keccak sponge core and a banked LSRAM vector memory, with a ciphertext-bound hybrid key combiner. Decapsulation keys live in a fabric key memory with no bus read path. In the RISC-V subsystem, the E51 monitor core, isolated by Physical Memory Protection, verifies ML-DSA-65 signed policy advisories in software, keeps anti-rollback counters in sNVM and switches the fabric between ML-KEM, HQC and hybrid modes. The U54 cores run Linux, a handshake daemon and sensor telemetry, using the SoC's native crypto services for AES-256-GCM and entropy.

> Target application and outcome. An industrial telemetry node that rekeys with a PC gateway while reporting BME280 sensor and INA219 power data. Expected outcomes: all known-answer tests passing in hardware; interoperable hybrid handshakes with a PC peer; a measured HQC speedup over the U54 software baseline (estimated 80x to 120x); fabric use below 55% of logic elements at 100 MHz; and authenticated algorithm failover without reflashing.

### 7.2 Innovation & Expected Impact (Max 250 Words — Actual Count: 227 Words)

> Novelty. The commercial PQC IP for PolarFire that we found covers lattice and hash-based algorithms, and published HQC hardware targets other FPGA families. We found no HQC implementation for PolarFire and no design combining lattice and code-based KEMs. Aegis-PQC contributes this integration:
> 1. Cross-family resource sharing: ML-KEM-768 (modular arithmetic on DSP math blocks) and HQC-1 (binary sparse multiplication and Reed-Muller/Reed-Solomon decoding in LUTs) share one Keccak core and one banked LSRAM subsystem, roughly halving hashing logic compared with two cores.
> 2. Dual-KEM hybrid key exchange: the session key depends on both KEMs and a device secret, so it holds if either lattice or code-based hardness holds.
> 3. Authenticated crypto-agility: ML-DSA-65 signed advisories with anti-rollback counters switch algorithms at run time, targeting under 100 ms, with no bitstream update.
> 4. Key containment: decapsulation keys sit in fabric memory without a bus read port, and Physical Memory Protection keeps Linux away from key-control registers.
>
> Impact. Long-lived industrial and energy systems must migrate before RSA and elliptic curves fail, yet the HQC standard will not be final until 2027. An updatable fabric can host and replace algorithms in the field. The project delivers a reusable SmartDesign subsystem, measured area, latency and energy data for an HQC backup path, and a verified reference design for engineers on PolarFire SoC. Larger parameter sets and ML-DSA acceleration map naturally to the Icicle Kit.

