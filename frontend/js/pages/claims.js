/* Claims list page — sortable, filterable table with pagination, batch actions, saved filters, workflow */
const ClaimsPage = {
    state: {
        fileId: null,
        status: null,
        workflowStatus: null,
        search: '',
        sortBy: 'id',
        sortDir: 'asc',
        page: 1,
        pageSize: 25,
        selectedClaims: new Set(),
        savedFilters: [],
    },

    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading claims...</div>';

        // Load files and saved filters in parallel
        let files = [];
        try {
            const [filesData, filtersData] = await Promise.all([
                API.listFiles(),
                API.listSavedFilters(),
            ]);
            files = filesData.files || [];
            this.state.savedFilters = filtersData.filters || [];
        } catch (_) {}

        let html = '<h2 style="margin-bottom: 16px;">Claims</h2>';

        // Saved filters pills
        if (this.state.savedFilters.length > 0) {
            html += '<div class="saved-filters-bar">';
            html += '<span class="saved-filters-label">Saved Views:</span>';
            for (const sf of this.state.savedFilters) {
                html += `<span class="saved-filter-pill" data-filter-id="${sf.id}">
                    ${this.esc(sf.name)}
                    <button class="saved-filter-delete" data-delete-filter="${sf.id}">&times;</button>
                </span>`;
            }
            html += '</div>';
        }

        // Filters
        html += `<div class="filter-bar">
            <label>File:</label>
            <select id="filter-file">
                <option value="">All Files</option>
                ${files.map(f => `<option value="${f.id}">${this.esc(f.filename)}</option>`).join('')}
            </select>
            <label>Status:</label>
            <select id="filter-status">
                <option value="">All</option>
                <option value="1">1 - Primary</option>
                <option value="2">2 - Secondary</option>
                <option value="4">4 - Denied</option>
                <option value="22">22 - Reversal</option>
            </select>
            <label>Workflow:</label>
            <select id="filter-workflow">
                <option value="">All</option>
                <option value="new">New</option>
                <option value="in-review">In Review</option>
                <option value="needs-appeal">Needs Appeal</option>
                <option value="appeal-sent">Appeal Sent</option>
                <option value="follow-up">Follow Up</option>
                <option value="resolved">Resolved</option>
                <option value="written-off">Written Off</option>
            </select>
            <input type="search" id="filter-search" placeholder="Search patient, claim #..." style="flex:1; min-width: 200px;">
            <button class="btn btn-outline btn-sm" id="save-view-btn">Save View</button>
            <button class="btn btn-outline" id="export-btn">Export CSV</button>
        </div>`;

        html += '<div class="card"><div id="claims-table-container"><div class="loading-spinner">Loading...</div></div></div>';

        // Batch action bar (hidden by default)
        html += `<div class="batch-bar hidden" id="batch-bar">
            <span class="batch-bar-count"><span id="batch-count">0</span> selected</span>
            <button class="btn btn-primary btn-sm" id="batch-flag-btn">Flag Selected</button>
            <button class="btn btn-outline btn-sm" id="batch-export-btn">Export Selected</button>
            <button class="btn btn-outline btn-sm" id="batch-resolve-btn">Resolve Flags</button>
            <button class="btn btn-outline btn-sm" id="batch-clear-btn">Clear Selection</button>
        </div>`;

        content.innerHTML = html;

        this.bindFilterEvents();
        this.bindBatchEvents();
        this.bindSavedFilterEvents();
        await this.loadClaims();
    },

    bindFilterEvents() {
        const self = this;

        document.getElementById('filter-file').addEventListener('change', function() {
            self.state.fileId = this.value || null;
            self.state.page = 1;
            self.loadClaims();
        });

        document.getElementById('filter-status').addEventListener('change', function() {
            self.state.status = this.value || null;
            self.state.page = 1;
            self.loadClaims();
        });

        document.getElementById('filter-workflow').addEventListener('change', function() {
            self.state.workflowStatus = this.value || null;
            self.state.page = 1;
            self.loadClaims();
        });

        let searchTimer;
        document.getElementById('filter-search').addEventListener('input', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                self.state.search = this.value;
                self.state.page = 1;
                self.loadClaims();
            }, 300);
        });

        document.getElementById('export-btn').addEventListener('click', async () => {
            try {
                const blob = await API.exportClaims(this.state.fileId);
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'claims_export.csv';
                a.click();
                URL.revokeObjectURL(url);
                Toast.success('CSV exported');
            } catch (err) {
                Toast.error(err.message);
            }
        });

        document.getElementById('save-view-btn').addEventListener('click', () => {
            this.showSaveViewModal();
        });

        // Set current filter values if they exist in state
        if (this.state.fileId) document.getElementById('filter-file').value = this.state.fileId;
        if (this.state.status) document.getElementById('filter-status').value = this.state.status;
        if (this.state.workflowStatus) document.getElementById('filter-workflow').value = this.state.workflowStatus;
        if (this.state.search) document.getElementById('filter-search').value = this.state.search;
    },

    bindBatchEvents() {
        document.getElementById('batch-flag-btn').addEventListener('click', () => {
            this.showBatchFlagModal();
        });

        document.getElementById('batch-export-btn').addEventListener('click', async () => {
            try {
                const ids = Array.from(this.state.selectedClaims);
                const blob = await API.batchExportCsv(ids);
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'selected_claims.csv';
                a.click();
                URL.revokeObjectURL(url);
                Toast.success(`Exported ${ids.length} claims`);
            } catch (err) {
                Toast.error(err.message);
            }
        });

        document.getElementById('batch-resolve-btn').addEventListener('click', async () => {
            try {
                const ids = Array.from(this.state.selectedClaims);
                const result = await API.batchResolveFlags(ids);
                Toast.success(result.message);
                this.clearSelection();
                this.loadClaims();
            } catch (err) {
                Toast.error(err.message);
            }
        });

        document.getElementById('batch-clear-btn').addEventListener('click', () => {
            this.clearSelection();
        });
    },

    bindSavedFilterEvents() {
        document.querySelectorAll('.saved-filter-pill[data-filter-id]').forEach(pill => {
            pill.addEventListener('click', (e) => {
                if (e.target.classList.contains('saved-filter-delete')) return;
                const id = parseInt(pill.dataset.filterId);
                const sf = this.state.savedFilters.find(f => f.id === id);
                if (sf) this.applySavedFilter(sf);
            });
        });

        document.querySelectorAll('[data-delete-filter]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                try {
                    await API.deleteSavedFilter(btn.dataset.deleteFilter);
                    Toast.success('View deleted');
                    this.render();
                } catch (err) {
                    Toast.error(err.message);
                }
            });
        });
    },

    applySavedFilter(sf) {
        try {
            const f = JSON.parse(sf.filters);
            this.state.fileId = f.fileId || null;
            this.state.status = f.status || null;
            this.state.workflowStatus = f.workflowStatus || null;
            this.state.search = f.search || '';
            this.state.sortBy = f.sortBy || 'id';
            this.state.sortDir = f.sortDir || 'asc';
            this.state.page = 1;

            // Update UI
            document.getElementById('filter-file').value = this.state.fileId || '';
            document.getElementById('filter-status').value = this.state.status || '';
            document.getElementById('filter-workflow').value = this.state.workflowStatus || '';
            document.getElementById('filter-search').value = this.state.search;

            this.loadClaims();
            Toast.info(`Applied view: ${sf.name}`);
        } catch (_) {
            Toast.error('Invalid saved filter');
        }
    },

    showSaveViewModal() {
        const overlay = document.getElementById('modal-overlay');
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">Save Current View</div>
                <div class="modal-body">
                    <label style="font-size: 0.85rem; display: block; margin-bottom: 4px;">View Name:</label>
                    <input type="text" id="view-name-input" placeholder="e.g. Denied claims this month"
                        style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary);">
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" id="view-cancel-btn">Cancel</button>
                    <button class="btn btn-primary" id="view-save-btn">Save</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');

        document.getElementById('view-cancel-btn').addEventListener('click', () => overlay.classList.add('hidden'));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.classList.add('hidden'); });

        document.getElementById('view-save-btn').addEventListener('click', async () => {
            const name = document.getElementById('view-name-input').value.trim();
            if (!name) return Toast.error('Please enter a name');
            try {
                await API.createSavedFilter(name, {
                    fileId: this.state.fileId,
                    status: this.state.status,
                    workflowStatus: this.state.workflowStatus,
                    search: this.state.search,
                    sortBy: this.state.sortBy,
                    sortDir: this.state.sortDir,
                });
                overlay.classList.add('hidden');
                Toast.success('View saved');
                this.render();
            } catch (err) {
                Toast.error(err.message);
            }
        });
    },

    showBatchFlagModal() {
        const overlay = document.getElementById('modal-overlay');
        const count = this.state.selectedClaims.size;
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">Flag ${count} Claims</div>
                <div class="modal-body">
                    <div style="margin-bottom: 12px;">
                        <label style="font-size: 0.85rem; display: block; margin-bottom: 4px;">Flag Type:</label>
                        <select id="batch-flag-type" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary);">
                            <option value="review">Review</option>
                            <option value="underpaid">Underpaid</option>
                            <option value="denied">Denied</option>
                            <option value="appeal">Appeal</option>
                            <option value="follow-up">Follow Up</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.85rem; display: block; margin-bottom: 4px;">Note:</label>
                        <textarea id="batch-flag-note" rows="3" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); color: var(--text-primary); font-family: var(--font); resize: vertical;"></textarea>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" id="batch-flag-cancel">Cancel</button>
                    <button class="btn btn-primary" id="batch-flag-save">Flag ${count} Claims</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');

        document.getElementById('batch-flag-cancel').addEventListener('click', () => overlay.classList.add('hidden'));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.classList.add('hidden'); });

        document.getElementById('batch-flag-save').addEventListener('click', async () => {
            const flagType = document.getElementById('batch-flag-type').value;
            const note = document.getElementById('batch-flag-note').value;
            try {
                const ids = Array.from(this.state.selectedClaims);
                const result = await API.batchFlag(ids, flagType, note);
                overlay.classList.add('hidden');
                Toast.success(result.message);
                this.clearSelection();
                this.loadClaims();
            } catch (err) {
                Toast.error(err.message);
            }
        });
    },

    updateBatchBar() {
        const bar = document.getElementById('batch-bar');
        const count = this.state.selectedClaims.size;
        if (count > 0) {
            bar.classList.remove('hidden');
            document.getElementById('batch-count').textContent = count;
        } else {
            bar.classList.add('hidden');
        }
    },

    clearSelection() {
        this.state.selectedClaims.clear();
        document.querySelectorAll('.claim-checkbox').forEach(cb => cb.checked = false);
        const selectAll = document.getElementById('select-all-checkbox');
        if (selectAll) selectAll.checked = false;
        this.updateBatchBar();
    },

    async loadClaims() {
        const container = document.getElementById('claims-table-container');
        if (!container) return;

        try {
            const data = await API.listClaims({
                file_id: this.state.fileId,
                status: this.state.status,
                workflow_status: this.state.workflowStatus,
                search: this.state.search,
                sort_by: this.state.sortBy,
                sort_dir: this.state.sortDir,
                page: this.state.page,
                page_size: this.state.pageSize,
            });

            // Build table manually to include checkbox column
            let tableHtml = '<div class="table-wrapper"><table><thead><tr>';
            tableHtml += '<th style="width: 36px;"><input type="checkbox" id="select-all-checkbox"></th>';

            const columns = [
                { key: 'clp_claim_id', label: 'Claim ID', sortable: true, sortKey: 'claim_id' },
                { key: 'clp_status_code', label: 'Status', sortable: true, sortKey: 'status' },
                { key: 'workflow_status', label: 'Workflow', sortable: true, sortKey: 'workflow' },
                { key: 'patient_name', label: 'Patient', sortable: true, sortKey: 'patient' },
                { key: 'rendering_provider_name', label: 'Provider', sortable: true, sortKey: 'provider' },
                { key: 'clp_total_charge', label: 'Charges', sortable: true, sortKey: 'charge', align: 'right' },
                { key: 'clp_total_payment', label: 'Payment', sortable: true, sortKey: 'payment', align: 'right' },
                { key: 'claim_date_start', label: 'Date', sortable: true, sortKey: 'date' },
                { key: 'service_line_count', label: 'Lines', align: 'right' },
            ];

            for (const col of columns) {
                const sortClass = col.sortable ? 'sortable' : '';
                const alignClass = col.align === 'right' ? 'text-right' : '';
                let activeSort = '';
                if (col.sortable && this.state.sortBy === col.sortKey) {
                    activeSort = this.state.sortDir === 'asc' ? 'sort-asc' : 'sort-desc';
                }
                tableHtml += `<th class="${sortClass} ${alignClass} ${activeSort}" data-sort-key="${col.sortKey || ''}">${col.label}<span class="sort-indicator"></span></th>`;
            }
            tableHtml += '</tr></thead><tbody>';

            if (data.claims.length === 0) {
                tableHtml += `<tr><td colspan="${columns.length + 1}" style="text-align: center; color: var(--text-muted); padding: 24px;">No claims found</td></tr>`;
            }

            for (const r of data.claims) {
                const checked = this.state.selectedClaims.has(r.id) ? 'checked' : '';
                tableHtml += `<tr class="clickable" data-id="${r.id}">`;
                tableHtml += `<td><input type="checkbox" class="claim-checkbox" data-claim-id="${r.id}" ${checked}></td>`;
                tableHtml += `<td>${this.esc(r.clp_claim_id)}</td>`;
                tableHtml += `<td>${this.statusBadge(r.clp_status_code)} <small>${r.status_description || ''}</small></td>`;
                tableHtml += `<td>${this.workflowBadge(r.workflow_status)}</td>`;
                tableHtml += `<td>${this.esc(r.patient_name)}</td>`;
                tableHtml += `<td>${this.esc(r.rendering_provider_name)}</td>`;
                tableHtml += `<td class="text-right">$${this.fmt(r.clp_total_charge)}</td>`;
                tableHtml += `<td class="text-right"><span class="${r.clp_total_payment > 0 ? 'amount-positive' : 'amount-zero'}">$${this.fmt(r.clp_total_payment)}</span></td>`;
                tableHtml += `<td>${this.formatDate(r.claim_date_start)}</td>`;
                tableHtml += `<td class="text-right">${r.service_line_count}</td>`;
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table></div>';

            let paginationHtml = '';
            if (data.total_pages > 1) {
                paginationHtml = `<div class="pagination">
                    <button id="page-prev" ${data.page <= 1 ? 'disabled' : ''}>Prev</button>
                    <span class="page-info">Page ${data.page} of ${data.total_pages} (${data.total} claims)</span>
                    <button id="page-next" ${data.page >= data.total_pages ? 'disabled' : ''}>Next</button>
                </div>`;
            }

            container.innerHTML = tableHtml + paginationHtml;

            // Bind sort headers
            container.querySelectorAll('th.sortable').forEach(th => {
                th.addEventListener('click', () => {
                    const sortKey = th.dataset.sortKey;
                    if (this.state.sortBy === sortKey) {
                        this.state.sortDir = this.state.sortDir === 'asc' ? 'desc' : 'asc';
                    } else {
                        this.state.sortBy = sortKey;
                        this.state.sortDir = 'asc';
                    }
                    this.loadClaims();
                });
            });

            // Bind row clicks (but not on checkboxes)
            container.querySelectorAll('tr.clickable').forEach(row => {
                row.addEventListener('click', (e) => {
                    if (e.target.type === 'checkbox') return;
                    window.location.hash = `#/claims/${row.dataset.id}`;
                });
            });

            // Bind checkboxes
            container.querySelectorAll('.claim-checkbox').forEach(cb => {
                cb.addEventListener('change', () => {
                    const id = parseInt(cb.dataset.claimId);
                    if (cb.checked) {
                        this.state.selectedClaims.add(id);
                    } else {
                        this.state.selectedClaims.delete(id);
                    }
                    this.updateBatchBar();
                });
            });

            // Select all checkbox
            const selectAll = document.getElementById('select-all-checkbox');
            if (selectAll) {
                selectAll.addEventListener('change', () => {
                    container.querySelectorAll('.claim-checkbox').forEach(cb => {
                        cb.checked = selectAll.checked;
                        const id = parseInt(cb.dataset.claimId);
                        if (selectAll.checked) {
                            this.state.selectedClaims.add(id);
                        } else {
                            this.state.selectedClaims.delete(id);
                        }
                    });
                    this.updateBatchBar();
                });
            }

            // Bind pagination
            const prevBtn = document.getElementById('page-prev');
            const nextBtn = document.getElementById('page-next');
            if (prevBtn) prevBtn.addEventListener('click', () => { this.state.page--; this.loadClaims(); });
            if (nextBtn) nextBtn.addEventListener('click', () => { this.state.page++; this.loadClaims(); });

            // Update batch bar state
            this.updateBatchBar();

        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    workflowBadge(status) {
        const s = status || 'new';
        const classes = {
            'new': 'badge-primary',
            'in-review': 'badge-info',
            'needs-appeal': 'badge-warning',
            'appeal-sent': 'badge-warning',
            'follow-up': 'badge-info',
            'resolved': 'badge-success',
            'written-off': 'badge-danger',
        };
        return `<span class="badge ${classes[s] || 'badge-primary'}">${s}</span>`;
    },

    statusBadge(code) {
        const classes = { '1': 'badge-success', '2': 'badge-info', '3': 'badge-info', '4': 'badge-danger', '22': 'badge-warning' };
        return `<span class="badge ${classes[code] || 'badge-primary'}">${code}</span>`;
    },

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },

    fmt(val) {
        return (Number(val) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    formatDate(d) {
        if (!d || d.length < 8) return d || '';
        return `${d.substring(0,4)}-${d.substring(4,6)}-${d.substring(6,8)}`;
    },
};
