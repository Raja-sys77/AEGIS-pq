# AEGIS-PQ Minimal Board Deployment Manifest
# Generated for PYNQ-Z2 (192.168.0.2)
# Storage Budget Constraint: Root filesystem free space is 5.4 MB.
# ZERO new package installations. RAM buffers only (/dev/shm).

Target IP: 192.168.0.2
Target User: xilinx
Target Directory: /home/xilinx/jupyter_notebooks/pqc_kyber512/

Files to Transfer:
-------------------------------------------------------------------------------------------------------------
File Name               | Source Location                 | Destination Location                 | Size (Bytes)
-------------------------------------------------------------------------------------------------------------
aegis_pynq_daemon.py    | src/pynq/aegis_pynq_daemon.py   | /home/xilinx/jupyter_notebooks/pqc_kyber512/ | ~3,500
-------------------------------------------------------------------------------------------------------------
Total Package Size: < 4.0 KB (0.004 MB)
Percentage of Available Flash: < 0.08%

Pre-existing Preserved Board Files:
- design_1.bit (SHA-256: bb712fc45ab6e328258a4304c6e2718b5c1711bdd9436ad9a24dc1307fbfa98a)
- design_1.hwh (SHA-256: 7a98716f797cd6ee5eb059bbc4c71a811c2228416bf412ed96407a37b9d0e207)
- app.py (Resident Flask Dashboard on Port 5000)
- kyber_hal.py

Verification Method:
1. Transfer aegis_pynq_daemon.py via SCP.
2. Verify SHA-256 checksum on board matches local file.
3. Check `df -h /` before and after transfer.
4. Execute non-blocking smoke test on port 5557 without restarting any board services.
5. Verify resident dashboard on port 5000 is still responding.
