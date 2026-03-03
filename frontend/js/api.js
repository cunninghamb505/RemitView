/* API fetch wrappers */
const API = {
    async request(url, options = {}) {
        try {
            const resp = await fetch(url, options);
            if (!resp.ok) {
                const data = await resp.json().catch(() => ({}));
                throw new Error(data.detail || `HTTP ${resp.status}`);
            }
            return resp;
        } catch (err) {
            if (err.message === 'Failed to fetch') {
                throw new Error('Cannot reach server');
            }
            throw err;
        }
    },

    async getJSON(url) {
        const resp = await this.request(url);
        return resp.json();
    },

    async postJSON(url, body) {
        const resp = await this.request(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        return resp.json();
    },

    async putJSON(url, body) {
        const resp = await this.request(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        return resp.json();
    },

    // Files
    async uploadFile(file) {
        const form = new FormData();
        form.append('file', file);
        const resp = await this.request('/api/files/upload', { method: 'POST', body: form });
        return resp.json();
    },

    async loadSample() {
        const resp = await this.request('/api/files/load-sample', { method: 'POST' });
        return resp.json();
    },

    async listFiles() {
        return this.getJSON('/api/files');
    },

    async deleteFile(id) {
        const resp = await this.request(`/api/files/${id}`, { method: 'DELETE' });
        return resp.json();
    },

    // Dashboard
    async getDashboard(fileId) {
        const params = fileId ? `?file_id=${fileId}` : '';
        return this.getJSON(`/api/dashboard${params}`);
    },

    // Claims
    async listClaims(params = {}) {
        const qs = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) {
            if (v !== null && v !== undefined && v !== '') qs.set(k, v);
        }
        return this.getJSON(`/api/claims?${qs}`);
    },

    async getClaim(id) {
        return this.getJSON(`/api/claims/${id}`);
    },

    // Codes
    async searchCodes(type, search) {
        const qs = search ? `?search=${encodeURIComponent(search)}` : '';
        return this.getJSON(`/api/codes/${type}${qs}`);
    },

    // Export
    async exportClaims(fileId) {
        const params = fileId ? `?file_id=${fileId}` : '';
        const resp = await this.request(`/api/export/claims${params}`);
        return resp.blob();
    },
};
