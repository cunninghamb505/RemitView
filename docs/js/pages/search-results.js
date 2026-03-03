/* Search results page */
const SearchResultsPage = {
    async render() {
        const content = document.getElementById('app-content');
        const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
        const query = params.get('q') || '';

        if (!query || query.length < 2) {
            content.innerHTML = `
                <h2 style="margin-bottom: 16px;">Search</h2>
                <div class="empty-state"><div class="empty-state-text">Enter at least 2 characters to search.</div></div>
            `;
            return;
        }

        content.innerHTML = '<div class="loading-spinner">Searching...</div>';

        try {
            const data = await API.getJSON(`/api/search?q=${encodeURIComponent(query)}`);
            const results = data.results || [];

            let html = `
                <h2 style="margin-bottom: 16px;">Search Results for "${this.esc(query)}"</h2>
                <p style="margin-bottom: 16px; color: var(--text-secondary);">${data.total} result${data.total !== 1 ? 's' : ''} found</p>
            `;

            if (results.length === 0) {
                html += '<div class="empty-state"><div class="empty-state-text">No results found.</div></div>';
            } else {
                html += '<div class="file-list">';
                for (const r of results) {
                    const badge = r.type === 'claim' ? 'badge-primary' : r.type === 'patient' ? 'badge-info' : 'badge-warning';
                    html += `
                        <a href="${r.link}" class="file-item" style="text-decoration: none; color: inherit; cursor: pointer;">
                            <div class="file-info">
                                <div class="file-name">
                                    <span class="badge ${badge}" style="margin-right: 8px;">${r.type}</span>
                                    ${this.esc(r.title)}
                                </div>
                                <div class="file-meta">
                                    <span>${this.esc(r.subtitle)}</span>
                                    <span>${this.esc(r.detail)}</span>
                                </div>
                            </div>
                        </a>
                    `;
                }
                html += '</div>';
            }

            content.innerHTML = html;
        } catch (err) {
            content.innerHTML = `<div class="empty-state"><div class="empty-state-text">Error: ${err.message}</div></div>`;
        }
    },

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
