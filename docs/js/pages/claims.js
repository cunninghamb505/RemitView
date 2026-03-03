/* Claims list page — sortable, filterable table with pagination */
const ClaimsPage = {
    state: {
        fileId: null,
        status: null,
        search: '',
        sortBy: 'id',
        sortDir: 'asc',
        page: 1,
        pageSize: 25,
    },

    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = '<div class="loading-spinner">Loading claims...</div>';

        // Load files for filter dropdown
        let files = [];
        try {
            const filesData = await API.listFiles();
            files = filesData.files || [];
        } catch (_) {}

        let html = '<h2 style="margin-bottom: 16px;">Claims</h2>';

        // Filters
        html += `<div class="filter-bar">
            <label>File:</label>
            <select id="filter-file">
                <option value="">All Files</option>
                ${files.map(f => `<option value="${f.id}">${f.filename}</option>`).join('')}
            </select>
            <label>Status:</label>
            <select id="filter-status">
                <option value="">All</option>
                <option value="1">1 - Primary</option>
                <option value="2">2 - Secondary</option>
                <option value="4">4 - Denied</option>
                <option value="22">22 - Reversal</option>
            </select>
            <input type="search" id="filter-search" placeholder="Search patient, claim #..." style="flex:1; min-width: 200px;">
            <button class="btn btn-outline" id="export-btn">Export CSV</button>
        </div>`;

        html += '<div class="card"><div id="claims-table-container"><div class="loading-spinner">Loading...</div></div></div>';
        content.innerHTML = html;

        this.bindFilterEvents();
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
    },

    async loadClaims() {
        const container = document.getElementById('claims-table-container');
        if (!container) return;

        try {
            const data = await API.listClaims({
                file_id: this.state.fileId,
                status: this.state.status,
                search: this.state.search,
                sort_by: this.state.sortBy,
                sort_dir: this.state.sortDir,
                page: this.state.page,
                page_size: this.state.pageSize,
            });

            const columns = [
                { key: 'clp_claim_id', label: 'Claim ID', sortable: true, sortKey: 'claim_id' },
                { key: 'clp_status_code', label: 'Status', sortable: true, sortKey: 'status',
                  render: (r) => `${this.statusBadge(r.clp_status_code)} <small>${r.status_description || ''}</small>` },
                { key: 'patient_name', label: 'Patient', sortable: true, sortKey: 'patient' },
                { key: 'rendering_provider_name', label: 'Provider', sortable: true, sortKey: 'provider' },
                { key: 'clp_total_charge', label: 'Charges', sortable: true, sortKey: 'charge', align: 'right',
                  render: (r) => `$${this.fmt(r.clp_total_charge)}` },
                { key: 'clp_total_payment', label: 'Payment', sortable: true, sortKey: 'payment', align: 'right',
                  render: (r) => `<span class="${r.clp_total_payment > 0 ? 'amount-positive' : 'amount-zero'}">$${this.fmt(r.clp_total_payment)}</span>` },
                { key: 'claim_date_start', label: 'Date', sortable: true, sortKey: 'date',
                  render: (r) => this.formatDate(r.claim_date_start) },
                { key: 'service_line_count', label: 'Lines', align: 'right' },
            ];

            const tableHtml = Table.render(columns, data.claims, {
                onRowClick: true,
                sortBy: this.state.sortBy,
                sortDir: this.state.sortDir,
                emptyMessage: 'No claims found',
            });

            let paginationHtml = '';
            if (data.total_pages > 1) {
                paginationHtml = `<div class="pagination">
                    <button id="page-prev" ${data.page <= 1 ? 'disabled' : ''}>Prev</button>
                    <span class="page-info">Page ${data.page} of ${data.total_pages} (${data.total} claims)</span>
                    <button id="page-next" ${data.page >= data.total_pages ? 'disabled' : ''}>Next</button>
                </div>`;
            }

            container.innerHTML = tableHtml + paginationHtml;

            // Bind sort
            Table.bindEvents(container, columns, {
                onSort: (key) => {
                    // Map column keys to API sort keys
                    const col = columns.find(c => c.key === key);
                    const sortKey = col?.sortKey || key;
                    if (this.state.sortBy === sortKey) {
                        this.state.sortDir = this.state.sortDir === 'asc' ? 'desc' : 'asc';
                    } else {
                        this.state.sortBy = sortKey;
                        this.state.sortDir = 'asc';
                    }
                    this.loadClaims();
                },
                onRowClick: (id) => {
                    window.location.hash = `#/claims/${id}`;
                },
            });

            // Bind pagination
            const prevBtn = document.getElementById('page-prev');
            const nextBtn = document.getElementById('page-next');
            if (prevBtn) prevBtn.addEventListener('click', () => { this.state.page--; this.loadClaims(); });
            if (nextBtn) nextBtn.addEventListener('click', () => { this.state.page++; this.loadClaims(); });

        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    statusBadge(code) {
        const classes = { '1': 'badge-success', '2': 'badge-info', '3': 'badge-info', '4': 'badge-danger', '22': 'badge-warning' };
        return `<span class="badge ${classes[code] || 'badge-primary'}">${code}</span>`;
    },

    fmt(val) {
        return (Number(val) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    formatDate(d) {
        if (!d || d.length < 8) return d || '';
        return `${d.substring(0,4)}-${d.substring(4,6)}-${d.substring(6,8)}`;
    },
};
