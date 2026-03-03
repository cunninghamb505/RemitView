/* API Keys page — demo version */
const ApiKeysPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">API Keys</h2>
            <p style="color: var(--text-secondary);">API key management is available in the full version. <a href="https://github.com/cunninghamb505/RemitView" target="_blank" style="color: var(--accent);">Get it on GitHub</a></p>
        `;
    },
};
