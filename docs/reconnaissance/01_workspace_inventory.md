# Reconnaissance Report 01: Complete Workspace Inventory & Baseline Review

**Document Reference:** `docs/reconnaissance/01_workspace_inventory.md`  
**Classification:** Authoritative Technical Reconnaissance  
**Author:** Teamwork Explorer 1 (Repo & Evolution Specialist)  
**Target Workspace:** `D:\Raja\College projects\PQC - ORION Hack`  
**Inspection Date:** 2026-10-29T19:25:00Z  
**Integrity Mode:** Strictly Non-Destructive / Read-Only  

---

## 1. Executive Summary

This report establishes the verified baseline inventory of the entire workspace repository at `D:\Raja\College projects\PQC - ORION Hack`. The workspace comprises 31 primary files across three evolutionary stages of the post-quantum cryptography project:
1. **Stage A (Legacy Silicon Hardware):** PYNQ-Z2 (Zynq-7020) hardware bitstream, hardware handoff XML, C++ HLS source code, and Python test harnesses.
2. **Stage B (PolarFire SoC Paper Proposal):** System design specifications, risk registers, and portal submission blocks for the Microchip PolarFire SoC Discovery Kit contest (`MPFS095T`).
3. **Stage C (ORION AI Finals Collateral):** Pitch decks, problem statement analyses, and demonstration design logs for the ORION AI Innovation Awards (Grand Finale at IIT Madras Research Park).

**Critical Finding on Repository Version Control:** The workspace root is a local directory without an active `.git` tracking repository (`git rev-parse --is-inside-work-tree` returned code 1). Chronological progression and version control are reconstructed via file system timestamps, embedded XML metadata, and historical conversational logs.

---

## 2. Directory Structure & File Hierarchy

```
D:\Raja\College projects\PQC - ORION Hack
├── .agents/                                  [Agent metadata and collaboration directories]
│   └── teamwork/
│       ├── BRIEFING.md
│       ├── ORIGINAL_REQUEST.md
│       ├── orchestrator_1/
│       ├── teamwork_explorer_survey_1/
│       ├── teamwork_explorer_survey_2/
│       └── teamwork_explorer_survey_3/
├── docs/                                     [Technical Documentation]
│   ├── development/
│   └── reconnaissance/                       [Reconnaissance Audit Reports 00 through 12]
│       └── README.md
├── PQC Kyber/                                [Stage A: Hardware Source, Bitstream & Outputs]
│   ├── bitstream/
│   │   ├── design_1.bit                      [Synthesized bitstream for Zynq-7020]
│   │   └── design_1.hwh                      [Hardware handoff file with register maps]
│   ├── docs/
│   │   ├── CRYSTALS Kyber & Dilithium Post-Quantum Cryptography (2).pptx [Presentation]
│   │   ├── KYBER - 512 Documentation.docx    [Technical report summary]
│   │   └── KYBER 512 Detailled Report.docx   [Comprehensive academic report]
│   ├── src/
│   │   ├── Final PL Output                   [PNG screenshot: Golden model verification]
│   │   ├── Jupyter Notebook Codes for PQC Kyber.py [Python PYNQ driver & harness]
│   │   ├── kyber_accelerator.cpp             [Vitis HLS C++ source code]
│   │   ├── Screenshot 2026-07-07 162306.png  [PNG screenshot: 27.0x speedup UI]
│   │   └── Screenshot 2026-07-07 165250.png  [PNG screenshot: 64-tile image demo UI]
│   └── video/
│       └── PQC DILITHIUM KYBER VIDEO DEMO.mp4 [Demonstration video recording]
├── Aegis-PQC Project Evolution and Roadmap.pdf [Stage B: Evolution analysis]
├── Aegis-PQC_Master_Proposal_v2(1).md        [Stage B: PolarFire master proposal v2]
├── Aegis-PQC_Portal_Text_Final.txt           [Stage B: Contest portal text]
├── ChatGPT-Branch · ORION AI - Analyze Award Criteria-20261024-1508.pdf [Rubric analysis]
├── Cyber_Shield_AI_Pitch_Deck_Redesigned.pdf [Stage C: Alternative pitch deck]
├── Migrating Legacy Systems to PQC.pdf       [Domain Research: Enterprise migration whitepaper]
├── ORION_TEMPLATE.pdf                        [Contest Submission: Official slide template]
├── Photonics_ORION AI FInals.pdf             [Stage C: Authoritative finals pitch deck]
├── Photonics_ORION AI.jpg                    [Stage C: Architectural graphic]
├── Photonics_ORION AI.pdf                    [Stage C: Initial draft pitch deck]
├── PITCH_PQC_ORION.pdf                       [Stage C: Initial screening pitch deck]
├── Post-Quantum Cryptography Migration Challenges.pdf [Domain Research: Embedded PQC bottlenecks]
├── Post-Quantum Cryptography Standards and Adoption.pdf [Domain Research: NIST standards report]
├── PQC - SNIC, Orion, DevFest.pdf            [Cross-Event Positioning: SmartNIC / Inline Engine]
├── PQC FPGA Demo Strategy.pdf                [Stage C: 19-jury demo strategy]
├── PQC Orion implentation.pdf                [Stage C: Authoritative 3-device demo transcript]
├── pqc_orion_img (1).pdf                     [Visual Graphic Asset]
├── pqc_orion_img (2).pdf                     [Visual Graphic Asset]
├── pqc_orion_img.pdf                         [Visual Graphic Asset]
└── Problem Statement (1).pdf                 [Contest Document: Domain 02 specification]
```

---

## 3. Comprehensive File Inventory & Categorization Table

All files in the workspace are cataloged below with exact byte counts, modification timestamps, format types, and functional categorization:
- **Active:** Essential operational files currently executable on hardware or active development documents.
- **Historical:** Provenance artifacts, previous academic submissions, or benchmark outputs.
- **Experimental / Proposed:** Paper co-designs, contest proposals, or candidate demo architectures.
- **Strategic Documentation:** Market research, contest rubrics, and competitive strategy decks.

| # | File Path | Format | Size (Bytes) | Last Modified (UTC) | Category | Functional Purpose & Technical Role |
|---|-----------|--------|--------------|---------------------|----------|-------------------------------------|
| 1 | `PQC Kyber/bitstream/design_1.bit` | Binary (`.bit`) | 4,045,692 | 2026-01-19 14:29:31 | **Active HW** | Synthesized FPGA bitstream targeting Xilinx XC7Z020-CLG400-1 (PYNQ-Z2). Contains `kyber_accelerator_top_0` and `axi_dma_0`. |
| 2 | `PQC Kyber/bitstream/design_1.hwh` | XML (`.hwh`) | 313,754 | 2026-01-19 14:24:48 | **Active HW** | Hardware handoff specification defining AXI bus interconnects, memory base addresses (`0x40000000`), register bitfields, and PL clock frequency (50.0 MHz via `PCW_FPGA0_PERIPHERAL_FREQMHZ = 50`). |
| 3 | `PQC Kyber/src/kyber_accelerator.cpp` | C++ (`.cpp`) | 7,692 | 2026-06-10 15:22:14 | **Active Source** | Authoritative Vitis HLS source implementing a 5-stage DATAFLOW pipeline (Load $\rightarrow$ NTT $\rightarrow$ PWM $\rightarrow$ iNTT $\rightarrow$ Store) with LUTRAM memory binding. |
| 4 | `PQC Kyber/src/Jupyter Notebook Codes for PQC Kyber.py` | Python (`.py`) | 11,113 | 2026-07-20 16:28:42 | **Active Source** | PYNQ host driver script containing the bit-accurate Python Golden Model, 1000-iteration benchmark harness, and the `app.py` server launcher on port 5000. |
| 5 | `PQC Kyber/src/Final PL Output` | PNG (`.png`) | 12,930 | 2026-06-10 15:22:14 | **Historical Artifact** | Graphic evidence showing terminal verification output confirming 256/256 coefficient match between FPGA hardware and software golden model. |
| 6 | `PQC Kyber/src/Screenshot 2026-07-07 162306.png` | PNG (`.png`) | 236,134 | 2026-07-07 16:23:06 | **Historical Artifact** | Visual evidence of PYNQ web dashboard showing "27.0x FASTER ON FPGA" metric (ARM CPU total: 32.26s, FPGA total: 1.19s) and coefficient fingerprint chart. |
| 7 | `PQC Kyber/src/Screenshot 2026-07-07 165250.png` | PNG (`.png`) | 170,030 | 2026-07-07 16:52:50 | **Historical Artifact** | Visual evidence of PYNQ web dashboard showing "Secure Image Transmission" tab with 64 sliced tiles encrypted in 3.464 seconds. |
| 8 | `PQC Kyber/docs/KYBER 512 Detailled Report.docx` | DOCX (`.docx`) | 4,347,045 | 2026-07-20 16:21:32 | **Historical Tech Report** | Comprehensive academic report detailing Zynq-7000 SoC architecture, LUTRAM dual-port conflict resolution, Montgomery reduction, and 0.436W power measurements. |
| 9 | `PQC Kyber/docs/KYBER - 512 Documentation.docx` | DOCX (`.docx`) | 178,871 | 2026-07-20 16:19:22 | **Historical Tech Report** | Condensed technical document outlining arithmetic engine boundaries, dataflow schedule, and future Keccak/CBD integration requirements. |
| 10 | `PQC Kyber/docs/CRYSTALS Kyber & Dilithium Post-Quantum Cryptography (2).pptx` | PPTX (`.pptx`) | 10,675,578 | 2026-07-13 01:05:28 | **Historical Presentation** | 13-slide technical presentation comparing Kyber-512 and Dilithium implementations on PYNQ-Z2; documents Dilithium software timings. |
| 11 | `PQC Kyber/video/PQC DILITHIUM KYBER VIDEO DEMO.mp4` | MP4 (`.mp4`) | 84,256,579 | 2026-06-10 15:09:57 | **Historical Media** | Video demonstration of physical PYNQ-Z2 board execution and terminal verification. |
| 12 | `Aegis-PQC_Master_Proposal_v2(1).md` | Markdown (`.md`) | 45,510 | 2026-10-29 22:07:42 | **Stage B Proposal** | Master technical proposal for Microchip PolarFire SoC contest (Track 1). Contains dual-KEM co-processor design, 20-item risk register, and architectural decision matrix. |
| 13 | `Aegis-PQC_Portal_Text_Final.txt` | Text (`.txt`) | 5,731 | 2026-10-29 22:07:19 | **Stage B Proposal** | Word-count verified plain-text blocks for official PolarFire contest portal submission. |
| 14 | `Aegis-PQC Project Evolution and Roadmap.pdf` | PDF (`.pdf`) | 225,987 | 2026-10-29 21:40:18 | **Stage B Analysis** | Architectural evolution transcript documenting the transition from the "Everything Everywhere" kitchen-sink draft to the hardened Master Proposal v2. |
| 15 | `PQC Orion implentation.pdf` | PDF (`.pdf`) | 352,761 | 2026-10-30 00:19:32 | **Stage C Architectural Log** | Detailed transcript of the 3-device network demonstration design (Legacy Laptop 1 $\rightarrow$ PYNQ-Z2 $\rightarrow$ Cloud Laptop 2) and live cryptographic break strategy. |
| 16 | `PQC FPGA Demo Strategy.pdf` | PDF (`.pdf`) | 203,640 | 2026-10-29 22:34:43 | **Stage C Strategy** | Pitch and demo strategy deconstructing the 19-member ORION grand finale jury across four executive value clusters. |
| 17 | `Photonics_ORION AI FInals.pdf` | PDF (`.pdf`) | 19,598,698 | 2026-10-28 20:58:09 | **Stage C Final Deck** | Authoritative pitch deck for ORION AI Finals at IIT Madras Research Park. Brands project as "AEGIS-PQ Inline Offload Engine". |
| 18 | `Photonics_ORION AI.pdf` | PDF (`.pdf`) | 17,522,561 | 2026-10-24 18:08:46 | **Stage C Draft Deck** | Prior iteration of the finals slide deck; contains obsolete "Q-XRIDGE" branding on Slides 6 and 11. |
| 19 | `Photonics_ORION AI.jpg` | JPEG (`.jpg`) | 58,022 | 2026-10-24 18:11:39 | **Stage C Visual Graphic** | Block diagram illustration of the inline gateway architecture. |
| 20 | `Cyber_Shield_AI_Pitch_Deck_Redesigned.pdf` | PDF (`.pdf`) | 205,800 | 2026-10-25 11:37:05 | **Stage C Pitch Deck** | Redesigned pitch deck emphasizing the commercial cyber shield positioning. |
| 21 | `PITCH_PQC_ORION.pdf` | PDF (`.pdf`) | 3,156,398 | 2026-10-24 14:49:26 | **Stage C Pitch Deck** | Initial pitch deck submitted for the preliminary screening round. |
| 22 | `ORION_TEMPLATE.pdf` | PDF (`.pdf`) | 2,811,943 | 2026-10-24 15:26:42 | **Contest Submission** | Official ORION competition presentation template and guidelines. |
| 23 | `ChatGPT-Branch · ORION AI - Analyze Award Criteria-20261024-1508.pdf` | PDF (`.pdf`) | 21,765,228 | 2026-10-24 15:10:11 | **Evaluation Analysis** | Evaluation of award criteria, scoring rubric, and presentation strategy for the ORION hackathon. |
| 24 | `Migrating Legacy Systems to PQC.pdf` | PDF (`.pdf`) | 1,462,118 | 2026-10-29 21:51:32 | **Domain Research** | Comprehensive technical paper on industrial and enterprise migration to post-quantum cryptography. |
| 25 | `Post-Quantum Cryptography Standards and Adoption.pdf` | PDF (`.pdf`) | 1,216,245 | 2026-10-29 21:48:06 | **Domain Research** | Standards reference report documenting NIST FIPS 203/204/205 adoption mandates. |
| 26 | `Post-Quantum Cryptography Migration Challenges.pdf` | PDF (`.pdf`) | 1,246,711 | 2026-10-29 22:36:14 | **Domain Research** | Research paper detailing embedded processor bottlenecks, packet fragmentation, and handshake overheads. |
| 27 | `PQC - SNIC, Orion, DevFest.pdf` | PDF (`.pdf`) | 779,339 | 2026-10-29 22:35:15 | **Cross-Event Strategy** | Multi-venue strategy document framing the PQC accelerator as a SmartNIC / Inline Engine across SNIC, DevFest, and ORION. |
| 28 | `Problem Statement (1).pdf` | PDF (`.pdf`) | 20,631,111 | 2026-10-25 23:17:30 | **Contest Document** | Official problem statement specification for Domain 02 (Robotics, IoT & Embedded Systems). |
| 29 | `pqc_orion_img.pdf` | PDF (`.pdf`) | 13,843,059 | 2026-10-24 14:44:54 | **Visual Asset** | High-resolution architectural diagram assets and hardware render figures. |
| 30 | `pqc_orion_img (1).pdf` | PDF (`.pdf`) | 17,518,608 | 2026-10-25 14:00:45 | **Visual Asset** | Updated block diagram renders and visual figures. |
| 31 | `pqc_orion_img (2).pdf` | PDF (`.pdf`) | 17,225,083 | 2026-10-24 17:22:58 | **Visual Asset** | Supplementary system schematics and interface illustrations. |

---

## 4. Source-to-Hardware Lineage & Dependencies

The functional chain connecting high-level algorithm descriptions to bitstream execution is traced below:

```
[ Algorithmic Specification: NIST FIPS 203 / CRYSTALS-Kyber ]
                            │
                            ▼
[ C++ HLS Implementation: PQC Kyber/src/kyber_accelerator.cpp ]
  - Constants: Q = 3329, N = 256, FIXED_SECRET = 3, Zetas[128]
  - Math primitives: montgomery_reduce (QINV = -3327), barrett_reduce (20159)
  - Memory pragma: #pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=lutram
  - Top function: kyber_accelerator_top(axis_stream &INPUT_DMA, axis_stream &OUTPUT_DMA)
                            │
                            ▼ (Vivado HLS 2025.1 Synthesis & IP Export)
[ Vivado Block Design: PQC Kyber/bitstream/design_1.hwh ]
  - IP Core: kyber_accelerator_top_0 (VLNV: xilinx.com:hls:kyber_accelerator_top:1.0)
    - S_AXI_LITE register block: Range 64KB @ Base 0x40000000 (CTRL reg @ offset 0x00)
    - AXI4-Stream slave: INPUT_DMA connected to axi_dma_0 MM2S
    - AXI4-Stream master: OUTPUT_DMA connected to axi_dma_0 S2MM
  - DMA Engine: axi_dma_0 (VLNV: xilinx.com:ip:axi_dma:7.1)
  - Processor: processing_system7_0 (Zynq-7000 Cortex-A9 PS)
                            │
                            ▼ (Vivado Implementation & Bitstream Generation)
[ FPGA Bitstream: PQC Kyber/bitstream/design_1.bit ]
  - Device: AMD Xilinx XC7Z020-CLG400-1 (PYNQ-Z2)
  - Timestamp: Mon Jan 19 14:24:48 2026
                            │
                            ▼ (Runtime Driver Execution)
[ Python Host Harness: PQC Kyber/src/Jupyter Notebook Codes for PQC Kyber.py ]
  - PYNQ Overlay: ol = Overlay("design_1.bit")
  - DMA Channel Management: dma.sendchannel.transfer(input_buf) & dma.recvchannel.transfer(output_buf)
  - Hardware Trigger: kyber_ip.write(0x00, 0x01) (AP_START)
  - Golden Model: generate_golden_model(input_data) with software NTT, PWM, and iNTT
```

---

## 5. Strict Non-Destructive Preservation List

The following files represent verified, non-reproducible operational assets and reference models. **Any modification, overwriting, or deletion of these files will compromise the existing PYNQ-Z2 deployment and invalidate historical benchmarks.**

```
====================================================================================================================
AUTHORITATIVE ARTIFACT PRESERVATION REGISTER — DO NOT MODIFY OR OVERWRITE
====================================================================================================================

1. TARGET: PQC Kyber/bitstream/design_1.bit
   - Size: 4,045,692 bytes
   - SHA-256: BB712FC45AB6E328258A4304C6E2718B5C1711BDD9436AD9A24DC1307FBFA98A
   - Preservation Rationale: Pre-synthesized, verified bitstream. Rebuilding risks place-and-route timing violations.

2. TARGET: PQC Kyber/bitstream/design_1.hwh
   - Size: 313,754 bytes
   - SHA-256: 7A98716F797CD6EE5EB059BBC4C71A811C2228416BF412ED96407A37B9D0E207
   - Preservation Rationale: Defines register offsets and AXI routing needed by PYNQ Overlay.

3. TARGET: PQC Kyber/src/kyber_accelerator.cpp
   - Size: 7,692 bytes
   - SHA-256: 294E60662E5403806AEF13455E4C7C0C7EBE83FDF1028E9D735011939045F69D
   - Preservation Rationale: Exact HLS implementation of the 5-stage pipeline and Montgomery arithmetic.

4. TARGET: PQC Kyber/src/Jupyter Notebook Codes for PQC Kyber.py
   - Size: 11,113 bytes
   - SHA-256: 44FBFE1C221D801A78501CC1A13476F7EAEF48C82F26CBA35216D852679F6302
   - Preservation Rationale: Reference Golden Model and benchmark measurement harness.

5. TARGET: Remote PYNQ-Z2 Deployment Directory (`/home/xilinx/jupyter_notebooks/pqc_kyber512`)
   - Preservation Rationale: Contains the live board dashboard (`app.py`, bitstreams, HTML assets) running on port 5000. Must not be disrupted or restarted.
====================================================================================================================
```

---

## 6. Baseline Verification Sign-Off

- **Workspace File Count:** 31 primary files cataloged and classified.
- **Hardware Architecture Verified:** AMD Xilinx XC7Z020-CLG400-1 confirmed via `design_1.hwh`.
- **Integrity Compliance:** Read-only inspection completed; zero modifications executed on existing codebase or hardware bitstreams.
