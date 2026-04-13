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

    // setupChartHandler('btn-run-div-finder', 'div-finder-ticker', '/api/chart/div-finder', 'div-finder-image', 'div-finder-loader');
    
    // --- 3.5 SPECIALIZED DIV FINDER HANDLER ---
    document.getElementById('btn-run-div-finder').addEventListener('click', async () => {
        const ticker = document.getElementById('div-finder-ticker').value.trim();
        if (!ticker) return alert("Please enter a ticker!");

        const btn = document.getElementById('btn-run-div-finder');
        const imgEl = document.getElementById('div-finder-image');
        const loader = document.getElementById('div-finder-loader');
        const reportEl = document.getElementById('div-finder-report');
        
        btn.disabled = true;
        imgEl.style.display = 'none';
        reportEl.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            const res = await fetch(`/api/chart/div-finder?ticker=${encodeURIComponent(ticker)}`);
            if (!res.ok) {
                const errInfo = await res.json();
                throw new Error(errInfo.detail || "Server Error");
            }
            const data = await res.json();
            const stats = data.stats;
            
            // 1. Render Image
            imgEl.src = "data:image/png;base64," + data.image;
            imgEl.style.display = 'block';

            // 2. Render Strategy Report
            renderDivFinderReport(reportEl, stats, ticker.toUpperCase());
            reportEl.classList.remove('hidden');

        } catch (err) {
            alert("Failed to generate report: " + err.message);
        } finally {
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    });

    function renderDivFinderReport(container, stats, ticker) {
        const today = new Date();
        const nextExStr = stats.next_ex_date ? stats.next_ex_date : "TBD";
        const rallyTargetStr = stats.target_rally_date ? stats.target_rally_date : "N/A";
        const sweetTargetStr = stats.target_sweet_date ? stats.target_sweet_date : "N/A";
        const divTargetStr = stats.target_div_date ? stats.target_div_date : "N/A";

        // Macro Context Logic
        const correlation = stats.correlation.toFixed(2);
        const benchTrend = stats.bench_5d_trend.toFixed(2);
        
        container.innerHTML = `
            <div class="report-section">
                <h3>*** MACRO CONTEXT: ${stats.industry} (${stats.sector}) ***</h3>
                <div class="report-grid">
                    <div class="report-item">
                        <span class="report-label">Tracking Benchmark</span>
                        <span class="report-value">${stats.benchmark_ticker}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Benchmark 5-Day Trend</span>
                        <span class="report-value ${benchTrend >= 0 ? 'highlight' : 'warning'}">${benchTrend >= 0 ? '+' : ''}${benchTrend}%</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">1-Year Correlation</span>
                        <span class="report-value">${correlation}</span>
                    </div>
                </div>
            </div>

            <div class="report-section">
                <h3>*** STRATEGY INSIGHTS FOR ${ticker} ***</h3>
                <div class="report-grid">
                    <div class="report-item">
                        <span class="report-label">Next Ex-Date</span>
                        <span class="report-value">${nextExStr}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Target Rally (Full)</span>
                        <span class="report-value">${rallyTargetStr}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Target Momentum (Big)</span>
                        <span class="report-value">${sweetTargetStr}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Target Div Entry</span>
                        <span class="report-value">${divTargetStr}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Avg Net Profit</span>
                        <span class="report-value highlight">+$${stats.avg_net_profit.toFixed(2)}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">BE Recovery</span>
                        <span class="report-value">${stats.avg_recovery.toFixed(1)} Days</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Std Dip Limit</span>
                        <span class="report-value">$${stats.target_limit_avg.toFixed(2)}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">VIX-Adj Dip Limit</span>
                        <span class="report-value warning">$${stats.target_limit_min.toFixed(2)}</span>
                    </div>
                </div>
            </div>

            <div class="report-section">
                <h3>--- Recent Dividend Analysis ---</h3>
                <div class="analysis-table-container">
                    <table class="analysis-table">
                        <thead>
                            <tr>
                                <th>Ex-Date</th>
                                <th>Pre-Div Px</th>
                                <th>Ex-Open</th>
                                <th>Ex-High</th>
                                <th>Div Amt</th>
                                <th>Net P/L</th>
                                <th>VIX</th>
                                <th>5d Trnd</th>
                                <th>RallyEnt</th>
                                <th>Div Ent</th>
                                <th>BE Recov</th>
                                <th>Full Recov</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stats.historical_cycles.map(c => `
                                <tr>
                                    <td>${c.ex_date}</td>
                                    <td>$${c.pre_div_price.toFixed(2)}</td>
                                    <td>$${c.ex_day_open.toFixed(2)}</td>
                                    <td>$${c.ex_day_high.toFixed(2)}</td>
                                    <td>$${c.div_amount.toFixed(2)}</td>
                                    <td><span class="report-value ${c.net_profit >= 0 ? 'highlight' : 'warning'}">${c.net_profit >= 0 ? '+' : ''}$${c.net_profit.toFixed(2)}</span></td>
                                    <td>${c.vix_level.toFixed(1)}</td>
                                    <td>${c.five_d_trend >= 0 ? '+' : ''}$${c.five_d_trend.toFixed(1)}</td>
                                    <td>-${c.rally_ent_days}d</td>
                                    <td>-${c.div_ent_days}d</td>
                                    <td>${c.be_recovery}d</td>
                                    <td>${c.full_recovery}d</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // setupChartHandler('btn-run-rebalance-mapper', 'rebalance-mapper-ticker', '/api/chart/rebalance-mapper', 'rebalance-mapper-image', 'rebalance-mapper-loader');
    
    // --- 3.6 SPECIALIZED REBALANCE MAP HANDLER ---
    document.getElementById('btn-run-rebalance-mapper').addEventListener('click', async () => {
        const ticker = document.getElementById('rebalance-mapper-ticker').value.trim();
        if (!ticker) return alert("Please enter a ticker!");

        const btn = document.getElementById('btn-run-rebalance-mapper');
        const imgEl = document.getElementById('rebalance-mapper-image');
        const loader = document.getElementById('rebalance-mapper-loader');
        const reportEl = document.getElementById('rebalance-mapper-report');
        
        btn.disabled = true;
        imgEl.style.display = 'none';
        reportEl.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            const res = await fetch(`/api/chart/rebalance-mapper?ticker=${encodeURIComponent(ticker)}`);
            if (!res.ok) {
                const errInfo = await res.json();
                throw new Error(errInfo.detail || "Server Error");
            }
            const data = await res.json();
            const stats = data.stats;
            
            // 1. Render Image
            imgEl.src = "data:image/png;base64," + data.image;
            imgEl.style.display = 'block';

            // 2. Render Strategy Report
            renderRebalanceReport(reportEl, stats, ticker.toUpperCase());
            reportEl.classList.remove('hidden');

        } catch (err) {
            alert("Failed to generate rebalance report: " + err.message);
        } finally {
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    });

    function renderRebalanceReport(container, stats, ticker) {
        const avgEom = stats.avg_eom_move.toFixed(2);
        
        container.innerHTML = `
            <div class="report-section">
                <h3>*** REBALANCING INSIGHTS FOR ${ticker} ***</h3>
                <div class="report-grid">
                    <div class="report-item">
                        <span class="report-label">Next Rebalance Date</span>
                        <span class="report-value">${stats.next_eom_date} (${stats.days_away} days)</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Historical Profile</span>
                        <span class="report-value">${stats.move_profile}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Avg EOM Impact</span>
                        <span class="report-value ${avgEom >= 0 ? 'highlight' : 'warning'}">${avgEom >= 0 ? '+' : ''}$${avgEom}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Mean Reversion</span>
                        <span class="report-value">${stats.avg_recovery.toFixed(1)} Days</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Baseline Volume</span>
                        <span class="report-value">${Math.round(stats.avg_base_vol).toLocaleString()}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">EOM Day Volume</span>
                        <span class="report-value highlight">${Math.round(stats.avg_eom_vol).toLocaleString()}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Avg Post-EOM Vol</span>
                        <span class="report-value">${Math.round(stats.avg_post_vol).toLocaleString()}</span>
                    </div>
                    <div class="report-item">
                        <span class="report-label">Current VIX</span>
                        <span class="report-value">${stats.current_vix.toFixed(1)}</span>
                    </div>
                </div>
            </div>

            <div class="report-section">
                <h3>--- Last 12 Months Rebalancing Events ---</h3>
                <div class="analysis-table-container">
                    <table class="analysis-table">
                        <thead>
                            <tr>
                                <th>EOM Date</th>
                                <th>Pre-3D Move</th>
                                <th>EOM Move</th>
                                <th>Base Vol</th>
                                <th>EOM Vol</th>
                                <th>Post 3D Vol</th>
                                <th>Recovery</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stats.historical_cycles.map(c => `
                                <tr>
                                    <td>${c.eom_date}</td>
                                    <td>${c.pre_move >= 0 ? '+' : ''}$${c.pre_move.toFixed(2)}</td>
                                    <td><span class="report-value ${c.eom_move >= 0 ? 'highlight' : 'warning'}">${c.eom_move >= 0 ? '+' : ''}$${c.eom_move.toFixed(2)}</span></td>
                                    <td>${c.vol_base ? Math.round(c.vol_base).toLocaleString() : 'N/A'}</td>
                                    <td>${c.vol_eom ? Math.round(c.vol_eom).toLocaleString() : 'N/A'}</td>
                                    <td>${c.vol_post ? Math.round(c.vol_post).toLocaleString() : 'N/A'}</td>
                                    <td>${c.recovery}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }


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
