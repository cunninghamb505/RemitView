/* File comparison page — diff between two files */
const FileComparePage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading...</div>';

        let files = [];
        try {
            const data = await API.listFiles();
            files = data.files || [];
        } catch (_) {}

        if (files.length < 2) {
            content.innerHTML = `
                <h2 style="margin-bottom: 16px;">File Compare</h2>
                <div class="empty-state">
                    <div class="empty-state-text">You need at least 2 files to compare. Upload more files first.</div>
                    <a href="#/files" class="btn btn-primary">Go to Files</a>
                </div>
            `;
            return;
        }

        const opts = files.map(f => `<option value="${f.id}">${this.esc(f.filename)}</option>`).join('');

        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">File Compare</h2>
            <div class="card" style="margin-bottom: 24px;">
                <div class="filter-bar">
                    <label>File 1:</label>
                    <select id="compare-file1">${opts}</select>
                    <label>File 2:</label>
                    <select id="compare-file2">${opts}</select>
                    <button class="btn btn-primary" id="compare-btn">Compare</button>
                </div>
            </div>
            <div id="compare-results"></div>
        `;

        // Default file2 to second file
        if (files.length >= 2) {
            document.getElementById('compare-file2').value = files[1].id;
        }

        document.getElementById('compare-btn').addEventListener('click', () => this.loadComparison());
    },

    async loadComparison() {
        const file1 = document.getElementById('compare-file1').value;
        const file2 = document.getElementById('compare-file2').value;
        const results = document.getElementById('compare-results');

        if (file1 === file2) {
            Toast.error('Select two different files');
            return;
        }

        results.innerHTML = '<div class="loading-spinner">Comparing...</div>';

        try {
            const data = await API.getJSON(`/api/compare?file1=${file1}&file2=${file2}`);

            let html = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${data.summary.file1_count}</div>
                        <div class="stat-label">File 1 Claims</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.summary.file2_count}</div>
                        <div class="stat-label">File 2 Claims</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: var(--danger);">${data.summary.removed_count}</div>
                        <div class="stat-label">Removed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: var(--success);">${data.summary.added_count}</div>
                        <div class="stat-label">Added</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: var(--warning);">${data.summary.changed_count}</div>
                        <div class="stat-label">Changed</div>
                    </div>
                </div>
            `;

            // Removed claims
            if (data.removed.length > 0) {
                html += `<div class="card" style="margin-bottom: 16px; border-left: 4px solid var(--danger);">
                    <div class="card-title" style="margin-bottom: 12px;">Removed Claims (in File 1, not in File 2)</div>
                    ${this.renderClaimTable(data.removed)}
                </div>`;
            }

            // Changed claims
            if (data.changed.length > 0) {
                html += `<div class="card" style="margin-bottom: 16px; border-left: 4px solid var(--warning);">
                    <div class="card-title" style="margin-bottom: 12px;">Changed Claims</div>
                    ${this.renderChangedTable(data.changed)}
                </div>`;
            }

            // Added claims
            if (data.added.length > 0) {
                html += `<div class="card" style="margin-bottom: 16px; border-left: 4px solid var(--success);">
                    <div class="card-title" style="margin-bottom: 12px;">Added Claims (in File 2, not in File 1)</div>
                    ${this.renderClaimTable(data.added)}
                </div>`;
            }

            if (data.removed.length === 0 && data.changed.length === 0 && data.added.length === 0) {
                html += '<div class="empty-state"><div class="empty-state-text">Files contain identical claims.</div></div>';
            }

            results.innerHTML = html;
        } catch (err) {
            results.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    renderClaimTable(claims) {
        let html = '<div class="table-wrapper"><table><thead><tr>';
        html += '<th>Claim ID</th><th>Status</th><th>Patient</th><th class="text-right">Charge</th><th class="text-right">Payment</th>';
        html += '</tr></thead><tbody>';
        for (const c of claims) {
            html += `<tr>
                <td class="text-mono">${this.esc(c.clp_claim_id)}</td>
                <td>${c.clp_status_code} - ${this.esc(c.status_description || '')}</td>
                <td>${this.esc(c.patient_name)}</td>
                <td class="text-right">$${this.fmt(c.clp_total_charge)}</td>
                <td class="text-right">$${this.fmt(c.clp_total_payment)}</td>
            </tr>`;
        }
        html += '</tbody></table></div>';
        return html;
    },

    renderChangedTable(changes) {
        let html = '<div class="table-wrapper"><table><thead><tr>';
        html += '<th>Claim ID</th><th>Field</th><th>Old Value</th><th>New Value</th>';
        html += '</tr></thead><tbody>';
        for (const ch of changes) {
            for (let i = 0; i < ch.diffs.length; i++) {
                const d = ch.diffs[i];
                html += `<tr>
                    <td class="text-mono">${i === 0 ? this.esc(ch.claim_id) : ''}</td>
                    <td>${this.esc(d.field)}</td>
                    <td class="amount-negative">${this.formatVal(d.old)}</td>
                    <td class="amount-positive">${this.formatVal(d.new)}</td>
                </tr>`;
            }
        }
        html += '</tbody></table></div>';
        return html;
    },

    formatVal(v) {
        if (v === null || v === undefined) return 'N/A';
        if (typeof v === 'number') return '$' + this.fmt(v);
        return this.esc(String(v));
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
