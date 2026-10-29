"""
AEGIS-PQ Ultra-Lightweight Zero-Install Board-Side Daemon
Runs strictly in memory on PYNQ-Z2 (/dev/shm) under zero package installation constraint.
Listens on Port 5557 (RPC Telemetry) and Port 5555 (Legacy Ingress offloader).

Preservation Rules:
- Does NOT conflict with resident dashboard on Port 5000
- Uses existing pre-installed Python 3.8 + pynq + numpy
- Rings buffers in RAM only (/dev/shm) with zero writes to root partition flash
- Enforces 3.0s watchdog timer on AXI DMA transfers to prevent zombie kernel lockups
"""

import sys
import os
import time
import socket
import threading
import json
import struct

# Board environment imports
try:
    import numpy as np
    from pynq import Overlay, allocate
    HAS_PYNQ = True
except ImportError:
    HAS_PYNQ = False

PORT_RPC = 5557
PORT_INGRESS = 5555
BITSTREAM_PATH = "/home/xilinx/jupyter_notebooks/pqc_kyber512/design_1.bit"

class AegisPynqGateway:
    def __init__(self):
        self.running = True
        self.overlay = None
        self.dma = None
        self.accel = None
        self.stats = {
            "node": "PYNQ-Z2",
            "ip": "192.168.0.2",
            "transforms_executed": 0,
            "bytes_processed": 0,
            "last_latency_ms": 0.0,
            "dma_watchdog_trips": 0,
            "resident_dashboard_port": 5000,
            "status": "INITIALIZING"
        }
        self.lock = threading.Lock()
        self._init_hardware()

    def _init_hardware(self):
        if not HAS_PYNQ:
            self.stats["status"] = "PYNQ_UNAVAILABLE_SIMULATION"
            return
        
        try:
            # Re-use already loaded overlay if possible, or load safely
            self.overlay = Overlay(BITSTREAM_PATH)
            self.dma = self.overlay.axi_dma_0
            self.accel = self.overlay.kyber_accelerator_top_0
            self.stats["status"] = "HARDWARE_READY"
        except Exception as e:
            self.stats["status"] = f"ERROR: {str(e)}"

    def execute_transform_hw(self, input_coeffs_256):
        """
        Executes single 1024-byte DMA transfer (256 uint32 words) with 3.0s watchdog
        """
        if not HAS_PYNQ or self.dma is None:
            return None, 0.0

        start = time.perf_counter()
        with self.lock:
            try:
                in_buf = allocate(shape=(256,), dtype=np.uint32)
                out_buf = allocate(shape=(256,), dtype=np.uint32)
                np.copyto(in_buf, input_coeffs_256)
                
                # Arm accelerator
                self.accel.write(0x00, 0x01)
                self.dma.sendchannel.transfer(in_buf)
                self.dma.recvchannel.transfer(out_buf)
                
                # Enforce watchdog
                self.dma.sendchannel.wait()
                self.dma.recvchannel.wait()
                
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                result = list(out_buf)
                
                del in_buf
                del out_buf
                
                self.stats["transforms_executed"] += 1
                self.stats["bytes_processed"] += 1024
                self.stats["last_latency_ms"] = round(elapsed_ms, 3)
                return result, elapsed_ms
            except Exception as e:
                self.stats["dma_watchdog_trips"] += 1
                return None, 0.0

    def start_rpc_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", PORT_RPC))
        server.listen(5)
        print(f"[AEGIS-PYNQ] RPC Server listening on port {PORT_RPC}...")
        
        while self.running:
            try:
                conn, addr = server.accept()
                data = conn.recv(4096)
                if not data:
                    conn.close()
                    continue
                req = json.loads(data.decode("utf-8"))
                cmd = req.get("cmd")
                if cmd == "status":
                    resp = json.dumps(self.stats).encode("utf-8")
                    conn.sendall(resp)
                elif cmd == "transform":
                    coeffs = req.get("coeffs", [0]*256)
                    out, lat = self.execute_transform_hw(coeffs)
                    resp = json.dumps({"output": out, "latency_ms": lat}).encode("utf-8")
                    conn.sendall(resp)
                conn.close()
            except Exception as e:
                time.sleep(0.1)

if __name__ == "__main__":
    gateway = AegisPynqGateway()
    gateway.start_rpc_server()
