/**
 * AEGIS-PQ CY · FOCUS Operations UI Logic
 * Handles real Mode A vs Mode B network socket transfers,
 * hardware status querying, and adversarial test executions.
 */

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initMobileNav();
    loadSystemInfo();
    loadFpgaStatus();
    loadTransferResults();
    loadSecurityTesting();
    loadEventLogs();
    
    // Auto-refresh event logs & results every 5 seconds
    setInterval(() => {
        loadTransferResults();
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
            
            const currentBreadcrumb = document.getElementById("breadcrumb-current");
            if (currentBreadcrumb) {
                currentBreadcrumb.textContent = item.querySelector("span:last-child").textContent;
            }
            
            document.querySelector(".sidebar").classList.remove("open");
        });
    });
}

function switchToTransferLab() {
    const labItem = document.querySelector(".nav-item[data-target='view-transfer-lab']");
    if (labItem) labItem.click();
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
        
        const pynqOnline = data.target_hardware && data.target_hardware.online;
        const pynqPill = document.getElementById("pynq-status-pill");
        if (pynqPill) {
            pynqPill.innerHTML = `<span class="status-dot" style="background-color: ${pynqOnline ? 'var(--color-success)' : 'var(--color-warning)'}"></span> PYNQ: ${pynqOnline ? 'ONLINE' : 'STANDBY'}`;
        }
    } catch (err) {
        console.error("Failed to load system info:", err);
    }
}

async function loadFpgaStatus() {
    try {
        const res = await fetch("/api/hardware/fpga");
        const data = await res.json();
        const pill = document.getElementById("fpga-provenance-pill");
        if (pill) {
            pill.textContent = data.provenance;
            pill.className = `kpi-pill ${data.online ? 'positive' : 'warning'}`;
        }
    } catch (err) {
        console.error("Failed to load FPGA status:", err);
    }
}

async function handleTransferSubmit(event) {
    event.preventDefault();
    const btn = document.getElementById("btn-submit-transfer");
    const spinner = document.getElementById("transfer-spinner");
    const card = document.getElementById("transfer-live-card");
    const content = document.getElementById("transfer-receipt-content");
    
    const mode = document.querySelector("input[name='transfer_mode']:checked").value;
    const payload = document.getElementById("transfer-payload").value;
    
    btn.disabled = true;
    spinner.style.display = "inline";
    card.style.display = "none";
    
    try {
        const res = await fetch("/api/transfers/execute", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                mode: mode,
                message: payload
            })
        });
        const data = await res.json();
        
        card.style.display = "block";
        if (data.success) {
            let timingDetail = "";
            if (data.timings_breakdown_ms) {
                timingDetail = `
                    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--color-border);">
                        <strong>PQC Timing Breakdown:</strong><br>
                        - ML-KEM-512 KeyGen: ${data.timings_breakdown_ms.mlkem_keygen} ms<br>
                        - ML-KEM-512 Encapsulation: ${data.timings_breakdown_ms.mlkem_encaps} ms<br>
                        - ML-KEM-512 Decapsulation: ${data.timings_breakdown_ms.mlkem_decaps} ms<br>
                        - AES-256-GCM Encryption: ${data.timings_breakdown_ms.aes_gcm_encrypt} ms<br>
                        - Total Socket Wire Roundtrip: ${data.timings_breakdown_ms.total_network_e2e} ms
                    </div>
                `;
            }
            
            content.innerHTML = `
                <div style="color: var(--color-success); font-weight: bold; margin-bottom: 6px;">
                    &#10003; Transfer Verified Successfully [${data.provenance}]
                </div>
                <div>Transfer ID: <strong>${data.transfer_id}</strong> | Mode: <strong>${data.mode}</strong></div>
                <div>Payload Transferred: <strong>${data.bytes_transferred} bytes</strong> | Latency: <strong>${data.latency_ms} ms</strong></div>
                <div>SHA-256 Digest: <code>${data.sha256}</code></div>
                <div>Security Assurance: <em>${data.security_level}</em></div>
                <div>Receiver Status: <strong>${data.receiver_ack ? data.receiver_ack.status : 'ACK'}</strong></div>
                ${timingDetail}
            `;
        } else {
            content.innerHTML = `
                <div style="color: var(--color-error); font-weight: bold;">
                    &#9888; Transfer Failed: ${data.error || 'Unknown network error'}
                </div>
            `;
        }
        
        loadTransferResults();
        loadEventLogs();
    } catch (err) {
        card.style.display = "block";
        content.innerHTML = `<div style="color: var(--color-error);">Network Exception: ${err}</div>`;
    } finally {
        btn.disabled = false;
        spinner.style.display = "none";
    }
}

async function loadTransferResults() {
    try {
        const res = await fetch("/api/transfers/results");
        const data = await res.json();
        const tbody = document.getElementById("transfer-results-tbody");
        if (tbody) {
            if (data.results.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-muted);">No transfers recorded yet. Transmit a payload in the Transfer Lab.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = data.results.map(r => {
                const isSecure = r.mode === "AEGIS_PQ_SECURE";
                const badge = r.authenticated ? 
                    `<span class="badge-tag pass">AUTHENTICATED</span>` : 
                    `<span class="badge-tag drop">UNPROTECTED</span>`;
                
                return `
                    <tr>
                        <td><strong>${r.transfer_id}</strong></td>
                        <td><code>${r.mode}</code></td>
                        <td>${r.bytes_transferred || r.original_bytes || 0} B</td>
                        <td><code style="font-size: 10px;">${(r.sha256 || '').substring(0, 16)}...</code></td>
                        <td><strong>${r.latency_ms} ms</strong></td>
                        <td>${badge}</td>
                        <td style="font-size: 11px;">${r.security_level || 'N/A'}</td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Failed to load transfer results:", err);
    }
}

async function loadSecurityTesting() {
    try {
        const res = await fetch("/api/security/testing");
        const data = await res.json();
        
        const rsaTbody = document.getElementById("rsa-benchmark-tbody");
        if (rsaTbody && data.toy_rsa_benchmarks) {
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
                    <p style="font-size: 10px; color: var(--color-muted); margin-top: 6px;">* Simulated demonstration only</p>
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
                if (l.status === "DROPPED" || l.status === "FAILED") badgeClass = "drop";
                
                return `
                    <tr>
                        <td style="font-family: var(--font-mono); font-size: 11px;">${l.time}</td>
                        <td><strong>${l.type}</strong></td>
                        <td><code>${l.component}</code></td>
                        <td>${l.details}</td>
                        <td><span style="font-size: 10px; color: var(--color-muted);">${l.provenance || 'LIVE'}</span></td>
                        <td><span class="badge-tag ${badgeClass}">${l.status}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (err) {
        console.error("Failed to load event logs:", err);
    }
}

async function triggerAdversarialAttack(attackType) {
    try {
        const res = await fetch("/api/security/execute", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({attack_type: attackType})
        });
        const data = await res.json();
        alert(`Adversarial Injection Result: ${data.outcome}\nDefense: ${data.defense || 'N/A'}\nProvenance: ${data.provenance || 'LIVE'}`);
        loadEventLogs();
    } catch (err) {
        alert("Attack injection failed: " + err);
    }
}
