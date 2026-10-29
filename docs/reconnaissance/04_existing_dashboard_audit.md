# Existing Dashboard Audit & Preservation Guide

**Document ID**: `04_existing_dashboard_audit.md`  
**Target Component**: PYNQ-Z2 Kyber-512 Accelerator Dashboard  
**Status**: Verified via Code Inspection & Live Board Telemetry  
**Date**: 2026-10-30  

---

## 1. Executive Summary

This document audits the pre-existing PYNQ-Z2 web dashboard application designed to demonstrate the Kyber-512 FPGA accelerator. It documents file locations, architecture, endpoint contracts, hardware access patterns, and defines strict non-destructive coexistence rules to ensure that future laptop receiver interfaces and three-device network integrations operate without disrupting the existing stage-demo capability.

---

## 2. File Inventory & Runtime Environment

The dashboard is a self-contained, lightweight Flask web application located on both the physical board and synchronized in the local workspace.

### 2.1 File Locations and Mapping

| Role | Board Location (`192.168.0.2`) | Local Workspace Copy | Size / Timestamp |
| :--- | :--- | :--- | :--- |
| **Flask Server** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/app.py` | `app_board.py` | 6,658 bytes (Jul 8 04:25) |
| **Hardware Abstraction** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/kyber_hal.py` | `kyber_hal_board.py` | 13,302 bytes (Jul 8 04:25) |
| **Frontend UI Template** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/templates/index.html` | — | 24,862 bytes (Jul 7 11:21) |
| **Documentation** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/README.md` | `board_README.md` | 3,667 bytes (Jul 7 04:04) |
| **Dependencies** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/requirements.txt` | — | 191 bytes (Jul 7 11:13) |
| **Server Log** | `/home/xilinx/jupyter_notebooks/pqc_kyber512/server.log` | — | 86,065 bytes (Oct 15 12:08) |

### 2.2 Runtime Environment

- **Host Platform**: PYNQ-Z2 Linux (`Linux pynq 5.4.0-xilinx-v2020.2 armv7l`, Ubuntu 20.04 LTS).
- **Python Environment**: System PYNQ virtualenv at `/usr/local/share/pynq-venv/bin/python3` (Python 3.8.10, PYNQ 2.7.0).
- **Dependencies**: `flask>=3.0`, `Pillow>=9.0`, `pynq==2.7.0`, `numpy`.
- **Network Binding**: Listens on `0.0.0.0:5000` (HTTP).
- **Service Invocation**: Spawned either manually via terminal (`python3 app.py`) or programmatically from Jupyter notebook `Final_KYBER.ipynb` Cell 1:
  ```python
  server = subprocess.Popen(
      [sys.executable, "app.py"],
      cwd="/home/xilinx/jupyter_notebooks/pqc_kyber512",
      stdout=open("server.log", "w"),
      stderr=subprocess.STDOUT,
  )
  ```

---

## 3. UI Features & Visual Layout

As confirmed by visual analysis of `PQC Kyber/src/Screenshot 2026-07-07 162306.png` and `Screenshot 2026-07-07 165250.png`, the dashboard provides three functional panels:

### 3.1 Live Verification Panel (`◆ LIVE VERIFICATION`)
- **Action**: "Run verification" button.
- **Sanity Check**: "Force a mismatch (sanity check)" checkbox (deliberately corrupts coefficient `0` to demonstrate that error detection is authentic).
- **Console Log**: Displays simulated PS-to-PL register transactions:
  - `> PS -> PL: writing control register 0x00 <- 0x01 (ap_start)`
  - `> Generating deterministic test vector (256 x uint32)`
  - `> AXI DMA: streaming 1024 bytes to PL, awaiting done IRQ`
  - `> Comparing 256 coefficients against the software NTT model`
- **Result Displays**:
  - Green banner: `Hardware matches the software model exactly — 256/256`.
  - Dynamic SVG / HTML5 Canvas waveform fingerprint showing 256 normalized coefficients.
  - Interactive table showing Index (`0..255`), HW value, SW value, and Status (`OK` / `FAIL`).

### 3.2 Performance Benchmark Panel (`◆ PERFORMANCE BENCHMARK`)
- **Action**: "Run benchmark" button.
- **Iterations Dropdown**: Selects 100 iterations (~15s) or 1000 iterations (~2 min).
- **Metric Card**: Prominent large-format readout:
  - **`27.0x`** `FASTER ON FPGA`
  - `32.26 s` `ARM CPU total`
  - `1.19 s` `FPGA total`

### 3.3 Secure Image Transmission Panel (`◆ SECURE IMAGE TRANSMISSION`)
- **Action**: "Choose File" and "Secure this image" button.
- **Visuals**: Slices uploaded image into an $8 \times 8$ grid (64 tiles). Renders the original tile grid alongside the FPGA-encrypted tile grid.
- **Summary Metrics**:
  - `1.2x Speedup, 64 keys`
  - `Pixel-exact Decrypt round trip`
  - `3.464 s HW time / 64 tiles`

---

## 4. REST API Endpoint Specification

The dashboard exposes seven REST routes implemented in `app.py`:

| Method | Path | Request Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | None | HTML | Serves `templates/index.html` (zero CDN dependencies) |
| `GET` | `/api/status` | None | `{"ready": bool, "bitstream": str}` | Health check; polled by frontend every 5 seconds |
| `POST` | `/api/reset` | None | `{"ok": bool, "error": str}` | Reloads bitstream overlay without restarting process |
| `POST` | `/api/verify` | `{"inject_fault": bool}` | `{"success": bool, "errors": int, "total": 256, "rows": [...]}` | Executes 1 HW pass + golden model comparison |
| `POST` | `/api/benchmark/start`| `{"iterations": int}` | `{"started": bool, "error": str}` | Launches asynchronous benchmarking thread |
| `GET` | `/api/benchmark/status`| None | `{"running": bool, "phase": str, "done": int, "total": int, "result": {...}}` | Polls progress and benchmark timings |
| `POST` | `/api/image/secure` | `multipart/form-data` (`image`) | `{"tile_count": 64, "speedup": float, "restored_exactly": bool, "original_tiles": [...], "encrypted_tiles": [...]}` | 64-tile image encryption demonstration |

---

## 5. Hardware Access Mechanism: The `KyberHAL` Architecture

The dashboard replaces script-level overlay reloading with a persistent singleton architecture implemented in `kyber_hal.py`:

```
+-------------------------------------------------------------+
|                      Flask app.py                           |
+------------------------------+------------------------------+
                               | Calls methods
                               v
+-------------------------------------------------------------+
|                      KyberHAL Singleton                     |
|                                                             |
|  - Holds resident Overlay("design_1.bit")                   |
|  - Allocates 1024-byte input & output CMA buffers once       |
|  - Mutex lock (self.lock) preventing concurrent DMA calls    |
|  - ThreadPoolExecutor(max_workers=2) for DMA timeouts        |
+------------------------------+------------------------------+
                               | AXI4-Lite & AXI-Stream
                               v
+-------------------------------------------------------------+
|              PYNQ Overlay (axi_dma_0, kyber_ip)             |
+-------------------------------------------------------------+
```

### Critical Innovations in `KyberHAL`:
1. **Resident Overlay**: PYNQ's `Overlay()` takes several seconds to reconfigure FPGA fabric via `/dev/xdevcfg`. `KyberHAL` loads it once at boot and keeps it resident in memory.
2. **Watchdog Protected Waits**: The method `_wait_with_timeout(channel, label)` delegates DMA completion waits to a background thread pool with a 3.0-second timeout. If the IP hangs (e.g. missing `TLAST`), it raises `HardwareTimeout` instead of locking the entire Python process into an unrecoverable zombie state.
3. **Optimized Benchmarking Loop**: For tight loops, `_run_once_raw_timed()` bypasses lock acquisition and thread-pool wrappers, matching the execution profile of native C DMA calls.

---

## 6. Analysis of Live vs. Simulated Telemetry

A rigorous forensic audit of the dashboard implementation confirms which behaviors interact with real hardware versus where mathematical or architectural abstractions are used:

| Dashboard Feature | Hardware Interaction Nature | Forensic Assessment |
| :--- | :--- | :--- |
| **Status Indicator** | Live Board Check | Inspects `hal.ready` and verifies FPGA overlay status. |
| **Live Verification Table** | **100% Real Hardware** | Generates test vector $(7i + 3) \bmod 3329$, transfers 1024 bytes across DMA to PL, reads 1024 bytes back, and validates value-by-value against Python golden model. |
| **Console Log IRQ String** | **Simulated Text** | Console outputs `awaiting done IRQ`, but hardware analysis reveals interrupt lines are physically unconnected; DMA completion is polled. |
| **Benchmark Timings** | **100% Real Hardware** | Measures wall-clock execution of 1000 real DMA transfers against 1000 software iterations. |
| **27x Speedup Metric** | **Factual vs. Reference** | Real ratio of pure Python software loop to FPGA DMA stream; not a speedup against optimized C/Assembly. |
| **Image Encryption** | **Hybrid / Toy Crypto** | Real FPGA execution (streams 64 polynomial tiles through PL), but cryptographic application is a **simple XOR stream cipher** using $P(x) \bmod 256$ as a keystream, **not** genuine ML-KEM encapsulation or AES-GCM. |

---

## 7. Non-Destructive Coexistence Rules

To satisfy the project requirements and preserve this existing, working dashboard for stage demonstrations, all future integration services (including the three-device demonstration daemon, laptop receiver interfaces, and telemetry collectors) must strictly adhere to the following coexistence rules:

### Rule 1: Port Allocation Isolation
- The existing dashboard claims **TCP Port 5000**.
- **Requirement**: No other service or daemon may bind to port 5000 on the PYNQ-Z2 board.
- Any secondary service (e.g. AEGIS-PQ node gateway or API relay) must bind to a dedicated, distinct port (e.g., **Port 5001** or **Port 8080**).

### Rule 2: Single-Process Overlay Ownership
- Linux and Xilinx DMA drivers allow only **one process** to hold open file descriptors to `/dev/xdevcfg` and contiguous memory buffers (`/dev/cma`) without bus collisions.
- **Requirement**: Never invoke `Overlay("design_1.bit")` from a second competing Python process while `app.py` is running.
- **Integration Mechanism**: If a secondary daemon needs hardware acceleration, it should either:
  1. Call into `app.py`'s existing REST API (`POST /api/verify`), OR
  2. Integrate modular route extensions directly into `app.py` calling the existing `hal` instance, OR
  3. Ensure `app.py` is stopped before running standalone CLI test scripts.

### Rule 3: File System Integrity & Preservation
- Do not modify, overwrite, or rename `app.py`, `kyber_hal.py`, or `templates/index.html` in `/home/xilinx/jupyter_notebooks/pqc_kyber512`.
- All new scripts and integration harnesses must reside in designated subdirectories or separate packages.

### Rule 4: Zero-Footprint Remote Access
- Remote laptop receivers must interact with the PYNQ board strictly over HTTP (`GET /api/status`, `POST /api/verify`) or non-intrusive SSH commands.
- Do not install conflicting global Python packages on the board.
