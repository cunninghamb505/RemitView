/* Files page — demo version (read-only, no uploads) */
const FilesPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">Files</h2>
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Sample Files</span>
                </div>
                <div id="file-list-container">
                    <div class="loading-spinner">Loading...</div>
                </div>
            </div>
        `;
        await this.loadFiles();
    },

    async loadFiles() {
        const container = document.getElementById('file-list-container');
        try {
            const data = await API.listFiles();
            if (!data.files || data.files.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No files loaded.</div></div>';
                return;
            }
            let html = '<div class="file-list">';
            for (const f of data.files) {
                html += `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">${this.escapeHtml(f.filename)}</div>
                            <div class="file-meta">
                                <span>${f.claim_count} claim${f.claim_count !== 1 ? 's' : ''}</span>
                                ${f.bpr_amount ? `<span>$${Number(f.bpr_amount).toFixed(2)}</span>` : ''}
                                ${f.payer_name ? `<span>${this.escapeHtml(f.payer_name)}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }
            html += '</div>';
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
