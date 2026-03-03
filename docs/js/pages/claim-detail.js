/* Claim detail page — full drilldown with service lines, adjustments, and flags */
const ClaimDetailPage = {
    async render(claimId) {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading claim...</div>';

        try {
            const [claim, flagsData, settings] = await Promise.all([
                API.getClaim(claimId),
                API.getJSON(`/api/flags?claim_id=${claimId}`),
                API.getJSON('/api/settings'),
            ]);

            const flags = flagsData.flags || [];
            const threshold = parseFloat(settings.underpayment_threshold || '70');
            const charges = claim.clp_total_charge || 0;
            const payment = claim.clp_total_payment || 0;
            const paymentRate = charges > 0 ? (payment / charges * 100) : 100;
            const isUnderpaid = charges > 0 && paymentRate < threshold;

            let html = `
                <a href="#/claims" class="back-link">&larr; Back to Claims</a>

                <div class="card" style="margin-bottom: 24px;">
                    <div class="card-header">
                        <span class="card-title">Claim ${this.esc(claim.clp_claim_id)}</span>
                        <div class="btn-group">
                            ${this.statusBadge(claim.clp_status_code)}
                            ${isUnderpaid ? '<span class="badge badge-warning">UNDERPAID</span>' : ''}
                            <button class="btn btn-outline btn-sm" id="flag-claim-btn">Flag</button>
                            <button class="btn btn-outline btn-sm" id="export-claim-btn">Export CSV</button>
                            <button class="btn btn-outline btn-sm" id="export-claim-pdf-btn">PDF</button>
                        </div>
                    </div>
                    <div class="detail-header">
                        ${this.field('Status', `${claim.clp_status_code} - ${claim.status_description}`)}
                        ${this.field('Total Charge', `$${this.fmt(claim.clp_total_charge)}`)}
                        ${this.field('Total Payment', `$${this.fmt(claim.clp_total_payment)}`)}
                        ${isUnderpaid ? this.field('Payment Rate', `${paymentRate.toFixed(1)}% (threshold: ${threshold}%)`) : ''}
                        ${this.field('Patient', claim.patient_name || 'N/A')}
                        ${this.field('Patient ID', claim.patient_id || 'N/A')}
                        ${this.field('Provider', claim.rendering_provider_name || 'N/A')}
                        ${this.field('Provider NPI', claim.rendering_provider_id || 'N/A')}
                        ${this.field('Plan Code', claim.clp_plan_code || 'N/A')}
                        ${this.field('DRG Code', claim.clp_drg_code || 'N/A')}
                        ${this.field('Date Start', this.formatDate(claim.claim_date_start))}
                        ${this.field('Date End', this.formatDate(claim.claim_date_end))}
                        ${this.field('Date Received', this.formatDate(claim.claim_received_date))}
                        ${this.field('File', claim.filename || '')}
                    </div>
                </div>
            `;

            // Flags section
            if (flags.length > 0) {
                html += `<div class="card" style="margin-bottom: 24px;">
                    <div class="section-title" style="margin-top: 0;">Flags (${flags.length})</div>
                    <div class="table-wrapper"><table><thead><tr>
                        <th>Type</th><th>Note</th><th>Created</th><th>Status</th><th>Actions</th>
                    </tr></thead><tbody>`;
                for (const f of flags) {
                    const resolved = !!f.resolved_at;
                    html += `<tr>
                        <td><span class="badge ${resolved ? 'badge-success' : 'badge-warning'}">${this.esc(f.flag_type)}</span></td>
                        <td>${this.esc(f.note)}</td>
                        <td>${f.created_at || ''}</td>
                        <td>${resolved ? 'Resolved' : 'Open'}</td>
                        <td>
                            ${!resolved ? `<button class="btn btn-sm btn-primary" data-resolve-flag="${f.id}">Resolve</button>` : ''}
                            <button class="btn btn-sm btn-danger" data-delete-flag="${f.id}">Delete</button>
                        </td>
                    </tr>`;
                }
                html += '</tbody></table></div></div>';
            }

            // Claim-level adjustments
            if (claim.adjustments && claim.adjustments.length > 0) {
                html += `
                    <div class="card" style="margin-bottom: 24px;">
                        <div class="section-title" style="margin-top: 0;">Claim Adjustments</div>
                        ${this.renderAdjustments(claim.adjustments)}
                    </div>
                `;
            }

            // Service lines
            html += `<div class="card" style="margin-bottom: 24px;">
                <div class="section-title" style="margin-top: 0;">Service Lines (${claim.service_lines?.length || 0})</div>`;

            if (claim.service_lines && claim.service_lines.length > 0) {
                html += `<div class="table-wrapper"><table>
                    <thead><tr>
                        <th>Procedure</th>
                        <th>Modifiers</th>
                        <th class="text-right">Charge</th>
                        <th class="text-right">Payment</th>
                        <th class="text-right">Units</th>
                        <th>Date</th>
                        <th>Control #</th>
                    </tr></thead><tbody>`;

                for (const svc of claim.service_lines) {
                    html += `<tr>
                        <td class="text-mono">${this.esc(svc.procedure_code)}</td>
                        <td class="text-mono">${this.esc(svc.procedure_modifiers)}</td>
                        <td class="text-right">$${this.fmt(svc.charge_amount)}</td>
                        <td class="text-right">$${this.fmt(svc.payment_amount)}</td>
                        <td class="text-right">${svc.units || ''}</td>
                        <td>${this.formatDate(svc.date_start)}</td>
                        <td class="text-mono">${this.esc(svc.control_number)}</td>
                    </tr>`;

                    if (svc.adjustments && svc.adjustments.length > 0) {
                        html += `<tr><td colspan="7" style="padding: 0 0 0 32px; background: var(--bg-primary);">
                            <div style="padding: 8px 0;">
                                <strong style="font-size: 0.8rem; color: var(--text-secondary);">Adjustments:</strong>
                                ${this.renderAdjustmentsInline(svc.adjustments)}
                            </div>
                        </td></tr>`;
                    }
                }

                html += '</tbody></table></div>';
            } else {
                html += '<div class="empty-state"><div class="empty-state-text">No service lines</div></div>';
            }

            html += '</div>';
            content.innerHTML = html;

            this.bindEvents(claimId, claim);

        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    bindEvents(claimId, claim) {
        // Flag button
        document.getElementById('flag-claim-btn').addEventListener('click', () => {
            this.showFlagModal(claimId);
        });

        // Export button
        document.getElementById('export-claim-btn').addEventListener('click', async () => {
            try {
                const blob = await API.exportClaims(claim.file_id);
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `claim_${claim.clp_claim_id}.csv`;
                a.click();
                URL.revokeObjectURL(url);
                Toast.success('CSV exported');
            } catch (err) {
                Toast.error(err.message);
            }
        });

        // PDF export button
        document.getElementById('export-claim-pdf-btn').addEventListener('click', async () => {
            try {
                const resp = await API.request(`/api/export/pdf/claim/${claimId}`);
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `claim_${claim.clp_claim_id}.pdf`;
                a.click();
                URL.revokeObjectURL(url);
                Toast.success('PDF exported');
            } catch (err) {
                Toast.error(err.message);
            }
        });

        // Resolve flag buttons
        document.querySelectorAll('[data-resolve-flag]').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await API.request(`/api/flags/${btn.dataset.resolveFlag}/resolve`, { method: 'PATCH' });
                    Toast.success('Flag resolved');
                    await this.render(claimId);
                } catch (err) { Toast.error(err.message); }
            });
        });

        // Delete flag buttons
        document.querySelectorAll('[data-delete-flag]').forEach(btn => {
            btn.addEventListener('click', async () => {
                try {
                    await API.request(`/api/flags/${btn.dataset.deleteFlag}`, { method: 'DELETE' });
                    Toast.success('Flag deleted');
                    await this.render(claimId);
                } catch (err) { Toast.error(err.message); }
            });
        });
    },

    showFlagModal(claimId) {
        const overlay = document.getElementById('modal-overlay');
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">Flag Claim</div>
                <div class="modal-body">
                    <div style="margin-bottom: 12px;">
                        <label style="font-size: 0.85rem; display: block; margin-bottom: 4px;">Flag Type:</label>
                        <select id="flag-type-select" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary);">
                            <option value="review">Review</option>
                            <option value="underpaid">Underpaid</option>
                            <option value="denied">Denied</option>
                            <option value="appeal">Appeal</option>
                            <option value="follow-up">Follow Up</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.85rem; display: block; margin-bottom: 4px;">Note:</label>
                        <textarea id="flag-note-input" rows="3" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary); font-family: var(--font); resize: vertical;"></textarea>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" id="flag-cancel-btn">Cancel</button>
                    <button class="btn btn-primary" id="flag-save-btn">Add Flag</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');

        document.getElementById('flag-cancel-btn').addEventListener('click', () => {
            overlay.classList.add('hidden');
        });

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.add('hidden');
        });

        document.getElementById('flag-save-btn').addEventListener('click', async () => {
            const flagType = document.getElementById('flag-type-select').value;
            const note = document.getElementById('flag-note-input').value;
            try {
                await API.postJSON('/api/flags', { claim_id: parseInt(claimId), flag_type: flagType, note });
                overlay.classList.add('hidden');
                Toast.success('Flag added');
                await this.render(claimId);
            } catch (err) {
                Toast.error(err.message);
            }
        });
    },

    renderAdjustments(adjustments) {
        let html = '<div class="table-wrapper"><table><thead><tr><th>Group</th><th>Reason</th><th>Description</th><th class="text-right">Amount</th><th class="text-right">Qty</th></tr></thead><tbody>';
        for (const a of adjustments) {
            html += `<tr>
                <td><span class="badge badge-info">${a.group_code}</span> ${this.esc(a.group_description)}</td>
                <td class="text-mono">${a.reason_code}</td>
                <td>${this.esc(a.reason_description)}</td>
                <td class="text-right">$${this.fmt(a.amount)}</td>
                <td class="text-right">${a.quantity || ''}</td>
            </tr>`;
        }
        html += '</tbody></table></div>';
        return html;
    },

    renderAdjustmentsInline(adjustments) {
        let html = '<table style="font-size: 0.8rem; margin-top: 4px;"><tbody>';
        for (const a of adjustments) {
            html += `<tr>
                <td style="padding: 2px 8px;"><span class="badge badge-info">${a.group_code}</span></td>
                <td style="padding: 2px 8px;" class="text-mono">${a.reason_code}</td>
                <td style="padding: 2px 8px;">${this.esc(a.reason_description)}</td>
                <td style="padding: 2px 8px;" class="text-right">$${this.fmt(a.amount)}</td>
            </tr>`;
        }
        html += '</tbody></table>';
        return html;
    },

    field(label, value) {
        return `<div class="detail-field">
            <span class="detail-label">${label}</span>
            <span class="detail-value">${this.esc(String(value || 'N/A'))}</span>
        </div>`;
    },

    statusBadge(code) {
        const classes = { '1': 'badge-success', '2': 'badge-info', '3': 'badge-info', '4': 'badge-danger', '22': 'badge-warning' };
        return `<span class="badge ${classes[code] || 'badge-primary'}">${code}</span>`;
    },

    fmt(val) {
        return (Number(val) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    formatDate(d) {
        if (!d || d.length < 8) return d || 'N/A';
        return `${d.substring(0,4)}-${d.substring(4,6)}-${d.substring(6,8)}`;
    },

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
