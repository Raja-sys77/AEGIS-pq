# FPGA Hardware & Accelerator Audit Report

**Document ID**: `03_fpga_hardware_audit.md`  
**Target Platform**: PYNQ-Z2 (Xilinx Zynq-7000 SoC: `XC7Z020-1CLG400C`)  
**Status**: Verified via Local Codebase & Non-Destructive Live PYNQ-Z2 Telemetry  
**Date**: 2026-10-30  

---

## 1. Executive Summary

This audit provides a complete, factual, and hardware-verified analysis of the FPGA accelerator artifact found in the AEGIS-PQ workspace and deployed to the live PYNQ-Z2 testbed at `192.168.0.2`.

The hardware design (`design_1.bit` / `design_1.hwh`) contains a functional Vivado HLS-synthesized streaming arithmetic core (`kyber_accelerator_top:1.0`) connected via AXI4-Stream to a Xilinx AXI DMA engine (`axi_dma:7.1`) clocked at **50.0 MHz**. 

### Critical Cryptographic Clarification
- **What the IP is**: An isolated **polynomial arithmetic test pipeline** performing forward Number Theoretic Transform (NTT), Pointwise Multiplication (PWM) by a **hardcoded scalar constant** (`FIXED_SECRET = 3`), inverse NTT (iNTT), and Montgomery modular scaling by $3316 \equiv 256^{-1} \pmod{3329}$.
- **What the IP is NOT**: It is **not** a complete post-quantum Key Encapsulation Mechanism (ML-KEM / CRYSTALS-Kyber). It does **not** perform polynomial-matrix multiplication, does **not** accept dynamic secret keys over AXI, contains **no** SHA-3/Keccak/SHAKE hardware acceleration, does **not** implement Centered Binomial Distribution (CBD) sampling, and does **not** perform encapsulation (`crypto_kem_enc`) or decapsulation (`crypto_kem_dec`).
- **The "27x Speedup" Origin**: The reported $\approx 27.0\times$ acceleration figure is derived entirely from comparing the FPGA's DMA streaming pipeline ($\approx 1.19\text{ ms}$ per 256-coefficient polynomial pass) against an unoptimized, interpreted pure-Python reference loop running on the board's 667 MHz ARM Cortex-A9 processor ($\approx 32.26\text{ ms}$ per pass for 1000 iterations).

---

## 2. FPGA Bitstream & Hardware Description Verification

The local workspace bitstream and the bitstream deployed to `/home/xilinx/jupyter_notebooks/pqc_kyber512` on the physical PYNQ-Z2 board were verified via cryptographic SHA-256 checksums and are **100% byte-for-byte identical**.

| Property | `design_1.bit` | `design_1.hwh` |
| :--- | :--- | :--- |
| **Local Path** | `PQC Kyber/bitstream/design_1.bit` | `PQC Kyber/bitstream/design_1.hwh` |
| **Board Path** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/design_1.bit` | `/home/xilinx/jupyter_notebooks/pqc_kyber512/design_1.hwh` |
| **File Size** | 4,045,692 bytes (~4.05 MB) | 313,754 bytes (~313.8 KB) |
| **Timestamp** | 2026-01-19 14:29:31 | 2026-01-19 14:24:48 |
| **SHA-256 Hash** | `bb712fc45ab6e328258a4304c6e2718b5c1711bdd9436ad9a24dc1307fbfa98a` | `7a98716f797cd6ee5eb059bbc4c71a811c2228416bf412ed96407a37b9d0e207` |
| **EDA Tool** | Vivado 2025.1 | Vivado 2025.1 |
| **Target Device** | Zynq-7000 (`7z020`), Package `clg400`, Speed `-1` | Zynq-7000 (`7z020`), Package `clg400`, Speed `-1` |

---

## 3. Vivado Block Design Architecture & Interconnect

The hardware design consists of six core modules instantiated on the Zynq Programmable Logic (PL) fabric:

```
+-----------------------------------------------------------------------------------+
|                              Processing System 7                                  |
|                           (Dual ARM Cortex-A9 @ 667 MHz)                         |
|                                                                                   |
|    +-------------------+                             +--------------------+       |
|    | M_AXI_GP0 (50MHz) |                             | S_AXI_HP0 (50MHz)  |       |
+----+---------+---------+-----------------------------+---------+----------+-------+
               |                                                 ^
               v                                                 |
+--------------+------------------+             +----------------+------------------+
|      axi_smc (SmartConnect)     |             |  axi_mem_intercon (Interconnect)  |
+-------+------------------+------+             +--------+-----------------+--------+
        |                  |                             |                 |
        | AXI4-Lite        | AXI4-Lite                   | AXI4 MM2S Read  | AXI4 S2MM Write
        v                  v                             |                 |
+-------+----------+  +----+---------------------+       |                 |
| kyber_accelerator|  |        axi_dma_0         |-------+                 |
| _top_0           |  |     (AXI DMA v7.1)       |-------------------------+
| (HLS Accelerator)|  +----+-----------------+---+
+-------+----------+       |                 ^
        ^                  | AXI4-Stream     | AXI4-Stream
        |                  | (32-bit TDATA)  | (32-bit TDATA)
        |                  v                 |
        +------------------+ INPUT_DMA       |
        +------------------------------------+ OUTPUT_DMA
```

### Module Inventory (`design_1.hwh`)

1. **`processing_system7_0`** (`xilinx.com:ip:processing_system7:5.5`)
   - CPU Clock (`PCW_APU_PERIPHERAL_FREQMHZ`): **666.666687 MHz**
   - PL Fabric Clock 0 (`PCW_FPGA0_PERIPHERAL_FREQMHZ` / `FCLK_CLK0`): **50.000000 MHz**
   - DDR Controller: 512 MB DDR3 memory space mapped to `0x00100000` - `0x1FFFFFFF`.
   - Master AXI Interface: `M_AXI_GP0` (32-bit AXI4-Lite, 50 MHz).
   - Slave AXI Interface: `S_AXI_HP0` (32-bit High-Performance direct DDR access, 50 MHz).

2. **`rst_ps7_0_50M`** (`xilinx.com:ip:proc_sys_reset:5.0`)
   - Generates synchronous reset signals for the 50 MHz PL clock domain (`slowest_sync_clk` connected to `FCLK_CLK0`).

3. **`axi_dma_0`** (`xilinx.com:ip:axi_dma:7.1`)
   - Scatter-Gather Engine: **Disabled** (`C_INCLUDE_SG = 0`). Operates in **Direct Register / Simple DMA Mode**.
   - MM2S (Memory-to-Stream) Channel: 32-bit burst size 32, streaming 32-bit words (`C_M_AXIS_MM2S_TDATA_WIDTH = 32`).
   - S2MM (Stream-to-Memory) Channel: 32-bit burst size 32, receiving 32-bit words (`C_S_AXIS_S2MM_TDATA_WIDTH = 32`).
   - AXI-Lite Base Address: `0x41E00000` (Range: 64 KB).

4. **`kyber_accelerator_top_0`** (`xilinx.com:hls:kyber_accelerator_top:1.0`)
   - Synthesized top-level Vivado HLS IP core.
   - Clock: `ap_clk` connected to `processing_system7_0_FCLK_CLK0` (50 MHz).
   - Control Interface: `s_axi_CTRL_BUS` mapped to `0x40000000` (Range: 64 KB).
   - Input Stream: `INPUT_DMA` (AXI4-Stream, 32-bit data width).
   - Output Stream: `OUTPUT_DMA` (AXI4-Stream, 32-bit data width with `TLAST` asserted on sample 255).

5. **`axi_smc`** (`xilinx.com:ip:smartconnect:1.0`)
   - Connects PS `M_AXI_GP0` to both `axi_dma_0/S_AXI_LITE` and `kyber_accelerator_top_0/s_axi_CTRL_BUS`.

6. **`axi_mem_intercon`** (`xilinx.com:ip:axi_interconnect:2.1`)
   - Arbitrates MM2S read and S2MM write masters from `axi_dma_0` into the PS `S_AXI_HP0` port.

---

## 4. Hardware Accelerator Register Map & Interfaces

### 4.1 Kyber IP Control Register Map (`0x40000000`)

The HLS core uses the standard Xilinx AXI-Lite slave protocol bundle (`CTRL_BUS`):

| Offset | Register Name | Access | Bitfields & Operational Description |
| :--- | :--- | :--- | :--- |
| **`0x00`** | **`CTRL`** | R/W | **Bit 0 (`ap_start`)**: Write `1` to start execution. Self-clears when done.<br>**Bit 1 (`ap_done`)**: Read-only. Hardware asserts `1` when computation finishes.<br>**Bit 2 (`ap_idle`)**: Read-only. Asserts `1` when accelerator is idle.<br>**Bit 3 (`ap_ready`)**: Read-only. Asserts `1` when IP can accept new inputs.<br>**Bit 7 (`auto_restart`)**: R/W. If set to `1`, core restarts automatically. |
| **`0x04`** | **`GIER`** | R/W | **Global Interrupt Enable Register**.<br>Bit 0: Master interrupt enable (0 = disabled, 1 = enabled). |
| **`0x08`** | **`IP_IER`** | R/W | **IP Interrupt Enable Register**.<br>Bit 0: Enable `ap_done` interrupt.<br>Bit 1: Enable `ap_ready` interrupt. |
| **`0x0C`** | **`IP_ISR`** | R/TOW | **IP Interrupt Status Register** (Toggle-on-write-1 to clear).<br>Bit 0: `ap_done` interrupt pending.<br>Bit 1: `ap_ready` interrupt pending. |

> **Crucial Implementation Note**: While the HLS IP exposes interrupt registers (`0x04` - `0x0C`), the physical hardware interrupt line `kyber_accelerator_top_0/interrupt` is **not connected** to the Zynq Processing System `IRQ_F2P` bus in `design_1.hwh` (`SIGNAME = None`). All PYNQ interactions must use polled status or rely on DMA channel polling.

### 4.2 AXI DMA Register Map (`0x41E00000`)

| Offset | Register | Description | Usage in PYNQ |
| :--- | :--- | :--- | :--- |
| **`0x00`** | `MM2S_DMACR` | Memory-to-Stream Control Register | Set Bit 0 (`RS=1`) to run channel |
| **`0x04`** | `MM2S_DMASR` | Memory-to-Stream Status Register | Bit 1 (`Idle`), Bit 0 (`Halted`) |
| **`0x18`** | `MM2S_SA` | MM2S Source Buffer Physical Address | Written with physical address of input CMA buffer |
| **`0x28`** | `MM2S_LENGTH` | MM2S Transfer Length (bytes) | Written with `1024` (triggers transfer) |
| **`0x30`** | `S2MM_DMACR` | Stream-to-Memory Control Register | Set Bit 0 (`RS=1`) to run channel |
| **`0x34`** | `S2MM_DMASR` | Stream-to-Memory Status Register | Bit 1 (`Idle`), Bit 0 (`Halted`) |
| **`0x48`** | `S2MM_DA` | S2MM Destination Buffer Phys Address | Written with physical address of output CMA buffer |
| **`0x58`** | `S2MM_LENGTH` | S2MM Transfer Length (bytes) | Written with `1024` (triggers receive) |

> **Hardware Interrupt Finding**: Similar to the Kyber core, `axi_dma_0/mm2s_introut` and `s2mm_introut` are **unconnected** (`SIGNAME = None`). Dashboard claims stating `awaiting done IRQ` are architectural simplifications; the runtime polls MMIO status bits.

---

## 5. Algorithmic & Cryptographic Implementation Analysis

The source code for the accelerator is located in `PQC Kyber/src/kyber_accelerator.cpp`.

### 5.1 Polynomial Parameters
- Polynomial Degree: $N = 256$
- Prime Modulus: $Q = 3329$
- Montgomery Constants:
  - $R = 2^{16} \pmod{3329} = 2285$
  - $QINV = -3327 \equiv -Q^{-1} \pmod{2^{16}}$
  - Inverse scaling factor: $3316 \equiv 256^{-1} \cdot R \pmod{3329}$
- Zeta Table: 128 verified precomputed twiddle factors (`zetas[128]`) for the radix-2 decimation-in-time NTT.

### 5.2 Internal Pipeline Architecture

The top-level function `kyber_accelerator_top` utilizes `#pragma HLS DATAFLOW` with five stages connected via four internal FIFOs (`pipe_1` to `pipe_4`, depth = 256):

```
INPUT_DMA ---> [Stage 1: Load] ---> pipe_1 ---> [Stage 2: NTT] ---> pipe_2
                                                                       |
OUTPUT_DMA <-- [Stage 5: Store] <-- pipe_4 <-- [Stage 4: iNTT] <-- pipe_3 <-- [Stage 3: PWM]
```

1. **Stage 1 (`load_data_wrapper`)**:
   - Reads 256 packets from `INPUT_DMA`.
   - Modulo reduces: `p.data % Q` $\to$ written to `pipe_1`.
2. **Stage 2 (`run_ntt_wrapper`)**:
   - Reads 256 coefficients into local LUTRAM buffer (`#pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=lutram`).
   - Performs Cooley-Tukey radix-2 NTT in-place over 7 butterfly loops (`len = 128` down to `2`).
   - Writes 256 NTT-domain coefficients to `pipe_2`.
3. **Stage 3 (`run_pwm_wrapper`) — CRITICAL HARDWARE CONSTANT**:
   ```cpp
   // Line 114: Hardcoded scalar secret
   static const int16_t FIXED_SECRET = 3; 

   for(int i = 0; i < N; i++) {
       #pragma HLS PIPELINE II=1
       int16_t val = in_stream.read();
       int16_t res = montgomery_reduce((int32_t)val * (FIXED_SECRET * 2285));
       out_stream.write(res); 
   }
   ```
   **Architectural Limitation**: The Pointwise Multiplication stage does **not** multiply two polynomials together $a(x) \circ s(x)$, nor does it accept an external secret key polynomial. It multiplies every coefficient in the single input polynomial by the **hardcoded scalar integer 3**.
4. **Stage 4 (`run_intt_wrapper`)**:
   - Reads 256 coefficients into local LUTRAM buffer.
   - Performs Gentleman-Sande radix-2 inverse NTT over 7 loops (`len = 2` up to `128`) using reversed zetas.
   - Scales each coefficient by $3316 \equiv 256^{-1}$ via Montgomery multiplication.
   - Writes to `pipe_4`.
5. **Stage 5 (`store_data_wrapper`)**:
   - Reads from `pipe_4`, applies final non-negative reduction (`if (val < 0) val += Q`), formats 32-bit AXI packet with `p.last = (i == 255)`, and pushes to `OUTPUT_DMA`.

### 5.3 Mathematical Equivalent Operation

Because the forward NTT and inverse NTT are exact linear mathematical inverses, and because multiplication by a scalar in the NTT domain is equivalent to scalar multiplication in the standard polynomial domain:

$$\text{Output}(x) = \text{iNTT}(\text{NTT}(P(x)) \times 3) \equiv (3 \cdot P(x)) \pmod{3329}$$

The hardware IP is therefore an end-to-end testbench pipeline verifying that the NTT and iNTT logic correctly round-trip without corruption.

---

## 6. Memory & DMA Buffer Requirements

To execute a hardware transfer, the host processor must allocate physically contiguous, uncached DMA memory using the Linux Contiguous Memory Allocator (CMA) via `pynq.allocate`:

- **Input Buffer**: `allocate(shape=(256,), dtype=np.uint32)`
  - Size: $256 \times 4\text{ bytes} = 1024\text{ bytes}$ ($1\text{ KB}$).
  - Alignment: 32-bit word aligned.
- **Output Buffer**: `allocate(shape=(256,), dtype=np.uint32)`
  - Size: $256 \times 4\text{ bytes} = 1024\text{ bytes}$ ($1\text{ KB}$).
- **Streaming Transfer Execution**:
  ```python
  kyber_ip.write(0x00, 0x01) # ap_start
  dma.sendchannel.transfer(input_buffer)
  dma.recvchannel.transfer(output_buffer)
  dma.sendchannel.wait()
  dma.recvchannel.wait()
  ```

### The "Zombie State" Hazard & Watchdog Solution
In stock PYNQ, `dma.sendchannel.wait()` and `dma.recvchannel.wait()` take no timeout argument and block unconditionally. If the IP fails to emit the `TLAST` frame delimiter or if fewer than 256 words are transferred, the DMA engine hangs indefinitely, freezing the entire Python process.

In `kyber_hal.py` (and `kyber_hal_board.py`), this was solved by executing `.wait()` inside a persistent `ThreadPoolExecutor(max_workers=2)` wrapped with a `3.0s` timeout:
```python
future = self._wait_pool.submit(channel.wait)
future.result(timeout=self.dma_timeout) # Raises HardwareTimeout on freeze
```

---

## 7. Clock Constraints and Synthesis Targets

From Vivado hardware handoff XML parameters:
- **Processor APU Frequency**: 666.67 MHz
- **FPGA PL Clock (`FCLK_CLK0`)**: **50.000000 MHz**
- **Clock Period**: $T = 20.0\text{ ns}$
- **Pipeline Latency**:
  - Load: 256 cycles
  - NTT: $\approx 7 \times 128 = 896$ butterfly cycles
  - PWM: 256 cycles
  - iNTT: $\approx 896$ butterfly cycles + 256 scaling cycles
  - Store: 256 cycles
  - Dataflow pipelined throughput: After initial fill, produces 1 coefficient per clock cycle ($20\text{ ns}$). Total core computation time is approximately **50 to 60 microseconds** ($\approx 2500\text{ cycles} \times 20\text{ ns}$).

---

## 8. Decomposition of the "27x Acceleration" Claim

The workspace documentation and pitch materials emphasize a **"27.0x Faster on FPGA"** metric. The origin and breakdown of this figure is proven directly from `PQC Kyber/src/Jupyter Notebook Codes for PQC Kyber.py` and `Final_KYBER.ipynb`:

| Metric | Software Baseline (CPU) | Hardware Accelerated (FPGA) | Speedup Ratio |
| :--- | :--- | :--- | :--- |
| **Execution Platform** | ARM Cortex-A9 @ 667 MHz | Zynq PL Fabric @ 50 MHz + AXI DMA | — |
| **Implementation** | Pure Python interpreted loops | Vivado HLS C++ RTL via AXI DMA | — |
| **1000 Iterations Time** | **32.26 s** (or 33.10 s in notebook run) | **1.19 s** (or 1.09 s in notebook run) | **27.1x** (up to 30.3x) |
| **Latency per Transform** | **32.26 ms** | **1.19 ms** | **27.1x** |

### Critical Engineering Observations on the 27x Claim
1. **DMA Transfer Overhead Dominance**: The PL core takes $\approx 0.05\text{ ms}$ to compute the math. The remaining $\approx 1.14\text{ ms}$ of the $1.19\text{ ms}$ FPGA latency is consumed by Linux user-space DMA driver transitions, buffer cache flushes, and MMIO register polling.
2. **Software Reference Disparity**: The software baseline is implemented in unvectorized, interpreted Python with nested `while` and `for` loops invoking dynamic method calls. An optimized C or NEON SIMD implementation of Kyber NTT on ARM Cortex-A9 typically executes in $\approx 10\text{ to }20\text{ microseconds}$.
3. **Factual Boundary for Technical Presentations**: The 27x figure is **genuine and reproducible** against the provided Python reference benchmark, but represents an arithmetic primitive benchmark rather than an entire cryptographic handshake speedup.

---

## 9. Architectural Comparison: Current IP vs. Complete ML-KEM

| Feature / Primitive | Current Hardware IP (`kyber_accelerator_top`) | Full ML-KEM / FIPS 203 Specification |
| :--- | :--- | :--- |
| **Modulus / Degree** | $N=256, Q=3329$ (Compliant) | $N=256, Q=3329$ |
| **Forward NTT / iNTT** | Implemented in RTL (Compliant) | Required for polynomial arithmetic |
| **Secret Key Input** | **Hardcoded scalar (`3`)** | Dynamic $k \times k$ polynomial matrix / vector |
| **Vector Dimension $k$** | $k=1$ (single polynomial only) | $k=2$ (ML-KEM-512), $k=3$ (768), $k=4$ (1024) |
| **Polynomial Mult** | Scalar PWM only | Full vector dot-products $\mathbf{A} \cdot \mathbf{s} + \mathbf{e}$ |
| **Keccak / SHA-3** | **None** in hardware | SHAKE-128, SHAKE-256, SHA3-256, SHA3-512 |
| **CBD Noise Sampler** | **None** in hardware | Centered Binomial Distribution ($\eta_1, \eta_2$) |
| **Key Generation** | **None** | $d \to (pk, sk)$ via SHAKE & matrix expansion |
| **Encapsulation** | **None** | $pk \to (ct, ss)$ via PRF & matrix multiplication |
| **Decapsulation** | **None** | $sk, ct \to ss$ with Fujisaki-Okamoto verification |

---

## 10. Conclusion & Recommendations

1. **Hardware Integrity**: The bitstream and HLS IP represent a stable, working polynomial pipeline verified on live silicon. It successfully validates that the PYNQ-Z2 fabric can stream polynomials across AXI DMA without bus errors.
2. **Preservation**: The bitstream `design_1.bit` must remain intact as the validated baseline hardware.
3. **Integration Strategy**: For the multi-device demo (AEGIS-PQ), the full ML-KEM state machine (matrix generation, noise sampling, FO-transform, session key derivation) must execute in optimized Python/C on the ARM PS or host gateway, delegating polynomial NTT/iNTT transformations to the FPGA accelerator where applicable.
