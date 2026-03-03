/* Code lookup page — CARC/RARC search */
const CodeLookupPage = {
    state: {
        type: 'carc',
        search: '',
    },

    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">Code Lookup</h2>
            <div class="card">
                <div class="code-toggle">
                    <button class="active" id="toggle-carc">CARC</button>
                    <button id="toggle-rarc">RARC</button>
                </div>
                <div style="margin-bottom: 16px;">
                    <input type="search" id="code-search" placeholder="Search by code or description..."
                           style="width: 100%; max-width: 500px;">
                </div>
                <div id="code-results"><div class="loading-spinner">Loading...</div></div>
            </div>
        `;

        this.bindEvents();
        await this.loadCodes();
    },

    bindEvents() {
        const self = this;

        document.getElementById('toggle-carc').addEventListener('click', function() {
            self.state.type = 'carc';
            this.classList.add('active');
            document.getElementById('toggle-rarc').classList.remove('active');
            self.loadCodes();
        });

        document.getElementById('toggle-rarc').addEventListener('click', function() {
            self.state.type = 'rarc';
            this.classList.add('active');
            document.getElementById('toggle-carc').classList.remove('active');
            self.loadCodes();
        });

        let searchTimer;
        document.getElementById('code-search').addEventListener('input', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                self.state.search = this.value;
                self.loadCodes();
            }, 300);
        });
    },

    async loadCodes() {
        const container = document.getElementById('code-results');
        try {
            const data = await API.searchCodes(this.state.type, this.state.search);

            if (!data.codes || data.codes.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No codes found</div></div>';
                return;
            }

            let html = `<div style="margin-bottom: 8px; font-size: 0.85rem; color: var(--text-secondary);">${data.total} code${data.total !== 1 ? 's' : ''} found</div>`;
            html += '<div class="table-wrapper"><table><thead><tr><th style="width: 80px;">Code</th><th>Description</th></tr></thead><tbody>';

            for (const c of data.codes) {
                html += `<tr>
                    <td class="text-mono" style="font-weight: 600;">${c.code}</td>
                    <td>${this.esc(c.description)}</td>
                </tr>`;
            }

            html += '</tbody></table></div>';
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
