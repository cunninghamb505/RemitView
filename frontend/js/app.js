/* Main application — hash router, theme persistence */
const App = {
    init() {
        this.initTheme();
        this.initRouter();
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

    async route() {
        const hash = window.location.hash || '#/files';
        const path = hash.replace('#', '');

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            const page = link.dataset.page;
            if (path.startsWith(`/${page}`)) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Route to page
        if (path === '/files') {
            await FilesPage.render();
        } else if (path === '/dashboard') {
            await DashboardPage.render();
        } else if (path.match(/^\/claims\/(\d+)$/)) {
            const id = path.match(/^\/claims\/(\d+)$/)[1];
            await ClaimDetailPage.render(id);
        } else if (path === '/claims') {
            await ClaimsPage.render();
        } else if (path === '/codes') {
            await CodeLookupPage.render();
        } else {
            window.location.hash = '#/files';
        }
    },
};

// Start the app
document.addEventListener('DOMContentLoaded', () => App.init());
