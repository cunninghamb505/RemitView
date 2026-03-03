/* Listeners page — demo version (info only) */
const ListenersPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">Listeners & Integrations</h2>
            <p style="color: var(--text-secondary); margin-bottom: 16px;">
                In the full version, RemitView supports FTP, Email/IMAP, and Webhook listeners for auto-importing files.
                These features are not available in the demo.
            </p>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">FTP</div><div class="stat-label">Embedded FTP Server</div></div>
                <div class="stat-card"><div class="stat-value">Email</div><div class="stat-label">IMAP Inbox Poller</div></div>
                <div class="stat-card"><div class="stat-value">Webhook</div><div class="stat-label">HTTP POST Endpoint</div></div>
            </div>
            <p style="color: var(--text-secondary); margin-top: 16px;">
                <a href="https://github.com/cunninghamb505/RemitView" target="_blank" style="color: var(--accent);">Get the full version on GitHub</a>
            </p>
        `;
    },
};
