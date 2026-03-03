/* Files page — upload, sample loading, file list with export options */
const FilesPage = {
    async render() {
        const content = document.getElementById('app-content');
        const isDemo = window._demoMode || false;
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">Files</h2>
            ${isDemo ? '' : `
            <div class="card" style="margin-bottom: 24px;">
                <div class="card-header">
                    <span class="card-title">Upload 835 File</span>
                    <button class="btn btn-primary" id="load-sample-btn">Load Sample</button>
                </div>
                <div class="upload-zone" id="upload-zone">
                    <div class="upload-zone-icon">&#128196;</div>
                    <div class="upload-zone-text">
                        <strong>Click to upload</strong> or drag and drop<br>
                        EDI X12 835 files (.835, .edi, .txt) or PDF remittances (.pdf)
                    </div>
                    <input type="file" id="file-input" hidden accept=".835,.edi,.txt,.x12,.pdf">
                </div>
            </div>`}
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Loaded Files</span>
                </div>
                <div id="file-list-container">
                    <div class="loading-spinner">Loading...</div>
                </div>
            </div>
        `;

        if (!isDemo) this.bindEvents();
        await this.loadFiles();
    },

    bindEvents() {
        const zone = document.getElementById('upload-zone');
        const input = document.getElementById('file-input');
        if (!zone || !input) return;

        zone.addEventListener('click', () => input.click());

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', async (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) await this.uploadFile(file);
        });

        input.addEventListener('change', async () => {
            if (input.files[0]) await this.uploadFile(input.files[0]);
            input.value = '';
        });

        document.getElementById('load-sample-btn').addEventListener('click', async () => {
            const btn = document.getElementById('load-sample-btn');
            btn.disabled = true;
            btn.textContent = 'Loading...';
            try {
                await API.loadSample();
                Toast.success('Sample file loaded');
                await this.loadFiles();
            } catch (err) {
                Toast.error(err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Load Sample';
            }
        });
    },

    async uploadFile(file) {
        try {
            Toast.info('Uploading...');
            await API.uploadFile(file);
            Toast.success(`${file.name} uploaded successfully`);
            await this.loadFiles();
        } catch (err) {
            Toast.error(err.message);
        }
    },

    async loadFiles() {
        const container = document.getElementById('file-list-container');
        try {
            const data = await API.listFiles();
            if (!data.files || data.files.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-text">No files loaded yet. Upload a file or load the sample.</div>
                    </div>
                `;
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
                                <span>${f.uploaded_at}</span>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-outline btn-sm" data-export-excel="${f.id}" title="Export Excel">Excel</button>
                            <button class="btn btn-outline btn-sm" data-export-pdf="${f.id}" title="Export PDF Report">PDF</button>
                            ${window._demoMode ? '' : `<button class="btn btn-danger btn-sm" data-delete-id="${f.id}">Delete</button>`}
                        </div>
                    </div>
                `;
            }
            html += '</div>';
            container.innerHTML = html;

            // Bind delete buttons
            container.querySelectorAll('[data-delete-id]').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.dataset.deleteId;
                    Modal.show(
                        'Delete File',
                        'This will permanently delete this file and all its claims. Continue?',
                        async () => {
                            try {
                                await API.deleteFile(id);
                                Toast.success('File deleted');
                                await this.loadFiles();
                            } catch (err) {
                                Toast.error(err.message);
                            }
                        }
                    );
                });
            });

            // Bind Excel export buttons
            container.querySelectorAll('[data-export-excel]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.dataset.exportExcel;
                    try {
                        const resp = await API.request(`/api/export/excel?file_id=${id}`);
                        const blob = await resp.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `remitview_export_${id}.xlsx`;
                        a.click();
                        URL.revokeObjectURL(url);
                        Toast.success('Excel exported');
                    } catch (err) {
                        Toast.error(err.message);
                    }
                });
            });

            // Bind PDF export buttons
            container.querySelectorAll('[data-export-pdf]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.dataset.exportPdf;
                    try {
                        const resp = await API.request(`/api/export/pdf/file/${id}`);
                        const blob = await resp.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `file_report_${id}.pdf`;
                        a.click();
                        URL.revokeObjectURL(url);
                        Toast.success('PDF exported');
                    } catch (err) {
                        Toast.error(err.message);
                    }
                });
            });
        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error loading files: ${err.message}</div></div>`;
        }
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
