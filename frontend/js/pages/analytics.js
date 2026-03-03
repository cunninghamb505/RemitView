/* Analytics page — denial trends, payer comparison, adjustment summary */
const AnalyticsPage = {
    charts: {},

    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">Analytics</h2>

            <div class="card" style="margin-bottom: 24px;">
                <div class="card-header">
                    <span class="card-title">Denial & Adjustment Trends</span>
                    <div class="input-group">
                        <label style="font-size:0.85rem; color:var(--text-secondary);">Group by:</label>
                        <select id="trend-group-by">
                            <option value="reason">Reason Code</option>
                            <option value="payer">Payer</option>
                            <option value="provider">Provider</option>
                        </select>
                        <input type="text" id="trend-start" placeholder="Start (YYYYMMDD)" style="width:130px;">
                        <input type="text" id="trend-end" placeholder="End (YYYYMMDD)" style="width:130px;">
                        <button class="btn btn-primary btn-sm" id="trend-refresh">Refresh</button>
                    </div>
                </div>
                <div class="chart-container" id="trend-chart-container">
                    <canvas id="trend-chart"></canvas>
                </div>
                <div id="trend-empty" class="empty-state" style="display:none;">
                    <div class="empty-state-text">No trend data available. Upload files with date information to see trends.</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Payer Comparison</span>
                    </div>
                    <div class="chart-container" id="payer-chart-container">
                        <canvas id="payer-chart"></canvas>
                    </div>
                    <div id="payer-table-container" style="margin-top: 16px;"></div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Adjustment Summary</span>
                    </div>
                    <div class="chart-container" id="adj-chart-container">
                        <canvas id="adj-chart"></canvas>
                    </div>
                    <div id="adj-table-container" style="margin-top: 16px;"></div>
                </div>
            </div>
        `;

        this.bindEvents();
        await Promise.all([
            this.loadTrends(),
            this.loadPayerComparison(),
            this.loadAdjustmentSummary(),
        ]);
    },

    bindEvents() {
        document.getElementById('trend-refresh').addEventListener('click', () => this.loadTrends());
    },

    async loadTrends() {
        const groupBy = document.getElementById('trend-group-by').value;
        const startDate = document.getElementById('trend-start').value.trim();
        const endDate = document.getElementById('trend-end').value.trim();

        try {
            const params = new URLSearchParams({ group_by: groupBy });
            if (startDate) params.set('start_date', startDate);
            if (endDate) params.set('end_date', endDate);

            const data = await API.getJSON(`/api/analytics/denial-trends?${params}`);

            ChartHelper.destroy(this.charts.trend);
            const chartEl = document.getElementById('trend-chart');
            const emptyEl = document.getElementById('trend-empty');

            if (!data.series || data.series.length === 0 || !data.periods || data.periods.length === 0) {
                chartEl.style.display = 'none';
                emptyEl.style.display = 'block';
                return;
            }

            chartEl.style.display = 'block';
            emptyEl.style.display = 'none';

            const datasets = data.series.map(s => ({
                label: s.label,
                data: s.amounts,
            }));

            this.charts.trend = ChartHelper.createLine(chartEl, data.periods, datasets, 'Adjustment Amounts Over Time');
        } catch (err) {
            console.error('Trend load error:', err);
        }
    },

    async loadPayerComparison() {
        const chartContainer = document.getElementById('payer-chart-container');
        const tableContainer = document.getElementById('payer-table-container');

        try {
            const data = await API.getJSON('/api/analytics/payer-comparison');
            const payers = data.payers || [];

            if (payers.length === 0) {
                chartContainer.innerHTML = '<div class="empty-state"><div class="empty-state-text">No payer data</div></div>';
                return;
            }

            ChartHelper.destroy(this.charts.payer);
            const canvas = document.getElementById('payer-chart');

            this.charts.payer = ChartHelper.createBar(
                canvas,
                payers.map(p => p.payer_name),
                [
                    { label: 'Total Payments', data: payers.map(p => p.total_payments || 0) },
                    { label: 'Total Charges', data: payers.map(p => p.total_charges || 0) },
                ],
                'Payer Payment vs Charges'
            );

            // Payer stats table
            let html = '<div class="table-wrapper"><table><thead><tr>';
            html += '<th>Payer</th><th class="text-right">Claims</th><th class="text-right">Payment Rate</th><th class="text-right">Denial Rate</th><th class="text-right">Avg Payment</th>';
            html += '</tr></thead><tbody>';
            for (const p of payers) {
                html += `<tr>
                    <td>${this.esc(p.payer_name)}</td>
                    <td class="text-right">${p.total_claims}</td>
                    <td class="text-right">${p.payment_rate}%</td>
                    <td class="text-right">${p.denial_rate}%</td>
                    <td class="text-right">$${this.fmt(p.avg_payment)}</td>
                </tr>`;
            }
            html += '</tbody></table></div>';
            tableContainer.innerHTML = html;
        } catch (err) {
            console.error('Payer comparison error:', err);
            chartContainer.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error loading payer data</div></div>`;
        }
    },

    async loadAdjustmentSummary() {
        const chartContainer = document.getElementById('adj-chart-container');
        const tableContainer = document.getElementById('adj-table-container');

        try {
            const data = await API.getJSON('/api/analytics/adjustment-summary');
            const groups = data.group_summary || [];
            const details = data.details || [];

            if (groups.length === 0) {
                chartContainer.innerHTML = '<div class="empty-state"><div class="empty-state-text">No adjustment data</div></div>';
                return;
            }

            ChartHelper.destroy(this.charts.adj);
            const canvas = document.getElementById('adj-chart');

            this.charts.adj = ChartHelper.createDoughnut(
                canvas,
                groups.map(g => `${g.group_code} - ${g.group_description}`),
                groups.map(g => Math.abs(g.total_amount || 0)),
                'Adjustments by Group Code'
            );

            // Detail table
            let html = '<div class="table-wrapper"><table><thead><tr>';
            html += '<th>Group</th><th>Code</th><th>Description</th><th class="text-right">Amount</th><th class="text-right">Count</th>';
            html += '</tr></thead><tbody>';
            for (const d of details) {
                html += `<tr>
                    <td><span class="badge badge-info">${d.group_code}</span></td>
                    <td class="text-mono">${d.reason_code}</td>
                    <td>${this.esc(d.reason_description)}</td>
                    <td class="text-right">$${this.fmt(d.total_amount)}</td>
                    <td class="text-right">${d.count}</td>
                </tr>`;
            }
            html += '</tbody></table></div>';
            tableContainer.innerHTML = html;
        } catch (err) {
            console.error('Adjustment summary error:', err);
            chartContainer.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error loading adjustment data</div></div>`;
        }
    },

    fmt(val) {
        return (Number(val) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
