#Jupyter Notebook Codes for PQC Kyber

#Proper Final KYBER_512 code:

#Final KYBER code: 
from pynq import Overlay, allocate
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
BITSTREAM = "design_1.bit"
Q = 3329
N = 256
FIXED_SECRET = 3
MONT_R = 2285 # 2^16 mod Q
QINV = -3327  # Q^-1 mod 2^16

# Full 128-value Zetas
ZETAS = [
    -1044,  -758,  -359, -1517,  1493,  1422,   287,   202,
     -171,   622,  1577,   182,   962, -1202, -1474,  1468,
      573, -1325,   264,   383,  -829,  1458, -1602,  -130,
     -681,  1017,   732,   608, -1542,   411,  -205, -1571,
     1223,   652,  -552,  1015,  -129,  -282,  -154,  -973,
     1205,   909,  1290,   326,  -724, -1568,  -598,   493,
     -150,   420,  1263,  -679,  -280,   145,  -143,  -108,
    -1459,   341,   228,  -146,  -1430,  -419,  -134,  -742,
    -1092,  -410,  -755,   387,  -683,  -734,  -122,   253,
    -1254,  -628,  -618,   277,  -511,   432,  -208,   488,
     -151,   374,  -653,   273,  -285,  -316,   149,  -443,
      165,   316,  -140,  -255,   109,   207,  -159,  -364,
     -145,   172,   156,   137,  -118,  -234,  -166,  -261,
      -30,   -79,   -35,   -70,   -68,   -52,   -49,   -41,
      905,  -540,  -713,   647,   689,  -330,  -940,    71, 
      311,   860,   759,  -620,  -269,   954,   531,  -284 
]

# ---------------------------------------------------------
# 2. SOFTWARE TWIN (Exact Hardware Replica)
# ---------------------------------------------------------
def to_int16(val):
    val = val & 0xFFFF 
    if val > 32767: val -= 65536
    return val

def montgomery_reduce(a):
    """
    Mimics the exact FPGA logic: a * R^-1 mod Q
    """
    # 1. int16_t u = (int16_t)(a * QINV);
    u = to_int16(a * QINV)
    
    # 2. int32_t t = (int32_t)u * Q;
    t = u * Q
    
    # 3. t = a - t;
    t = a - t
    
    # 4. t >>= 16;
    t = t >> 16
    
    return to_int16(t)

def software_ntt(a):
    a = list(a)
    k = 0
    length = 128
    while length >= 2:
        start = 0
        while start < N:
            zeta = ZETAS[k]
            k += 1
            for j in range(start, start + length):
                # HW: montgomery_reduce((int32_t)zeta * buffer[j + len])
                t = montgomery_reduce(zeta * a[j + length])
                
                val_up = a[j] - t
                if val_up < 0: val_up += Q
                a[j + length] = val_up
                
                val_dn = a[j] + t
                if val_dn >= Q: val_dn -= Q
                a[j] = val_dn
            start = j + 1 + length
        length >>= 1
    return a

def software_pwm(a):
    res = []
    # HW: montgomery_reduce((int32_t)val * (FIXED_SECRET * 2285))
    hw_constant = FIXED_SECRET * 2285 # 3 * R
    for val in a:
        # Simulate HW Multiplication
        new_val = montgomery_reduce(val * hw_constant)
        res.append(new_val)
    return res

def software_intt(a):
    a = list(a)
    k = 127
    length = 2
    while length <= 128:
        start = 0
        while start < N:
            zeta = ZETAS[k]
            for j in range(start, start + length):
                u = a[j]
                v = a[j + length]
                
                a[j] = (u + v)
                if a[j] >= Q: a[j] -= Q
                
                t = (u - v)
                if t < 0: t += Q
                
                # HW: montgomery_reduce((int32_t)t * zeta)
                a[j + length] = montgomery_reduce(t * zeta)
            start = j + 1 + length
            k -= 1
        length <<= 1
    
    # Final Scaling
    for i in range(N):
        # HW: montgomery_reduce((int32_t)buffer[i] * 3316)
        a[i] = montgomery_reduce(a[i] * 3316)
    return a

def generate_golden_model(input_data):
    ntt_res = software_ntt(input_data)
    pwm_res = software_pwm(ntt_res)
    final_res = software_intt(pwm_res)
    return np.array(final_res, dtype=np.int32)

# ---------------------------------------------------------
# 3. EXECUTION
# ---------------------------------------------------------
print("Loading Overlay...")
ol = Overlay(BITSTREAM)
dma = ol.axi_dma_0
kyber_ip = ol.kyber_accelerator_top_0

print("Generating Test Data...")
input_data = np.array([(7 * i + 3) % Q for i in range(N)], dtype=np.uint32)
input_buffer = allocate(shape=(N,), dtype=np.uint32)
output_buffer = allocate(shape=(N,), dtype=np.uint32)
np.copyto(input_buffer, input_data)

print("Running Hardware...")
kyber_ip.write(0x00, 0x01)
dma.sendchannel.transfer(input_buffer)
dma.recvchannel.transfer(output_buffer)
dma.sendchannel.wait()
dma.recvchannel.wait()

print("\nVerifying...")
golden_output = generate_golden_model(input_data)
errors = 0

print(f"{'Idx':<5} | {'HW':<6} | {'SW':<6} | {'Status'}")
print("-" * 30)

for i in range(N):
    # Convert Huge Unsigned to Signed
    hw_val = int(output_buffer[i])
    if hw_val > 32767: hw_val -= 65536
    
    # Normalize to 0..Q for comparison
    hw_norm = hw_val
    while hw_norm < 0: hw_norm += Q
    
    sw_norm = golden_output[i]
    while sw_norm < 0: sw_norm += Q
    
    if hw_norm != sw_norm:
        errors += 1
        if errors <= 10:
             print(f"{i:<5} | {hw_norm:<6} | {sw_norm:<6} | FAIL")
    elif i < 5:
         print(f"{i:<5} | {hw_norm:<6} | {sw_norm:<6} | OK")

if errors == 0:
    print("\nSUCCESS: Hardware matches Software Model exactly!")
else:
    print(f"\nFAILURE: {errors} mismatches found.")




#Proper Benchmark Comparison code

from pynq import Overlay, allocate
import numpy as np
import time

# ---------------------------------------------------------
# 1. SETUP
# ---------------------------------------------------------
BITSTREAM = "design_1.bit"
Q = 3329
N = 256
FIXED_SECRET = 3
ITERATIONS = 1000  # Number of runs for averaging

# Full Zetas
ZETAS = [
    -1044,  -758,  -359, -1517,  1493,  1422,   287,   202,
     -171,   622,  1577,   182,   962, -1202, -1474,  1468,
      573, -1325,   264,   383,  -829,  1458, -1602,  -130,
     -681,  1017,   732,   608, -1542,   411,  -205, -1571,
     1223,   652,  -552,  1015,  -129,  -282,  -154,  -973,
     1205,   909,  1290,   326,  -724, -1568,  -598,   493,
     -150,   420,  1263,  -679,  -280,   145,  -143,  -108,
    -1459,   341,   228,  -146,  -1430,  -419,  -134,  -742,
    -1092,  -410,  -755,   387,  -683,  -734,  -122,   253,
    -1254,  -628,  -618,   277,  -511,   432,  -208,   488,
     -151,   374,  -653,   273,  -285,  -316,   149,  -443,
      165,   316,  -140,  -255,   109,   207,  -159,  -364,
     -145,   172,   156,   137,  -118,  -234,  -166,  -261,
      -30,   -79,   -35,   -70,   -68,   -52,   -49,   -41,
      905,  -540,  -713,   647,   689,  -330,  -940,    71, 
      311,   860,   759,  -620,  -269,   954,   531,  -284 
]

# ---------------------------------------------------------
# 2. SOFTWARE IMPLEMENTATION (The Slow Way)
# ---------------------------------------------------------
def to_int16(val):
    val = val & 0xFFFF 
    if val > 32767: val -= 65536
    return val

def montgomery_reduce(a):
    u = to_int16(a * -3327)
    t = u * Q
    t = a - t
    t = t >> 16
    return to_int16(t)

def run_software_chain(a):
    a = [int(v) for v in a]
    # NTT
    k = 0
    length = 128
    while length >= 2:
        start = 0
        while start < N:
            zeta = ZETAS[k]
            k += 1
            for j in range(start, start + length):
                t = montgomery_reduce(zeta * a[j + length])
                val_up = a[j] - t
                if val_up < 0: val_up += Q
                a[j + length] = val_up
                val_dn = a[j] + t
                if val_dn >= Q: val_dn -= Q
                a[j] = val_dn
            start = j + 1 + length
        length >>= 1
    
    # PWM
    hw_constant = FIXED_SECRET * 2285
    for i in range(N):
        a[i] = montgomery_reduce(a[i] * hw_constant)

    # iNTT
    k = 127
    length = 2
    while length <= 128:
        start = 0
        while start < N:
            zeta = ZETAS[k]
            for j in range(start, start + length):
                u = a[j]
                v = a[j + length]
                a[j] = (u + v)
                if a[j] >= Q: a[j] -= Q
                t = (u - v)
                if t < 0: t += Q
                a[j + length] = montgomery_reduce(t * zeta)
            start = j + 1 + length
            k -= 1
        length <<= 1
    
    # Scale
    for i in range(N):
        a[i] = montgomery_reduce(a[i] * 3316)
    
    return a

# ---------------------------------------------------------
# 3. BENCHMARKING
# ---------------------------------------------------------
print(f"Loading Overlay (Design: {BITSTREAM})...")
ol = Overlay(BITSTREAM)
dma = ol.axi_dma_0
kyber_ip = ol.kyber_accelerator_top_0

print(f"Generating Data for {ITERATIONS} runs...")
input_data = np.array([(7 * i + 3) % Q for i in range(N)], dtype=np.uint32)
input_buffer = allocate(shape=(N,), dtype=np.uint32)
output_buffer = allocate(shape=(N,), dtype=np.uint32)
np.copyto(input_buffer, input_data)

# --- SOFTWARE RUN ---
print(">>> Starting SOFTWARE Benchmark (ARM CPU)...")
start_sw = time.time()
for i in range(ITERATIONS):
    _ = run_software_chain(input_data)
end_sw = time.time()
time_sw = end_sw - start_sw
print(f"    Done. Time: {time_sw:.4f} seconds")

# --- HARDWARE RUN ---
print(">>> Starting HARDWARE Benchmark (FPGA Accelerator)...")
kyber_ip.write(0x00, 0x01) # Start IP once (if using auto-restart) or inside loop
start_hw = time.time()
for i in range(ITERATIONS):
    kyber_ip.write(0x00, 0x01) # Trigger IP
    dma.sendchannel.transfer(input_buffer)
    dma.recvchannel.transfer(output_buffer)
    dma.sendchannel.wait()
    dma.recvchannel.wait()
end_hw = time.time()
time_hw = end_hw - start_hw
print(f"    Done. Time: {time_hw:.4f} seconds")

# ---------------------------------------------------------
# 4. RESULTS
# ---------------------------------------------------------
print("\n" + "="*40)
print("       BENCHMARK RESULTS")
print("="*40)
print(f"Iterations:      {ITERATIONS}")
print(f"Software (CPU):  {time_sw:.4f} s  ({(time_sw/ITERATIONS)*1000:.2f} ms/run)")
print(f"Hardware (FPGA): {time_hw:.4f} s  ({(time_hw/ITERATIONS)*1000:.2f} ms/run)")
print("-" * 40)
speedup = time_sw / time_hw
print(f"SPEEDUP FACTOR:  {speedup:.2f}x FASTER")
print("="*40)

#Proper GUI Website code

import subprocess, sys

server = subprocess.Popen(
    [sys.executable, "app.py"],
    cwd="/home/xilinx/jupyter_notebooks/pqc_kyber512",  # adjust to your actual folder path
    stdout=open("server.log", "w"),
    stderr=subprocess.STDOUT,
)
print("Server starting, PID:", server.pid)

#http://10.11.58.IP:5000/ - Use this webiste to see the real time demo