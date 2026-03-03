/* Settings page — app configuration */
const SettingsPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading settings...</div>';

        try {
            const settings = await API.getJSON('/api/settings');

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

            document.getElementById('save-threshold-btn').addEventListener('click', async () => {
                const val = document.getElementById('threshold-input').value;
                try {
                    await API.putJSON('/api/settings', { key: 'underpayment_threshold', value: val });
                    Toast.success('Setting saved');
                } catch (err) {
                    Toast.error(err.message);
                }
            });
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },
};
