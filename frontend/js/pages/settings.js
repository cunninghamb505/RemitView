/* Settings page — app configuration and database management */
const SettingsPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading settings...</div>';

        try {
            const [settings, dbInfo] = await Promise.all([
                API.getJSON('/api/settings'),
                API.getDbInfo(),
            ]);

            const fileSizeMB = (dbInfo.file_size / (1024 * 1024)).toFixed(2);
            const tables = dbInfo.tables || {};

            content.innerHTML = `
                <h2 style="margin-bottom: 16px;">Settings</h2>

                <div class="card" style="margin-bottom: 24px;">
                    <div class="card-header">
                        <span class="card-title">Underpayment Detection</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <label style="font-size: 0.9rem;">Payment threshold (% of charges):</label>
                        <input type="number" id="threshold-input" min="0" max="100"
                            value="${settings.underpayment_threshold || 70}"
                            style="width: 80px; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary);">
                        <span style="color: var(--text-secondary); font-size: 0.85rem;">%</span>
                        <button class="btn btn-primary btn-sm" id="save-threshold-btn">Save</button>
                    </div>
                    <p style="margin-top: 8px; font-size: 0.85rem; color: var(--text-secondary);">
                        Claims where payment is below this percentage of charges will be flagged as potentially underpaid.
                    </p>
                </div>

                <div class="card" style="margin-bottom: 24px;">
                    <div class="card-header">
                        <span class="card-title">Database Management</span>
                    </div>
                    <div class="db-info">
                        <div class="db-info-row">
                            <span class="db-info-label">Database Size:</span>
                            <span class="db-info-value">${fileSizeMB} MB</span>
                        </div>
                        <div class="db-info-row">
                            <span class="db-info-label">Tables:</span>
                            <span class="db-info-value">${Object.keys(tables).length}</span>
                        </div>
                        ${Object.entries(tables).map(([name, count]) =>
                            `<div class="db-info-row">
                                <span class="db-info-label" style="padding-left: 16px;">${name}:</span>
                                <span class="db-info-value">${count.toLocaleString()} rows</span>
                            </div>`
                        ).join('')}
                    </div>

                    <div style="display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap;">
                        <button class="btn btn-primary btn-sm" id="backup-btn">Download Backup</button>
                        <label class="btn btn-outline btn-sm" style="cursor: pointer;">
                            Restore from Backup
                            <input type="file" id="restore-file-input" accept=".db" style="display: none;">
                        </label>
                    </div>

                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-color);">
                        <p style="font-size: 0.85rem; color: var(--danger); margin-bottom: 12px; font-weight: 600;">Danger Zone</p>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                            <button class="btn btn-danger btn-sm" id="wipe-btn">Wipe All Data</button>
                            <button class="btn btn-danger btn-sm" id="reset-btn">Factory Reset</button>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">About</span>
                    </div>
                    <div id="about-info" style="color: var(--text-secondary); font-size: 0.9rem;"></div>
                </div>
            `;

            // Load app info
            try {
                const info = await API.getJSON('/api/info');
                document.getElementById('about-info').innerHTML = `
                    <p><strong>${info.name}</strong> v${info.version}</p>
                    <p>By ${info.author}</p>
                    <p style="margin-top: 8px;">EDI X12 835 Remittance Analyzer — parse, view, and analyze healthcare remittance data.</p>
                `;
            } catch (_) {}

            this.bindEvents();
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    bindEvents() {
        // Save threshold
        document.getElementById('save-threshold-btn').addEventListener('click', async () => {
            const val = document.getElementById('threshold-input').value;
            try {
                await API.putJSON('/api/settings', { key: 'underpayment_threshold', value: val });
                Toast.success('Setting saved');
            } catch (err) {
                Toast.error(err.message);
            }
        });

        // Download backup
        document.getElementById('backup-btn').addEventListener('click', async () => {
            try {
                Toast.info('Preparing backup...');
                const blob = await API.downloadBackup();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const ts = new Date().toISOString().replace(/[:\-T]/g, '').substring(0, 15);
                a.download = `remitview_backup_${ts}.db`;
                a.click();
                URL.revokeObjectURL(url);
                Toast.success('Backup downloaded');
            } catch (err) {
                Toast.error(err.message);
            }
        });

        // Restore backup
        document.getElementById('restore-file-input').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            this.showConfirmModal(
                'Restore Database',
                `Are you sure you want to restore from <strong>${file.name}</strong>? This will replace all current data.`,
                null,
                async () => {
                    try {
                        Toast.info('Restoring...');
                        await API.restoreBackup(file);
                        Toast.success('Database restored successfully');
                        setTimeout(() => window.location.reload(), 1000);
                    } catch (err) {
                        Toast.error(err.message);
                    }
                }
            );
        });

        // Wipe
        document.getElementById('wipe-btn').addEventListener('click', () => {
            this.showConfirmModal(
                'Wipe All Data',
                'This will delete <strong>all files, claims, and related data</strong>. Settings and API keys will be preserved.<br><br>Type <strong>WIPE</strong> to confirm.',
                'WIPE',
                async (confirm) => {
                    try {
                        await API.wipeData(confirm);
                        Toast.success('All data wiped');
                        setTimeout(() => window.location.reload(), 1000);
                    } catch (err) {
                        Toast.error(err.message);
                    }
                }
            );
        });

        // Factory reset
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.showConfirmModal(
                'Factory Reset',
                'This will <strong>delete everything</strong> including settings and API keys, and restore the database to its initial state.<br><br>Type <strong>RESET</strong> to confirm.',
                'RESET',
                async (confirm) => {
                    try {
                        await API.factoryReset(confirm);
                        Toast.success('Factory reset complete');
                        setTimeout(() => window.location.reload(), 1000);
                    } catch (err) {
                        Toast.error(err.message);
                    }
                }
            );
        });
    },

    showConfirmModal(title, message, confirmText, onConfirm) {
        const overlay = document.getElementById('modal-overlay');
        const needsInput = !!confirmText;
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">${title}</div>
                <div class="modal-body">${message}</div>
                ${needsInput ? `<input type="text" id="confirm-input" placeholder="Type ${confirmText} to confirm"
                    style="width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary);">` : ''}
                <div class="modal-actions">
                    <button class="btn btn-outline" id="confirm-cancel">Cancel</button>
                    <button class="btn btn-danger" id="confirm-ok">Confirm</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');

        document.getElementById('confirm-cancel').addEventListener('click', () => overlay.classList.add('hidden'));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.classList.add('hidden'); });

        document.getElementById('confirm-ok').addEventListener('click', async () => {
            if (needsInput) {
                const val = document.getElementById('confirm-input').value.trim();
                if (val !== confirmText) {
                    return Toast.error(`Please type "${confirmText}" to confirm`);
                }
                overlay.classList.add('hidden');
                await onConfirm(val);
            } else {
                overlay.classList.add('hidden');
                await onConfirm();
            }
        });
    },
};
