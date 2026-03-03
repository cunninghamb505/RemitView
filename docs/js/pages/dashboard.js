/* Dashboard page — summary cards and stats tables */
const DashboardPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading dashboard...</div>';

        try {
            const data = await API.getDashboard();

            if (data.file_count === 0) {
                content.innerHTML = `
                    <h2 style="margin-bottom: 16px;">Dashboard</h2>
                    <div class="empty-state">
                        <div class="empty-state-text">No files loaded yet.</div>
                        <a href="#/files" class="btn btn-primary">Go to Files</a>
                    </div>
                `;
                return;
            }

            let html = `
                <h2 style="margin-bottom: 16px;">Dashboard</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">$${this.formatMoney(data.total_payments)}</div>
                        <div class="stat-label">Total Payments</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">$${this.formatMoney(data.total_charges)}</div>
                        <div class="stat-label">Total Charges</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">$${this.formatMoney(data.total_adjustments)}</div>
                        <div class="stat-label">Total Adjustments</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.total_claims}</div>
                        <div class="stat-label">Total Claims</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div class="card">
                        <div class="card-title" style="margin-bottom: 12px;">Claims by Status</div>
                        ${this.renderStatusTable(data.claims_by_status)}
                    </div>
                    <div class="card">
                        <div class="card-title" style="margin-bottom: 12px;">Top Adjustment Reasons (Service Level)</div>
                        ${this.renderAdjustmentTable(data.top_denial_reasons)}
                    </div>
                </div>
            `;

            if (data.top_adjustments && data.top_adjustments.length > 0) {
                html += `
                    <div class="card" style="margin-top: 16px;">
                        <div class="card-title" style="margin-bottom: 12px;">Top Adjustment Reasons (Claim Level)</div>
                        ${this.renderAdjustmentTable(data.top_adjustments)}
                    </div>
                `;
            }

            content.innerHTML = html;
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    renderStatusTable(items) {
        if (!items || items.length === 0) return '<div class="empty-state"><div class="empty-state-text">No data</div></div>';

        let html = '<div class="table-wrapper"><table><thead><tr><th>Status</th><th>Description</th><th class="text-right">Count</th></tr></thead><tbody>';
        for (const item of items) {
            const badge = this.statusBadge(item.status_code);
            html += `<tr>
                <td>${badge}</td>
                <td>${item.status_description}</td>
                <td class="text-right">${item.count}</td>
            </tr>`;
        }
        html += '</tbody></table></div>';
        return html;
    },

    renderAdjustmentTable(items) {
        if (!items || items.length === 0) return '<div class="empty-state"><div class="empty-state-text">No adjustments</div></div>';

        let html = '<div class="table-wrapper"><table><thead><tr><th>Group</th><th>Code</th><th>Description</th><th class="text-right">Amount</th><th class="text-right">Count</th></tr></thead><tbody>';
        for (const item of items) {
            html += `<tr>
                <td><span class="badge badge-info">${item.group_code}</span></td>
                <td class="text-mono">${item.reason_code}</td>
                <td>${item.reason_description}</td>
                <td class="text-right">$${this.formatMoney(item.total_amount)}</td>
                <td class="text-right">${item.count}</td>
            </tr>`;
        }
        html += '</tbody></table></div>';
        return html;
    },

    statusBadge(code) {
        const classes = { '1': 'badge-success', '2': 'badge-info', '3': 'badge-info', '4': 'badge-danger', '22': 'badge-warning' };
        return `<span class="badge ${classes[code] || 'badge-primary'}">${code}</span>`;
    },

    formatMoney(val) {
        return (Number(val) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
};
