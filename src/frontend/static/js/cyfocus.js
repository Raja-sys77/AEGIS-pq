/**
 * AEGIS-PQ CY · FOCUS Frontend Operations Logic
 * Connects with backend APIs at 192.168.0.5:8000
 */

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initMobileNav();
    loadSystemInfo();
    loadCryptoOperations();
    loadBenchmarks();
    loadSessions();
    loadSecurityTesting();
    loadEventLogs();
    loadImageGrid();
    
    // Auto-refresh telemetry every 5 seconds
    setInterval(() => {
        loadSessions();
        loadEventLogs();
    }, 5000);
});

function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetSection = item.getAttribute("data-target");
            
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");
            
            document.querySelectorAll(".view-section").forEach(sec => {
                sec.classList.remove("active");
            });
            
            const activeSec = document.getElementById(targetSection);
            if (activeSec) {
                activeSec.classList.add("active");
            }
            
            // Update breadcrumb
            const currentBreadcrumb = document.getElementById("breadcrumb-current");
            if (currentBreadcrumb) {
                currentBreadcrumb.textContent = item.querySelector("span").textContent;
            }
            
            // Close mobile drawer if open
            document.querySelector(".sidebar").classList.remove("open");
        });
    });
}

function initMobileNav() {
    const toggle = document.querySelector(".mobile-nav-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (toggle && sidebar) {
        toggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }
}

async function loadSystemInfo() {
    try {
        const res = await fetch("/api/system/info");
        const data = await res.json();
        
        const socEl = document.getElementById("stat-soc");
        if (socEl) socEl.textContent = data.target_hardware.soc || "Zynq-7000 XC7Z020";
        
        const hostEl = document.getElementById("stat-host");
        if (hostEl) hostEl.textContent = `${data.host_system.ip}:${data.host_system.port}`;
        
        const diskEl = document.getElementById("stat-disk");
        if (diskEl) diskEl.textContent = `${data.storage_budget.root_filesystem_free} Free (Safe)`;
        
        const targetOnline = data.target_hardware.online;
        const pynqPill = document.getElementById("pynq-status-pill");
        if (pynqPill) {
            pynqPill.innerHTML = `<span class="status-dot" style="background-color: ${targetOnline ? 'var(--color-success)' : 'var(--color-warning)'}"></span> PYNQ: ${targetOnline ? 'ONLINE' : 'STANDBY'}`;
        }
    } catch (err) {
        console.error("Failed to load system info:", err);
    }
}

async function loadCryptoOperations() {
    try {
        const res = await fetch("/api/crypto/operations");
        const data = await res.json();
        
        const kemEl = document.getElementById("info-kem");
        if (kemEl) kemEl.textContent = data.standard;
        
        const ringEl = document.getElementById("info-ring");
        if (ringEl) ringEl.textContent = data.ring;
        
        const kdfEl = document.getElementById("info-kdf");
        if (kdfEl) kdfEl.textContent = data.kdf;
        
        const aeadEl = document.getElementById("info-aead");
        if (aeadEl) aeadEl.textContent = data.aead;
    } catch (err) {
        console.error("Failed to load crypto ops:", err);
    }
}

async function loadBenchmarks() {
    try {
        const res = await fetch("/api/telemetry/benchmarks");
        const data = await res.json();
        
        const speedupEl = document.getElementById("kpi-speedup");
        if (speedupEl) speedupEl.textContent = `${data.speedup_ratio}x`;
        
        const hwTimeEl = document.getElementById("kpi-hw-time");
        if (hwTimeEl) hwTimeEl.textContent = `${data.fpga_pl_transform_ms} ms`;
        
        const swTimeEl = document.getElementById("kpi-sw-time");
        if (swTimeEl) swTimeEl.textContent = `${data.pure_python_arm_ms} ms`;
    } catch (err) {
        console.error("Failed to load benchmarks:", err);
    }
}

async function loadSessions() {
    try {
        const res = await fetch("/api/network/sessions");
        const data = await res.json();
        
        const securedEl = document.getElementById("kpi-secured");
        if (securedEl) securedEl.textContent = data.packets_secured;
        
        const droppedEl = document.getElementById("kpi-dropped");
        if (droppedEl) droppedEl.textContent = data.packets_dropped;
        
        const sessionMeta = document.getElementById("session-meta-id");
        if (sessionMeta) sessionMeta.textContent = data.current_session_id;
    } catch (err) {
        console.error("Failed to load sessions:", err);
    }
}

async function loadSecurityTesting() {
    try {
        const res = await fetch("/api/security/testing");
        const data = await res.json();
        
        const rsaTbody = document.getElementById("rsa-benchmark-tbody");
        if (rsaTbody) {
            rsaTbody.innerHTML = data.toy_rsa_benchmarks.map(b => `
                <tr>
                    <td><strong>${b.name}</strong> (${b.bits}-bit)</td>
                    <td><code>${b.modulus_n}</code></td>
                    <td><code>${b.recovered_factor}</code></td>
                    <td>${b.steps} steps</td>
                    <td>${b.latency_ms} ms</td>
                    <td><span class="badge-tag drop">${b.status}</span></td>
                </tr>
            `).join("");
        }
        
        const shorEl = document.getElementById("shor-result-box");
        if (shorEl && data.shor_quantum_simulator) {
            const s = data.shor_quantum_simulator;
            shorEl.innerHTML = `
                <div style="font-family: var(--font-mono); font-size: 12px; color: var(--color-text2);">
                    <p>Base $a$: ${s.base_a} | Modulus $N$: ${s.modulus_n}</p>
                    <p>Simulated Period $r$: <strong>${s.period_r}</strong> (${s.quantum_speedup_class})</p>
                    <p>Recovered Non-Trivial Factors: <span style="color: var(--color-accent); font-weight: bold;">[${s.factors_recovered.join(", ")}]</span></p>
                    <p>Verdict: <span class="badge-tag drop">${s.security_verdict}</span></p>
                </div>
            `;
        }
    } catch (err) {
        console.error("Failed to load security testing:", err);
    }
}

async function loadEventLogs() {
    try {
        const res = await fetch("/api/events/logs");
        const logs = await res.json();
        
        const tbody = document.getElementById("event-logs-tbody");
        if (tbody) {
            tbody.innerHTML = logs.map(l => {
                let badgeClass = "info";
                if (l.status === "PASS" || l.status === "VERIFIED") badgeClass = "pass";
                if (l.status === "DROPPED" || l.severity === "CRITICAL") badgeClass = "drop";
                
                return `
                    <tr>
                        <td style="font-family: var(--font-mono); font-size: 11px;">${l.time}</td>
                        <td><strong>${l.type}</strong></td>
                        <td><code>${l.component}</code></td>
                        <td>${l.details}</td>
                        <td><span class="badge-tag ${badgeClass}">${l.status}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Failed to load event logs:", err);
    }
}

async function loadImageGrid() {
    try {
        const res = await fetch("/api/telemetry/image-grid");
        const data = await res.json();
        
        const grid = document.getElementById("tile-grid-container");
        if (grid) {
            grid.innerHTML = data.tiles.map(t => `
                <div class="tile-block authenticated" title="Tile #${t.tile_id} - Latency: ${t.latency_ms}ms, Entropy: ${t.entropy}">
                    ${t.tile_id.toString().padStart(2, '0')}
                </div>
            `).join("");
        }
    } catch (err) {
        console.error("Failed to load image grid:", err);
    }
}

// Trigger Interactive Cryptographic Transaction
async function triggerCryptoTransaction() {
    const btn = document.getElementById("btn-run-pqc");
    if (btn) btn.disabled = true;
    
    try {
        const res = await fetch("/api/crypto/execute-op", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: "AEGIS-PQ High-Assurance Medical Scan Telemetry"})
        });
        const data = await res.json();
        alert(`PQC Transaction Completed!\nKeyGen: ${data.timings_ms.keygen} ms\nEncaps: ${data.timings_ms.encaps} ms\nDecaps: ${data.timings_ms.decaps} ms\nCiphertext Entropy: ${data.entropy} bits/B`);
        loadSessions();
        loadEventLogs();
    } catch (err) {
        alert("Transaction failed: " + err);
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Trigger Active Adversarial Test
async function triggerAdversarialAttack(attackType) {
    try {
        const res = await fetch("/api/security/execute", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({attack_type: attackType})
        });
        const data = await res.json();
        alert(`Adversarial Injection Result: ${data.outcome}\nDefense: ${data.defense || 'N/A'}`);
        loadSessions();
        loadEventLogs();
    } catch (err) {
        alert("Attack injection failed: " + err);
    }
}
