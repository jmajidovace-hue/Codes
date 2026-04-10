document.addEventListener('DOMContentLoaded', () => {

    // --- TAB SWITCHING ---
    const navLinks = document.querySelectorAll('.sidebar .nav-links li');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove active class from all
            navLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            // Add active to clicked
            link.classList.add('active');
            const targetId = link.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // --- 1. DIVIDEND INSIGHT SCANNER ---
    const btnDivScan = document.getElementById('btn-run-div-scan');
    const terminalDivScan = document.getElementById('div-insight-terminal');
    let divScanSource = null;

    btnDivScan.addEventListener('click', () => {
        if (divScanSource) divScanSource.close();
        terminalDivScan.textContent = "Initializing connection...\n";
        btnDivScan.disabled = true;
        btnDivScan.textContent = "Scanning...";

        divScanSource = new EventSource('/api/scan/div-insight');

        divScanSource.onmessage = function(event) {
            if (event.data === "EOF") {
                divScanSource.close();
                btnDivScan.disabled = false;
                btnDivScan.textContent = "Start Market Scan";
            } else {
                terminalDivScan.textContent += event.data + "\n";
                // Auto-scroll to bottom
                terminalDivScan.parentElement.scrollTop = terminalDivScan.parentElement.scrollHeight;
            }
        };

        divScanSource.onerror = function(err) {
            console.error("EventSource failed:", err);
            divScanSource.close();
            btnDivScan.disabled = false;
            btnDivScan.textContent = "Start Market Scan (Error)";
        };
    });


    // --- 2. REBALANCE SCANNER ---
    const btnRebScan = document.getElementById('btn-run-rebalance-scan');
    const terminalRebScan = document.getElementById('rebalance-terminal');
    let rebScanSource = null;

    btnRebScan.addEventListener('click', () => {
        if (rebScanSource) rebScanSource.close();
        terminalRebScan.textContent = "Initializing connection...\n";
        btnRebScan.disabled = true;
        btnRebScan.textContent = "Scanning Options...";

        rebScanSource = new EventSource('/api/scan/rebalancing');

        rebScanSource.onmessage = function(event) {
            if (event.data === "EOF") {
                rebScanSource.close();
                btnRebScan.disabled = false;
                btnRebScan.textContent = "Run Master EOM Scan";
            } else {
                terminalRebScan.textContent += event.data + "\n";
                terminalRebScan.parentElement.scrollTop = terminalRebScan.parentElement.scrollHeight;
            }
        };

        rebScanSource.onerror = function(err) {
            console.error("EventSource failed:", err);
            rebScanSource.close();
            btnRebScan.disabled = false;
            btnRebScan.textContent = "Run Master EOM Scan (Error)";
        };
    });


    // --- 3. CHARTING API CALLS ---
    function setupChartHandler(btnId, inputId, endpoint, imgId, loaderId) {
        document.getElementById(btnId).addEventListener('click', async () => {
            const ticker = document.getElementById(inputId).value.trim();
            if (!ticker) return alert("Please enter a ticker!");

            const imgEl = document.getElementById(imgId);
            const loader = document.getElementById(loaderId);
            
            imgEl.style.display = 'none';
            loader.classList.remove('hidden');

            try {
                const res = await fetch(`${endpoint}?ticker=${encodeURIComponent(ticker)}`);
                if (!res.ok) {
                    const errInfo = await res.json();
                    throw new Error(errInfo.detail || "Server Error");
                }
                const data = await res.json();
                
                imgEl.src = "data:image/png;base64," + data.image;
                imgEl.style.display = 'block';
            } catch (err) {
                alert("Failed to generate chart: " + err.message);
            } finally {
                loader.classList.add('hidden');
            }
        });
    }

    setupChartHandler('btn-run-div-finder', 'div-finder-ticker', '/api/chart/div-finder', 'div-finder-image', 'div-finder-loader');
    setupChartHandler('btn-run-rebalance-mapper', 'rebalance-mapper-ticker', '/api/chart/rebalance-mapper', 'rebalance-mapper-image', 'rebalance-mapper-loader');


    // --- 4. CALCULATORS ---
    
    // FORMATTING HELPER
    const formatMoney = (val) => new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(val);

    // SMI Form
    document.getElementById('smi-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fd = new FormData();
        fd.append('file', document.getElementById('smi-file').files[0]);
        fd.append('ticker', document.getElementById('smi-ticker').value);
        fd.append('shares', document.getElementById('smi-shares').value);
        fd.append('price', document.getElementById('smi-price').value);
        fd.append('days', document.getElementById('smi-days').value);
        fd.append('target_profit', document.getElementById('smi-profit').value);

        const resBox = document.getElementById('smi-result');
        resBox.classList.add('hidden');
        resBox.className = 'result-box'; // Reset borders

        try {
            const response = await fetch('/api/calc/smi', { method: 'POST', body: fd });
            if (!response.ok) {
                const errorInfo = await response.json();
                throw new Error(errorInfo.detail || "Error calculating SMI");
            }
            const { result } = await response.json();
            
            resBox.innerHTML = `
                <div style="font-weight:bold; margin-bottom: 0.5rem; color: #fff;">ANALYSIS RESULTS</div>
                <div>Yearly Rate: ${result.yearly_rate.toFixed(2)}%</div>
                <div>Position Value: ${formatMoney(result.position_value)}</div>
                <div>Total SMI Cost: ${formatMoney(result.total_cost)}</div>
                <hr style="margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);">
                <div>Gross Profit expected: ${formatMoney(result.potential_gain)}</div>
                <div style="font-size: 1.1em; font-weight: bold; margin-top: 0.5rem;">
                    Net Profit: ${formatMoney(result.net_profit)}
                </div>
            `;
            
            resBox.classList.add(result.is_good ? 'good' : 'bad');
            resBox.classList.remove('hidden');
        } catch(err) {
            alert(err.message);
        }
    });

    // LONG Form
    document.getElementById('long-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fd = new FormData();
        fd.append('ticker', document.getElementById('long-ticker').value);
        fd.append('shares', document.getElementById('long-shares').value);
        fd.append('price', document.getElementById('long-price').value);
        fd.append('days', document.getElementById('long-days').value);
        fd.append('target_profit', document.getElementById('long-profit').value);

        const resBox = document.getElementById('long-result');
        resBox.classList.add('hidden');
        resBox.className = 'result-box'; // Reset borders

        try {
            const response = await fetch('/api/calc/long', { method: 'POST', body: fd });
            if (!response.ok) {
                const errorInfo = await response.json();
                throw new Error(errorInfo.detail || "Error calculating Long Commission");
            }
            const { result } = await response.json();
            
            resBox.innerHTML = `
                <div style="font-weight:bold; margin-bottom: 0.5rem; color: #fff;">ANALYSIS RESULTS</div>
                <div>Yearly Rate: ${result.yearly_rate.toFixed(2)}%</div>
                <div>Position Value: ${formatMoney(result.position_value)}</div>
                <div>Total Cost: ${formatMoney(result.total_cost)}</div>
                <hr style="margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);">
                <div>Gross Profit expected: ${formatMoney(result.potential_gain)}</div>
                <div style="font-size: 1.1em; font-weight: bold; margin-top: 0.5rem;">
                    Net Profit: ${formatMoney(result.net_profit)}
                </div>
            `;
            
            resBox.classList.add(result.is_good ? 'good' : 'bad');
            resBox.classList.remove('hidden');
        } catch(err) {
            alert(err.message);
        }
    });

});
