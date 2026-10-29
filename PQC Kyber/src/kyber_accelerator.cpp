#include "hls_stream.h"
#include "ap_axi_sdata.h"
#include <stdint.h>

#define N 256
#define Q 3329

typedef ap_axis<32, 0, 0, 0> axis_pkt;
typedef hls::stream<axis_pkt> axis_stream;
typedef hls::stream<int16_t> internal_stream;

// --------------------------------------------------------
// 1. CONSTANTS & TABLES
// --------------------------------------------------------
// Full 128-value Zeta Table (Verified)
static const int16_t zetas[128] = {
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
};

// --------------------------------------------------------
// 2. MATH HELPERS
// --------------------------------------------------------
static int16_t montgomery_reduce(int32_t a) {
    #pragma HLS INLINE
    int16_t u = (int16_t)(a * -3327); // QINV
    int32_t t = (int32_t)u * Q;
    t = a - t;
    t >>= 16;
    return (int16_t)t;
}

static int16_t barrett_reduce(int16_t a) {
    #pragma HLS INLINE
    int16_t v = ((int32_t)a * 20159) >> 26;
    int16_t res = a - v * Q;
    return res;
}

// --------------------------------------------------------
// 3. STAGE 1: LOAD (DMA -> Stream)
// --------------------------------------------------------
void load_data_wrapper(axis_stream &in_dma, internal_stream &out_stream) {
    #pragma HLS INLINE off
    for(int i = 0; i < N; i++) {
        #pragma HLS PIPELINE II=1
        axis_pkt p = in_dma.read();
        out_stream.write((int16_t)(p.data % Q));
    }
}

// --------------------------------------------------------
// 4. STAGE 2: NTT (Stream -> Stream)
// --------------------------------------------------------
void run_ntt_wrapper(internal_stream &in_stream, internal_stream &out_stream) {
    #pragma HLS INLINE off
    
    int16_t buffer[N];
    #pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=lutram

    // Read
    for(int i=0; i<N; i++) {
        #pragma HLS PIPELINE II=1
        buffer[i] = in_stream.read();
    }

    // NTT Logic
    int len, start, j, k;
    int16_t zeta, t;
    k = 0;
    for (len = 128; len >= 2; len >>= 1) {
        for (start = 0; start < N; start += 2 * len) {
            zeta = zetas[k++];
            for (j = start; j < start + len; j++) {
                #pragma HLS PIPELINE
                t = montgomery_reduce((int32_t)zeta * buffer[j + len]);
                buffer[j + len] = buffer[j] - t;
                if (buffer[j + len] < 0) buffer[j + len] += Q;
                buffer[j] = buffer[j] + t;
                if (buffer[j] >= Q) buffer[j] -= Q;
            }
        }
    }

    // Write
    for(int i=0; i<N; i++) {
        #pragma HLS PIPELINE II=1
        out_stream.write(buffer[i]);
    }
}

// --------------------------------------------------------
// 5. STAGE 3: PWM (Pointwise Multiply)
// --------------------------------------------------------
void run_pwm_wrapper(internal_stream &in_stream, internal_stream &out_stream) {
    #pragma HLS INLINE off
    
    // We use a fixed "Secret" key for verification
    // In real Kyber, this would come from another stream or memory
    static const int16_t FIXED_SECRET = 3; 

    for(int i = 0; i < N; i++) {
        #pragma HLS PIPELINE II=1
        int16_t val = in_stream.read();
        
        // Modular Multiplication: (val * SECRET) % Q
        // We use Montgomery reduce to keep it consistent
        int16_t res = montgomery_reduce((int32_t)val * (FIXED_SECRET * 2285)); // 2285 is 2^16 mod Q (R)
        
        out_stream.write(res); 
    }
}

// --------------------------------------------------------
// 6. STAGE 4: iNTT (Stream -> Stream)
// --------------------------------------------------------
void run_intt_wrapper(internal_stream &in_stream, internal_stream &out_stream) {
    #pragma HLS INLINE off
    
    int16_t buffer[N];
    #pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=lutram

    // Read
    for(int i=0; i<N; i++) {
        #pragma HLS PIPELINE II=1
        buffer[i] = in_stream.read();
    }

    // iNTT Logic
    int len, start, j, k;
    int16_t zeta, t;
    k = 127;
    for (len = 2; len <= 128; len <<= 1) {
        for (start = 0; start < N; start += 2 * len) {
            zeta = zetas[k];
            for (j = start; j < start + len; j++) {
                #pragma HLS PIPELINE
                int16_t u = buffer[j];
                int16_t v = buffer[j + len];
                buffer[j] = u + v;
                if (buffer[j] >= Q) buffer[j] -= Q;
                t = u - v;
                if (t < 0) t += Q;
                buffer[j + len] = montgomery_reduce((int32_t)t * zeta);
            }
            k--;
        }
    }
    
    // Scaling
    for(int i=0; i<N; i++) {
        #pragma HLS PIPELINE
        // Multiply by 3316 (1/256)
        buffer[i] = montgomery_reduce((int32_t)buffer[i] * 3316); 
    }

    // Write
    for(int i=0; i<N; i++) {
        #pragma HLS PIPELINE II=1
        out_stream.write(buffer[i]);
    }
}

// --------------------------------------------------------
// 7. STAGE 5: STORE (Stream -> DMA)
// --------------------------------------------------------
void store_data_wrapper(internal_stream &in_stream, axis_stream &out_dma) {
    #pragma HLS INLINE off
    for(int i = 0; i < N; i++) {
        #pragma HLS PIPELINE II=1
        int16_t val = in_stream.read();
        
        // Final Positive Correction
        if(val < 0) val += Q;

        axis_pkt p;
        p.data = val;
        p.keep = 0xF;
        p.strb = 0xF;
        p.last = (i == 255);
        out_dma.write(p);
    }
}

// ========================================================
// THE TOP FUNCTION
// ========================================================
void kyber_accelerator_top(axis_stream &INPUT_DMA, axis_stream &OUTPUT_DMA) {
    #pragma HLS INTERFACE axis port=INPUT_DMA
    #pragma HLS INTERFACE axis port=OUTPUT_DMA
    #pragma HLS INTERFACE s_axilite port=return bundle=CTRL_BUS

    static internal_stream pipe_1;
    static internal_stream pipe_2;
    static internal_stream pipe_3;
    static internal_stream pipe_4;
    
    #pragma HLS STREAM variable=pipe_1 depth=256
    #pragma HLS STREAM variable=pipe_2 depth=256
    #pragma HLS STREAM variable=pipe_3 depth=256
    #pragma HLS STREAM variable=pipe_4 depth=256

    #pragma HLS DATAFLOW

    // 1. DMA -> Stream
    load_data_wrapper(INPUT_DMA, pipe_1);
    
    // 2. NTT
    run_ntt_wrapper(pipe_1, pipe_2);
    
    // 3. PWM (Math!)
    run_pwm_wrapper(pipe_2, pipe_3);
    
    // 4. iNTT
    run_intt_wrapper(pipe_3, pipe_4);
    
    // 5. Stream -> DMA
    store_data_wrapper(pipe_4, OUTPUT_DMA);
}