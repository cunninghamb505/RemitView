/* Developer view — inspect and edit raw inbound file content */
const DeveloperPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading files...</div>';

        try {
            const data = await API.getJSON('/api/developer/files');
            const files = data.files || [];

            if (files.length === 0) {
                content.innerHTML = `
                    <h2 style="margin-bottom: 16px;">Developer View</h2>
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128736;</div>
                        <div class="empty-state-text">No files loaded yet</div>
                        <p style="color: var(--text-secondary);">Upload files or load samples from the <a href="#/files" style="color: var(--accent);">Files page</a>.</p>
                    </div>
                `;
                return;
            }

            content.innerHTML = `
                <h2 style="margin-bottom: 16px;">Developer View</h2>
                <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 16px;">
                    Inspect and edit raw inbound file content. Changes will re-parse the file and update all associated data.
                </p>
                <div class="file-list" id="dev-file-list">
                    ${files.map(f => `
                        <div class="file-item">
                            <div class="file-info">
                                <div class="file-name">${this.escapeHtml(f.filename)}</div>
                                <div class="file-meta">
                                    <span>ID: ${f.id}</span>
                                    <span>Source: ${f.source_type || 'edi'}</span>
                                    <span>Claims: ${f.claim_count}</span>
                                    <span>${f.uploaded_at || ''}</span>
                                    <span>${f.payer_name ? 'Payer: ' + f.payer_name : ''}</span>
                                </div>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary dev-view-btn" data-id="${f.id}">View Raw</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div id="dev-editor-area" style="margin-top: 24px;"></div>
            `;

            // Bind view buttons
            content.querySelectorAll('.dev-view-btn').forEach(btn => {
                btn.addEventListener('click', () => this.loadRawContent(parseInt(btn.dataset.id)));
            });
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    async loadRawContent(fileId) {
        const area = document.getElementById('dev-editor-area');
        area.innerHTML = '<div class="loading-spinner">Loading raw content...</div>';

        try {
            const data = await API.getJSON(`/api/developer/files/${fileId}/raw`);
            const raw = data.raw_content || '';
            const hasContent = raw.length > 0;

            area.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Raw Content &mdash; ${this.escapeHtml(data.filename)} (ID: ${fileId})</span>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline" id="dev-copy-btn">Copy</button>
                            <button class="btn btn-sm btn-outline" id="dev-download-btn">Download</button>
                            ${data.source_type !== 'pdf' ? `<button class="btn btn-sm btn-primary" id="dev-save-btn" ${!hasContent ? 'disabled' : ''}>Save & Re-parse</button>` : ''}
                        </div>
                    </div>
                    ${!hasContent && data.source_type !== 'pdf' ? `
                        <div style="background: var(--bg-tertiary); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 12px; font-size: 0.85rem; color: var(--text-secondary);">
                            No raw content stored for this file (it was imported before the developer view was added).
                            You can paste EDI content below and save to associate it with this file.
                        </div>
                    ` : ''}
                    ${data.source_type === 'pdf' ? `
                        <div style="background: var(--bg-tertiary); padding: 12px; border-radius: var(--radius-sm); font-size: 0.85rem; color: var(--text-secondary);">
                            PDF files cannot be edited as raw text. The parsed data is shown below.
                        </div>
                    ` : ''}
                    <div class="dev-editor-wrapper">
                        <div class="dev-editor-info">
                            <span id="dev-char-count">${raw.length.toLocaleString()} characters</span>
                            <span id="dev-segment-count">${this.countSegments(raw)} segments</span>
                        </div>
                        <textarea id="dev-raw-textarea" class="dev-textarea" spellcheck="false"
                            ${data.source_type === 'pdf' ? 'readonly' : ''}
                        >${this.escapeHtml(this.formatEdi(raw))}</textarea>
                    </div>
                </div>
            `;

            // Bind events
            document.getElementById('dev-copy-btn').addEventListener('click', () => {
                const text = document.getElementById('dev-raw-textarea').value;
                navigator.clipboard.writeText(text).then(() => Toast.success('Copied to clipboard'));
            });

            document.getElementById('dev-download-btn').addEventListener('click', () => {
                const text = document.getElementById('dev-raw-textarea').value;
                const blob = new Blob([text], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename || `file_${fileId}.edi`;
                a.click();
                URL.revokeObjectURL(url);
            });

            const saveBtn = document.getElementById('dev-save-btn');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => this.saveRawContent(fileId));
            }

            // Update counts on edit
            const textarea = document.getElementById('dev-raw-textarea');
            textarea.addEventListener('input', () => {
                const val = textarea.value;
                document.getElementById('dev-char-count').textContent = val.length.toLocaleString() + ' characters';
                document.getElementById('dev-segment-count').textContent = this.countSegments(val) + ' segments';
            });

            // Scroll into view
            area.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (err) {
            area.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    async saveRawContent(fileId) {
        const textarea = document.getElementById('dev-raw-textarea');
        const raw = this.unformatEdi(textarea.value);

        if (!raw.trim()) {
            Toast.error('Content cannot be empty');
            return;
        }

        const saveBtn = document.getElementById('dev-save-btn');
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const result = await API.putJSON(`/api/developer/files/${fileId}/raw`, {
                raw_content: raw,
            });
            Toast.success(result.message);
            // Refresh the page to show updated data
            setTimeout(() => this.render(), 500);
        } catch (err) {
            Toast.error(err.message);
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save & Re-parse';
        }
    },

    formatEdi(raw) {
        if (!raw) return '';
        // If it's already formatted with newlines, return as-is
        if (raw.includes('\n') && !raw.startsWith('ISA')) return raw;
        // Try to detect segment terminator and add newlines
        const terminator = raw.length > 105 ? raw[105] : '~';
        if (terminator && raw.includes(terminator)) {
            return raw.split(terminator).filter(s => s.trim()).join(terminator + '\n');
        }
        return raw;
    },

    unformatEdi(text) {
        // Remove newlines that were added for display
        return text.replace(/\n/g, '');
    },

    countSegments(raw) {
        if (!raw) return 0;
        const terminator = raw.length > 105 ? raw[105] : '~';
        return raw.split(terminator).filter(s => s.trim()).length;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};
