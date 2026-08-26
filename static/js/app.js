/**
 * Indian Equities Swing Trading Research & Scanner Platform - Frontend App
 * Handles API communications, chart rendering, candidate rankings, and testing studio.
 */

let activeChart = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadMarketRegime();
    initScannerControls();
    initDeepDive();
    initManualTester();
});

/* ==========================================================================
   TAB NAVIGATION
   ========================================================================== */
function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const viewPanels = document.querySelectorAll(".view-panel");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            viewPanels.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add("active");
            }
        });
    });
}

function switchToTab(tabId) {
    const tabBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (tabBtn) tabBtn.click();
}

/* ==========================================================================
   MARKET REGIME & SECTOR BREADTH
   ========================================================================== */
async function loadMarketRegime() {
    try {
        const resp = await fetch("/api/market-regime");
        const json = await resp.json();
        if (json.status !== "success") return;
        const data = json.data;

        // Top navbar regime pill
        const navPill = document.getElementById("nav-regime-text");
        if (navPill) navPill.textContent = `Regime: ${data.regime_status} • VIX: ${data.india_vix?.value || '--'}`;

        // Banner strip
        const nifty = data.nifty_50 || {};
        document.getElementById("strip-nifty-price").textContent = `₹${nifty.price?.toLocaleString('en-IN') || '--'}`;
        const niftyChg = document.getElementById("strip-nifty-chg");
        niftyChg.textContent = `${nifty.change_1d >= 0 ? '+' : ''}${nifty.change_1d || 0}%`;
        niftyChg.className = `regime-chg ${nifty.change_1d >= 0 ? 'text-green' : 'text-red'}`;
        document.getElementById("strip-nifty-trend").textContent = nifty.trend || '--';

        const bank = data.bank_nifty || {};
        document.getElementById("strip-bank-price").textContent = `₹${bank.price?.toLocaleString('en-IN') || '--'}`;
        const bankChg = document.getElementById("strip-bank-chg");
        bankChg.textContent = `${bank.change_1d >= 0 ? '+' : ''}${bank.change_1d || 0}%`;
        bankChg.className = `regime-chg ${bank.change_1d >= 0 ? 'text-green' : 'text-red'}`;
        document.getElementById("strip-bank-trend").textContent = bank.trend || '--';

        const vix = data.india_vix || {};
        document.getElementById("strip-vix-val").textContent = vix.value || '--';
        const vixChg = document.getElementById("strip-vix-chg");
        vixChg.textContent = `${vix.change_pct >= 0 ? '+' : ''}${vix.change_pct || 0}%`;
        vixChg.className = `regime-chg ${vix.change_pct <= 0 ? 'text-green' : 'text-red'}`;
        document.getElementById("strip-vix-status").textContent = vix.status || '--';

        const breadth = data.sector_breadth || {};
        document.getElementById("strip-breadth-pct").textContent = `${breadth.breadth_pct || 0}%`;
        document.getElementById("strip-breadth-sub").textContent = `${breadth.bullish_sectors_count || 0}/${breadth.total_sectors || 0} Sectors > 20 EMA`;

        document.getElementById("strip-guidance-text").textContent = data.guidance || '--';

        // Macro Tab items
        const mainBadge = document.getElementById("regime-main-badge");
        if (mainBadge) {
            mainBadge.textContent = data.regime_badge;
            if (data.regime_status === "BEARISH") {
                mainBadge.className = "regime-huge-badge badge-danger";
            } else if (data.regime_status === "NEUTRAL") {
                mainBadge.className = "regime-huge-badge badge-warning";
            } else {
                mainBadge.className = "regime-huge-badge badge-success";
            }
        }
        const mainGuidance = document.getElementById("regime-main-guidance");
        if (mainGuidance) mainGuidance.textContent = data.guidance;

        const macroNifty20 = document.getElementById("macro-nifty-20ema");
        if (macroNifty20) macroNifty20.textContent = `₹${nifty.ema_20?.toLocaleString('en-IN') || '--'}`;
        const macroNifty50 = document.getElementById("macro-nifty-50ema");
        if (macroNifty50) macroNifty50.textContent = `₹${nifty.ema_50?.toLocaleString('en-IN') || '--'}`;
        const macroVix = document.getElementById("macro-vix-val");
        if (macroVix) macroVix.textContent = vix.value || '--';
        const macroBreadth = document.getElementById("macro-breadth-pct");
        if (macroBreadth) macroBreadth.textContent = `${breadth.breadth_pct || 0}%`;

        // Render Sectors Table
        const secTbody = document.getElementById("sectors-tbody");
        if (secTbody && data.sectors) {
            secTbody.innerHTML = data.sectors.map(sec => `
                <tr>
                    <td style="font-weight:600;">${sec.name}</td>
                    <td class="mono-val">₹${sec.price?.toLocaleString('en-IN') || '--'}</td>
                    <td class="mono-val ${sec.change_1d >= 0 ? 'text-green' : 'text-red'}">${sec.change_1d >= 0 ? '+' : ''}${sec.change_1d}%</td>
                    <td class="mono-val ${sec.change_5d >= 0 ? 'text-green' : 'text-red'}">${sec.change_5d >= 0 ? '+' : ''}${sec.change_5d}%</td>
                    <td class="mono-val ${sec.change_20d >= 0 ? 'text-green' : 'text-red'}">${sec.change_20d >= 0 ? '+' : ''}${sec.change_20d}%</td>
                    <td><span class="badge ${sec.above_20_ema ? 'badge-success' : 'badge-danger'}">${sec.trend}</span></td>
                </tr>
            `).join("");
        }

    } catch (err) {
        console.error("Error loading regime:", err);
    }
}

/* ==========================================================================
   SCANNER & CANDIDATE RANKINGS
   ========================================================================== */
function initScannerControls() {
    const slider = document.getElementById("score-slider");
    const sliderLabel = document.getElementById("score-val-label");
    slider.addEventListener("input", (e) => {
        sliderLabel.textContent = e.target.value;
    });

    const runBtn = document.getElementById("run-scan-btn");
    runBtn.addEventListener("click", executeMarketScan);

    const refreshRegimeBtn = document.getElementById("refresh-regime-btn");
    if (refreshRegimeBtn) refreshRegimeBtn.addEventListener("click", loadMarketRegime);
}

async function executeMarketScan() {
    const universe = document.getElementById("universe-select").value;
    const setup = document.getElementById("setup-select").value;
    const minScore = parseFloat(document.getElementById("score-slider").value) || 0;

    const progressBar = document.getElementById("scan-progress-bar");
    const runBtn = document.getElementById("run-scan-btn");
    const tbody = document.getElementById("candidates-tbody");

    progressBar.classList.remove("hidden");
    runBtn.disabled = true;
    runBtn.innerHTML = `<span>⏳</span> Scanning...`;

    try {
        const resp = await fetch("/api/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ universe, setup, min_score: minScore })
        });
        const json = await resp.json();

        if (json.status !== "success") {
            tbody.innerHTML = `<tr><td colspan="10" class="empty-state text-red">Scan error: ${json.message}</td></tr>`;
            return;
        }

        const candidates = json.candidates || [];
        document.getElementById("candidate-count").textContent = candidates.length;

        if (candidates.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="empty-state">No stocks matched current criteria. Try lowering the Min Score or changing the Setup filter.</td></tr>`;
            return;
        }

        tbody.innerHTML = candidates.map((c, idx) => {
            let scoreClass = "";
            if (c.composite_score >= 80) scoreClass = "high";
            else if (c.composite_score >= 65) scoreClass = "mid";

            let riskBadgeClass = "badge-success";
            if (c.event_risk_level === "VERY HIGH" || c.event_risk_level === "HIGH") riskBadgeClass = "badge-danger";
            else if (c.event_risk_level === "MEDIUM") riskBadgeClass = "badge-warning";

            return `
                <tr>
                    <td class="mono-val" style="color:var(--text-dim);">${idx + 1}</td>
                    <td>
                        <div style="font-weight:700; font-size:0.95rem;">${c.symbol}</div>
                        <div style="font-size:0.72rem; color:var(--text-dim);">${c.sector || 'Equities'}</div>
                    </td>
                    <td>
                        <span class="score-badge ${scoreClass}">${c.composite_score}/100</span>
                    </td>
                    <td>
                        <div class="mono-val">₹${c.close?.toLocaleString('en-IN') || '--'}</div>
                        <div class="mono-val ${c.change_1d >= 0 ? 'text-green' : 'text-red'}" style="font-size:0.76rem;">
                            ${c.change_1d >= 0 ? '+' : ''}${c.change_1d}%
                        </div>
                    </td>
                    <td>
                        <span class="badge badge-info">${c.primary_setup}</span>
                    </td>
                    <td>
                        <span class="mono-val ${c.volume_multiplier >= 1.8 ? 'text-green' : ''}">${c.volume_multiplier}x</span>
                        ${c.volume_multiplier >= 2.0 ? '<span title="Volume Surge">🔥</span>' : ''}
                    </td>
                    <td>
                        <span class="badge ${c.rs_score >= 75 ? 'badge-success' : 'badge-purple'}">${c.rs_percentile || 'Top RS'}</span>
                        <div style="font-size:0.72rem; color:var(--text-dim); margin-top:2px;">Alpha: ${c.alpha_20d >= 0 ? '+' : ''}${c.alpha_20d}%</div>
                    </td>
                    <td>
                        <span style="font-size:0.82rem; font-family:var(--font-mono);">${c.days_to_results_display}</span>
                    </td>
                    <td>
                        <span class="badge ${riskBadgeClass}">${c.event_risk_badge}</span>
                    </td>
                    <td>
                        <button class="btn btn-xs btn-primary" onclick="inspectStock('${c.symbol}')">
                            Deep Dive 🔍
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Scan error:", err);
        tbody.innerHTML = `<tr><td colspan="10" class="empty-state text-red">Scan request failed: ${err.message}</td></tr>`;
    } finally {
        progressBar.classList.add("hidden");
        runBtn.disabled = false;
        runBtn.innerHTML = `<span class="btn-icon">⚡</span> Run Market Scan`;
    }
}

function inspectStock(symbol) {
    switchToTab("deepdive-view");
    document.getElementById("deepdive-input").value = symbol;
    fetchAndRenderDeepDive(symbol);
}

/* ==========================================================================
   STOCK 360° DEEP-DIVE & THESIS CARD
   ========================================================================== */
function initDeepDive() {
    const btn = document.getElementById("deepdive-btn");
    const input = document.getElementById("deepdive-input");

    btn.addEventListener("click", () => {
        const sym = input.value.trim().toUpperCase();
        if (sym) fetchAndRenderDeepDive(sym);
    });

    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const sym = input.value.trim().toUpperCase();
            if (sym) fetchAndRenderDeepDive(sym);
        }
    });

    // Quick pick chip buttons
    document.querySelectorAll(".chip-btn").forEach(chip => {
        chip.addEventListener("click", () => {
            const sym = chip.getAttribute("data-sym");
            input.value = sym;
            fetchAndRenderDeepDive(sym);
        });
    });

    // Initial load for default stock
    fetchAndRenderDeepDive("TRENT");
}

async function fetchAndRenderDeepDive(symbol) {
    const loading = document.getElementById("deepdive-loading");
    const container = document.getElementById("deepdive-content");
    loading.classList.remove("hidden");

    try {
        const resp = await fetch(`/api/stock/${symbol}`);
        const json = await resp.json();
        if (json.status !== "success") {
            container.innerHTML = `<div class="glass-card empty-state text-red">Could not load stock data for ${symbol}: ${json.message}</div>`;
            return;
        }

        const data = json.data;
        renderThesisCard(data);
    } catch (err) {
        console.error("Deep dive fetch error:", err);
        container.innerHTML = `<div class="glass-card empty-state text-red">Failed to fetch deep dive for ${symbol}: ${err.message}</div>`;
    } finally {
        loading.classList.add("hidden");
    }
}

function renderThesisCard(data) {
    const container = document.getElementById("deepdive-content");
    const tech = data.technicals || {};
    const rs = data.relative_strength || {};
    const fund = data.fundamentals || {};
    const events = data.corporate_events || {};
    const trade = tech.trade_structure || {};
    const news = data.news || [];
    const ratios = fund.ratios || {};
    const growth = fund.growth_metrics || {};

    let scoreClass = "high";
    if (data.composite_score < 65) scoreClass = "mid";

    let riskBadgeClass = "badge-success";
    if (events.event_risk_level === "VERY HIGH" || events.event_risk_level === "HIGH") riskBadgeClass = "badge-danger";
    else if (events.event_risk_level === "MEDIUM") riskBadgeClass = "badge-warning";

    container.innerHTML = `
        <!-- Header Strip -->
        <div class="glass-card thesis-header-card">
            <div>
                <div class="thesis-stock-title">${data.company_name} <span style="color:var(--primary); font-size:1.4rem;">(${data.symbol})</span></div>
                <div class="thesis-stock-sector">NSE Sector: <strong>${data.sector}</strong> | Market Cap: <strong>${ratios['Market Cap'] || 'Large/Midcap'}</strong></div>
            </div>

            <div style="display:flex; gap:24px; align-items:center;">
                <div style="text-align:right;">
                    <div class="mono-val" style="font-size:1.6rem;">₹${tech.close?.toLocaleString('en-IN') || '--'}</div>
                    <div class="mono-val ${tech.change_pct_1d >= 0 ? 'text-green' : 'text-red'}" style="font-weight:700;">
                        ${tech.change_pct_1d >= 0 ? '+' : ''}${tech.change_pct_1d}% Today
                    </div>
                </div>

                <div class="thesis-score-box">
                    <div style="font-size:0.7rem; font-weight:800; color:var(--text-dim); letter-spacing:0.8px;">COMPOSITE SCORE</div>
                    <div class="thesis-score-num">${data.composite_score}<span style="font-size:1.1rem; color:var(--text-dim);">/100</span></div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">
                        Tech: ${data.score_breakdown?.technical} | RS: ${data.score_breakdown?.relative_strength} | Fund: ${data.score_breakdown?.fundamentals}
                    </div>
                </div>
            </div>
        </div>

        <!-- 2-Column Grid -->
        <div class="thesis-grid">
            <!-- Left Column: Chart, Trade Plan, Fundamentals -->
            <div class="thesis-left-col">
                <!-- Interactive Chart Card -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 style="font-size:1.1rem;">Price History & EMAs (90 Days)</h3>
                        <div class="quick-pills">
                            <span class="badge badge-info">20 EMA: ₹${tech.ema_20}</span>
                            <span class="badge badge-purple">50 EMA: ₹${tech.ema_50}</span>
                        </div>
                    </div>
                    <div style="position:relative; height:320px; width:100%;">
                        <canvas id="stock-chart-canvas"></canvas>
                    </div>
                </div>

                <!-- Swing Trade Structure Card -->
                <div class="glass-card">
                    <h3 style="font-size:1.1rem; display:flex; justify-content:space-between;">
                        <span>🎯 Swing Trade Execution Plan</span>
                        <span class="badge badge-success">Risk:Reward ${trade.risk_reward || '1 : 2.5'}</span>
                    </h3>
                    <div class="trade-structure-box">
                        <div class="trade-levels-grid">
                            <div class="trade-tile">
                                <div class="trade-tile-label">Recommended Entry</div>
                                <div class="trade-tile-val text-accent">₹${trade.entry}</div>
                            </div>
                            <div class="trade-tile stop">
                                <div class="trade-tile-label">Stop Loss</div>
                                <div class="trade-tile-val text-red">₹${trade.stop_loss}</div>
                                <div style="font-size:0.72rem; color:#fb7185;">${trade.stop_loss_pct}%</div>
                            </div>
                            <div class="trade-tile target">
                                <div class="trade-tile-label">Target 1 (2R)</div>
                                <div class="trade-tile-val text-green">₹${trade.target_1}</div>
                                <div style="font-size:0.72rem; color:#34d399;">+${trade.target_1_pct}%</div>
                            </div>
                            <div class="trade-tile target">
                                <div class="trade-tile-label">Target 2 (3R)</div>
                                <div class="trade-tile-val text-green">₹${trade.target_2}</div>
                                <div style="font-size:0.72rem; color:#34d399;">+${trade.target_2_pct}%</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Screener.in Fundamentals & Financial Health -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="font-size:1.1rem;">Screener.in Financial Analysis</h3>
                        <span class="badge badge-info">Quality Score: ${fund.fundamental_score}/100</span>
                    </div>

                    <div class="ratios-grid">
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">Stock P/E</div>
                            <div class="ratio-tile-val">${ratios['Stock P/E'] || 'N/A'}</div>
                        </div>
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">ROCE</div>
                            <div class="ratio-tile-val text-green">${ratios['ROCE'] || 'N/A'}</div>
                        </div>
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">ROE</div>
                            <div class="ratio-tile-val text-green">${ratios['ROE'] || 'N/A'}</div>
                        </div>
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">Book Value</div>
                            <div class="ratio-tile-val">${ratios['Book Value'] || 'N/A'}</div>
                        </div>
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">Sales YoY Growth</div>
                            <div class="ratio-tile-val ${growth.sales_yoy_growth_pct >= 0 ? 'text-green' : 'text-red'}">
                                ${growth.sales_yoy_growth_pct ? growth.sales_yoy_growth_pct + '%' : 'N/A'}
                            </div>
                        </div>
                        <div class="ratio-tile">
                            <div class="ratio-tile-name">PAT YoY Growth</div>
                            <div class="ratio-tile-val ${growth.pat_yoy_growth_pct >= 0 ? 'text-green' : 'text-red'}">
                                ${growth.pat_yoy_growth_pct ? growth.pat_yoy_growth_pct + '%' : 'N/A'}
                            </div>
                        </div>
                    </div>

                    <!-- Screener Pros & Cons -->
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;">
                        <div>
                            <div style="font-size:0.78rem; font-weight:700; color:#34d399; margin-bottom:6px;">PROS</div>
                            ${(fund.pros && fund.pros.length > 0) ? fund.pros.slice(0, 3).map(p => `
                                <div class="checklist-item"><span class="checklist-icon text-green">✓</span> ${p}</div>
                            `).join("") : '<div class="checklist-item" style="color:var(--text-dim);">No specific pros highlighted.</div>'}
                        </div>
                        <div>
                            <div style="font-size:0.78rem; font-weight:700; color:#fb7185; margin-bottom:6px;">CONS / WATCHOUTS</div>
                            ${(fund.cons && fund.cons.length > 0) ? fund.cons.slice(0, 3).map(c => `
                                <div class="checklist-item"><span class="checklist-icon text-red">⚠</span> ${c}</div>
                            `).join("") : '<div class="checklist-item" style="color:var(--text-dim);">No significant cons reported.</div>'}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Setup Thesis, Events & Filings, News, Invalidation -->
            <div class="thesis-right-col">
                <!-- Why It Appeared / Technical Setup -->
                <div class="glass-card">
                    <h3 style="font-size:1.1rem; margin-bottom:10px;">Why It Appeared</h3>
                    <div class="checklist-item">
                        <span class="checklist-icon ${tech.is_ema_bullish_stack ? 'text-green' : 'text-accent'}">✓</span>
                        <span>EMA Trend: <strong>${tech.is_ema_bullish_stack ? 'Bullish Stack (20>50>200)' : 'Above Key EMAs'}</strong></span>
                    </div>
                    <div class="checklist-item">
                        <span class="checklist-icon text-green">✓</span>
                        <span>Relative Strength: <strong>${rs.rs_percentile || 'Strong'}</strong> vs NIFTY 50 (Alpha: ${rs.alpha_20d >= 0 ? '+' : ''}${rs.alpha_20d}%)</span>
                    </div>
                    <div class="checklist-item">
                        <span class="checklist-icon ${tech.volume_multiplier >= 1.5 ? 'text-green' : 'text-dim'}">✓</span>
                        <span>Volume: <strong>${tech.volume_multiplier}x</strong> of 20-Day SMA</span>
                    </div>
                    <div class="checklist-item">
                        <span class="checklist-icon text-green">✓</span>
                        <span>RSI: <strong>${tech.rsi}</strong> (Sweet spot 50-70)</span>
                    </div>
                    <div class="checklist-item">
                        <span class="checklist-icon text-green">✓</span>
                        <span>52W High Range: <strong>${tech.pct_from_52w_high}%</strong> from 52W High</span>
                    </div>
                </div>

                <!-- NSE Results Calendar & Event Risk -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h3 style="font-size:1.1rem;">NSE Events & Results Risk</h3>
                        <span class="badge ${riskBadgeClass}">${events.event_risk_level} RISK</span>
                    </div>

                    <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:var(--radius-sm); border:1px solid var(--border-color); margin-bottom:12px;">
                        <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase;">Next Earnings Results Date</div>
                        <div style="font-family:var(--font-mono); font-size:1.1rem; font-weight:700; color:var(--text-main); margin:2px 0;">
                            ${events.next_results_date} <span style="font-size:0.85rem; color:var(--primary);">(${events.days_to_results_display})</span>
                        </div>
                        <div style="font-size:0.8rem; color:var(--text-muted);">${events.event_risk_description}</div>
                    </div>

                    <!-- Upcoming Board Meetings -->
                    <div style="font-size:0.78rem; font-weight:700; color:var(--text-dim); text-transform:uppercase; margin-bottom:6px;">Recent Board Filings</div>
                    ${(events.upcoming_board_meetings && events.upcoming_board_meetings.length > 0) ? events.upcoming_board_meetings.slice(0, 2).map(m => `
                        <div class="checklist-item" style="font-size:0.8rem;">
                            <span class="checklist-icon">📅</span>
                            <span><strong>${m.meeting_date}:</strong> ${m.purpose}</span>
                        </div>
                    `).join("") : '<div style="font-size:0.8rem; color:var(--text-dim);">No upcoming board meetings listed on NSE.</div>'}
                </div>

                <!-- Bear Case & Invalidation -->
                <div class="glass-card" style="border-left:4px solid var(--amber);">
                    <h3 style="font-size:1.1rem; color:var(--amber); margin-bottom:10px;">⚠ Invalidation & Bear Case</h3>
                    ${data.bear_case.map(b => `
                        <div class="checklist-item" style="color:#fbbf24; font-size:0.82rem;">
                            <span class="checklist-icon">⚠</span> <span>${b}</span>
                        </div>
                    `).join("")}
                </div>

                <!-- Latest Material News -->
                <div class="glass-card">
                    <h3 style="font-size:1.1rem; margin-bottom:10px;">📰 Latest Material News</h3>
                    <div class="news-list">
                        ${(news && news.length > 0) ? news.slice(0, 4).map(n => `
                            <div class="news-item">
                                <span class="news-tag">${n.event_tag}</span>
                                <a href="${n.link}" target="_blank" rel="noopener noreferrer" class="news-title">${n.title}</a>
                                <span class="news-meta">${n.source} • ${n.published_at}</span>
                            </div>
                        `).join("") : '<div class="empty-state">No recent articles found.</div>'}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render interactive chart
    renderChart(data.chart);
}

function renderChart(chartData) {
    if (!chartData || !chartData.dates) return;
    const canvas = document.getElementById("stock-chart-canvas");
    if (!canvas) return;

    if (activeChart) {
        activeChart.destroy();
    }

    const ctx = canvas.getContext("2d");
    activeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [
                {
                    label: 'Close (₹)',
                    data: chartData.close,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.15,
                    pointRadius: 0,
                    pointHoverRadius: 5
                },
                {
                    label: '20 EMA',
                    data: chartData.ema_20,
                    borderColor: '#34d399',
                    borderWidth: 1.5,
                    borderDash: [3, 3],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: '50 EMA',
                    data: chartData.ema_50,
                    borderColor: '#c084fc',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#94a3b8', boxWidth: 12, font: { family: 'Inter', size: 11 } }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleColor: '#f8fafc',
                    bodyColor: '#38bdf8',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#64748b', maxTicksLimit: 8, font: { family: 'JetBrains Mono', size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

/* ==========================================================================
   MANUAL FETCHER TESTING STUDIO
   ========================================================================== */
function initManualTester() {
    const runBtn = document.getElementById("run-test-btn");
    const copyBtn = document.getElementById("copy-json-btn");

    runBtn.addEventListener("click", executeManualFetchTest);
    copyBtn.addEventListener("click", () => {
        const text = document.getElementById("tester-json-content").textContent;
        navigator.clipboard.writeText(text);
        copyBtn.textContent = "Copied! ✓";
        setTimeout(() => copyBtn.textContent = "Copy JSON", 1500);
    });
}

async function executeManualFetchTest() {
    const target = document.getElementById("tester-target").value;
    const symbol = document.getElementById("tester-symbol").value.trim().toUpperCase() || "TRENT";
    const loading = document.getElementById("tester-loading");
    const visualBody = document.getElementById("tester-visual-content");
    const jsonPre = document.getElementById("tester-json-content");

    loading.classList.remove("hidden");

    try {
        const resp = await fetch("/api/test-fetch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target, symbol })
        });
        const json = await resp.json();
        
        jsonPre.textContent = JSON.stringify(json, null, 2);

        if (json.status !== "success") {
            visualBody.innerHTML = `<div class="empty-state text-red">Error: ${json.message}</div>`;
            return;
        }

        const res = json.result;
        renderVisualTesterOutput(target, symbol, res, visualBody);
    } catch (err) {
        jsonPre.textContent = JSON.stringify({ error: err.message }, null, 2);
        visualBody.innerHTML = `<div class="empty-state text-red">Request Failed: ${err.message}</div>`;
    } finally {
        loading.classList.add("hidden");
    }
}

function renderVisualTesterOutput(target, symbol, res, container) {
    if (!res) {
        container.innerHTML = `<div class="empty-state">No result returned.</div>`;
        return;
    }

    if (target === "technicals") {
        container.innerHTML = `
            <div style="border-left:4px solid var(--primary); padding-left:12px; margin-bottom:12px;">
                <h4>${symbol} Technical Summary</h4>
                <div class="mono-val" style="font-size:1.4rem;">₹${res.close} (${res.change_pct_1d >= 0 ? '+' : ''}${res.change_pct_1d}%)</div>
                <div style="font-size:0.85rem; color:var(--text-muted);">Setup: <strong class="text-accent">${res.primary_setup}</strong></div>
            </div>
            <div class="ratios-grid">
                <div class="ratio-tile"><div class="ratio-tile-name">20 EMA</div><div class="ratio-tile-val">₹${res.ema_20}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">50 EMA</div><div class="ratio-tile-val">₹${res.ema_50}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">200 EMA</div><div class="ratio-tile-val">₹${res.ema_200}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">RSI (14)</div><div class="ratio-tile-val">${res.rsi}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">Volume Mult</div><div class="ratio-tile-val">${res.volume_multiplier}x</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">ATR (14)</div><div class="ratio-tile-val">₹${res.atr}</div></div>
            </div>
            <div class="trade-structure-box" style="margin-top:14px;">
                <div style="font-size:0.75rem; font-weight:700; color:var(--text-dim);">CALCULATED SWING TRADE LEVELS</div>
                <div class="trade-levels-grid" style="margin-top:6px;">
                    <div class="trade-tile"><div class="trade-tile-label">Entry</div><div class="trade-tile-val">₹${res.trade_structure?.entry}</div></div>
                    <div class="trade-tile stop"><div class="trade-tile-label">Stop</div><div class="trade-tile-val text-red">₹${res.trade_structure?.stop_loss}</div></div>
                    <div class="trade-tile target"><div class="trade-tile-label">Target 1</div><div class="trade-tile-val text-green">₹${res.trade_structure?.target_1}</div></div>
                    <div class="trade-tile target"><div class="trade-tile-label">Target 2</div><div class="trade-tile-val text-green">₹${res.trade_structure?.target_2}</div></div>
                </div>
            </div>
        `;
    } else if (target === "screener") {
        const ratios = res.ratios || {};
        container.innerHTML = `
            <div style="border-left:4px solid var(--green); padding-left:12px; margin-bottom:12px;">
                <h4>${res.company_name || symbol}</h4>
                <div style="font-size:0.85rem; color:var(--text-muted);">${res.about?.slice(0, 140)}...</div>
            </div>
            <div class="ratios-grid">
                ${Object.entries(ratios).slice(0, 8).map(([k, v]) => `
                    <div class="ratio-tile"><div class="ratio-tile-name">${k}</div><div class="ratio-tile-val">${v}</div></div>
                `).join("")}
            </div>
        `;
    } else if (target === "events") {
        const ev = res.events || {};
        const meetings = ev.upcoming_board_meetings || [];
        container.innerHTML = `
            <div style="background:rgba(0,0,0,0.25); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-color); margin-bottom:12px;">
                <div style="font-size:0.75rem; color:var(--text-dim);">NEXT RESULTS CALENDAR</div>
                <div style="font-family:var(--font-mono); font-size:1.2rem; font-weight:700;">${ev.next_results_date} (${ev.days_to_results_display})</div>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">${ev.event_risk_badge} — ${ev.event_risk_description}</div>
            </div>
            <h4>Recent Board Filings from NSE:</h4>
            ${meetings.slice(0, 3).map(m => `
                <div class="checklist-item">📅 <strong>${m.meeting_date}:</strong> ${m.purpose}</div>
            `).join("")}
        `;
    } else if (target === "news") {
        container.innerHTML = `
            <h4>Latest Google News for ${symbol}</h4>
            <div class="news-list" style="margin-top:10px;">
                ${Array.isArray(res) ? res.slice(0, 5).map(n => `
                    <div class="news-item">
                        <span class="news-tag">${n.event_tag}</span>
                        <a href="${n.link}" target="_blank" class="news-title">${n.title}</a>
                        <span class="news-meta">${n.source} • ${n.published_at}</span>
                    </div>
                `).join("") : 'No news found.'}
            </div>
        `;
    } else if (target === "quote") {
        container.innerHTML = `
            <h4>NSE Official Quote: ${symbol}</h4>
            <div class="ratios-grid" style="margin-top:10px;">
                <div class="ratio-tile"><div class="ratio-tile-name">Last Price</div><div class="ratio-tile-val">₹${res.last_price}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">1D Change</div><div class="ratio-tile-val ${res.pChange >= 0 ? 'text-green' : 'text-red'}">${res.pChange}%</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">VWAP</div><div class="ratio-tile-val">₹${res.vwap}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">Day Range</div><div class="ratio-tile-val">₹${res.day_low} - ₹${res.day_high}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">52W High</div><div class="ratio-tile-val">₹${res.week_52_high}</div></div>
                <div class="ratio-tile"><div class="ratio-tile-name">52W Low</div><div class="ratio-tile-val">₹${res.week_52_low}</div></div>
            </div>
        `;
    } else if (target === "regime") {
        container.innerHTML = `
            <div class="regime-huge-badge">${res.regime_badge}</div>
            <p>${res.guidance}</p>
        `;
    }
}
