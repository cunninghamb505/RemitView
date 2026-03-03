/* Main application — hash router, theme, search, keyboard shortcuts (demo version) */
const App = {
    init() {
        window._demoMode = true;
        this.initTheme();
        this.initRouter();
        this.initSearch();
        this.initKeyboardShortcuts();
        this.loadVersionInfo();
        window.addEventListener('hashchange', () => this.route());
        this.route();
    },

    initTheme() {
        const saved = localStorage.getItem('edi-theme');
        if (saved === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        }

        document.getElementById('theme-toggle').addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            if (next === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
            localStorage.setItem('edi-theme', next);
        });
    },

    initRouter() {
        if (!window.location.hash) {
            window.location.hash = '#/files';
        }
    },

    initSearch() {
        const input = document.getElementById('global-search');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const q = input.value.trim();
                if (q.length >= 2) {
                    window.location.hash = `#/search?q=${encodeURIComponent(q)}`;
                }
            }
        });
    },

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            const tag = (e.target.tagName || '').toLowerCase();
            if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

            switch (e.key) {
                case '/':
                    e.preventDefault();
                    document.getElementById('global-search').focus();
                    break;
                case '?':
                    e.preventDefault();
                    this.showShortcutsHelp();
                    break;
                case '1': window.location.hash = '#/files'; break;
                case '2': window.location.hash = '#/dashboard'; break;
                case '3': window.location.hash = '#/claims'; break;
                case '4': window.location.hash = '#/analytics'; break;
                case '5': window.location.hash = '#/compare'; break;
                case '6': window.location.hash = '#/codes'; break;
                case '7': window.location.hash = '#/developer'; break;
                case '8': window.location.hash = '#/settings'; break;
                case 'Escape':
                    document.getElementById('global-search').blur();
                    const modal = document.getElementById('modal-overlay');
                    if (modal && !modal.classList.contains('hidden')) {
                        modal.classList.add('hidden');
                    }
                    break;
            }
        });
    },

    showShortcutsHelp() {
        const overlay = document.getElementById('modal-overlay');
        overlay.innerHTML = `
            <div class="modal" style="max-width: 500px;">
                <div class="modal-title">Keyboard Shortcuts</div>
                <div class="modal-body">
                    <table style="width: 100%; font-size: 0.9rem;">
                        <tbody>
                            <tr><td><kbd>/</kbd></td><td>Focus search</td></tr>
                            <tr><td><kbd>?</kbd></td><td>Show this help</td></tr>
                            <tr><td><kbd>1</kbd>-<kbd>8</kbd></td><td>Navigate to page</td></tr>
                            <tr><td><kbd>Esc</kbd></td><td>Close modal / blur search</td></tr>
                        </tbody>
                    </table>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="document.getElementById('modal-overlay').classList.add('hidden')">Close</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.add('hidden');
        }, { once: true });
    },

    async loadVersionInfo() {
        const info = await API.getJSON('/api/info');
        const el = document.getElementById('app-version-info');
        if (el) {
            el.textContent = `${info.name} v${info.version} — by ${info.author} (Demo)`;
        }
    },

    async route() {
        const hash = window.location.hash || '#/files';
        const path = hash.replace('#', '').split('?')[0];

        document.querySelectorAll('.nav-link').forEach(link => {
            const page = link.dataset.page;
            if (path.startsWith(`/${page}`)) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        if (path === '/files') {
            await FilesPage.render();
        } else if (path === '/dashboard') {
            await DashboardPage.render();
        } else if (path.match(/^\/claims\/(\d+)$/)) {
            const id = path.match(/^\/claims\/(\d+)$/)[1];
            await ClaimDetailPage.render(id);
        } else if (path === '/claims') {
            await ClaimsPage.render();
        } else if (path === '/analytics') {
            await AnalyticsPage.render();
        } else if (path === '/compare') {
            await FileComparePage.render();
        } else if (path === '/codes') {
            await CodeLookupPage.render();
        } else if (path === '/developer') {
            await DeveloperPage.render();
        } else if (path === '/settings') {
            await SettingsPage.render();
        } else if (path === '/api-keys') {
            await ApiKeysPage.render();
        } else if (path === '/search') {
            await SearchResultsPage.render();
        } else if (path === '/listeners') {
            await ListenersPage.render();
        } else {
            window.location.hash = '#/files';
        }
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());
