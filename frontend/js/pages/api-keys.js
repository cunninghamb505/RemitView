/* API Keys management page */
const ApiKeysPage = {
    async render() {
        const content = document.getElementById('app-content');
        content.innerHTML = `
            <h2 style="margin-bottom: 16px;">API Keys</h2>

            <div class="card" style="margin-bottom: 24px;">
                <div class="card-header">
                    <span class="card-title">Create New Key</span>
                </div>
                <div class="input-group">
                    <input type="text" id="key-name-input" placeholder="Key name (e.g., 'My Integration')" style="flex: 1;">
                    <select id="key-perms-select">
                        <option value="read">Read Only</option>
                        <option value="read,write">Read & Write</option>
                    </select>
                    <button class="btn btn-primary" id="create-key-btn">Create Key</button>
                </div>
                <div id="key-created-banner" style="display: none; margin-top: 16px; padding: 12px; background: var(--accent-light); border: 1px solid var(--accent); border-radius: var(--radius-sm);">
                    <strong>API Key Created!</strong> Copy it now — it won't be shown again:<br>
                    <code id="new-key-value" style="font-size: 0.95rem; word-break: break-all;"></code>
                    <button class="btn btn-sm btn-outline" id="copy-key-btn" style="margin-left: 8px;">Copy</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Active Keys</span>
                </div>
                <div id="keys-table-container"><div class="loading-spinner">Loading...</div></div>
            </div>
        `;

        this.bindEvents();
        await this.loadKeys();
    },

    bindEvents() {
        document.getElementById('create-key-btn').addEventListener('click', async () => {
            const name = document.getElementById('key-name-input').value.trim();
            if (!name) {
                Toast.error('Enter a key name');
                return;
            }
            const perms = document.getElementById('key-perms-select').value;
            try {
                const data = await API.postJSON('/api/keys', { key_name: name, permissions: perms });
                document.getElementById('new-key-value').textContent = data.key;
                document.getElementById('key-created-banner').style.display = 'block';
                document.getElementById('key-name-input').value = '';
                Toast.success('API key created');
                await this.loadKeys();
            } catch (err) {
                Toast.error(err.message);
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.id === 'copy-key-btn') {
                const key = document.getElementById('new-key-value').textContent;
                navigator.clipboard.writeText(key).then(() => Toast.success('Key copied'));
            }
        });
    },

    async loadKeys() {
        const container = document.getElementById('keys-table-container');
        try {
            const data = await API.getJSON('/api/keys');
            const keys = data.keys || [];

            if (keys.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No API keys yet.</div></div>';
                return;
            }

            let html = '<div class="table-wrapper"><table><thead><tr>';
            html += '<th>Name</th><th>Permissions</th><th>Created</th><th>Last Used</th><th>Status</th><th>Actions</th>';
            html += '</tr></thead><tbody>';
            for (const k of keys) {
                html += `<tr>
                    <td>${this.esc(k.key_name)}</td>
                    <td>${this.esc(k.permissions)}</td>
                    <td>${k.created_at || ''}</td>
                    <td>${k.last_used_at || 'Never'}</td>
                    <td><span class="badge ${k.is_active ? 'badge-success' : 'badge-danger'}">${k.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>${k.is_active ? `<button class="btn btn-sm btn-danger" data-revoke-key="${k.id}">Revoke</button>` : ''}</td>
                </tr>`;
            }
            html += '</tbody></table></div>';
            container.innerHTML = html;

            container.querySelectorAll('[data-revoke-key]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    try {
                        await API.request(`/api/keys/${btn.dataset.revokeKey}`, { method: 'DELETE' });
                        Toast.success('Key revoked');
                        await this.loadKeys();
                    } catch (err) {
                        Toast.error(err.message);
                    }
                });
            });
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
