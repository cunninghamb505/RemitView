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

    // Batch actions
    async batchFlag(claimIds, flagType, note) {
        return this.postJSON('/api/batch/flag', { claim_ids: claimIds, flag_type: flagType, note });
    },

    async batchExportCsv(claimIds) {
        const resp = await this.request('/api/batch/export-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ claim_ids: claimIds }),
        });
        return resp.blob();
    },

    async batchResolveFlags(claimIds) {
        return this.postJSON('/api/batch/resolve-flags', { claim_ids: claimIds });
    },

    // Notes
    async listNotes(claimId) {
        return this.getJSON(`/api/notes?claim_id=${claimId}`);
    },

    async createNote(claimId, content) {
        return this.postJSON('/api/notes', { claim_id: claimId, content });
    },

    async deleteNote(noteId) {
        const resp = await this.request(`/api/notes/${noteId}`, { method: 'DELETE' });
        return resp.json();
    },

    // Saved filters
    async listSavedFilters() {
        return this.getJSON('/api/saved-filters');
    },

    async createSavedFilter(name, filters) {
        return this.postJSON('/api/saved-filters', { name, filters: JSON.stringify(filters) });
    },

    async deleteSavedFilter(id) {
        const resp = await this.request(`/api/saved-filters/${id}`, { method: 'DELETE' });
        return resp.json();
    },

    // Workflow
    async updateWorkflow(claimId, status, note) {
        const resp = await this.request(`/api/claims/${claimId}/workflow`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, note }),
        });
        return resp.json();
    },

    async getWorkflowHistory(claimId) {
        return this.getJSON(`/api/claims/${claimId}/workflow-history`);
    },

    // Maintenance
    async getDbInfo() {
        return this.getJSON('/api/maintenance/db-info');
    },

    async downloadBackup() {
        const resp = await this.request('/api/maintenance/backup');
        return resp.blob();
    },

    async restoreBackup(file) {
        const form = new FormData();
        form.append('file', file);
        const resp = await this.request('/api/maintenance/restore', { method: 'POST', body: form });
        return resp.json();
    },

    async wipeData(confirm) {
        return this.postJSON('/api/maintenance/wipe', { confirm });
    },

    async factoryReset(confirm) {
        return this.postJSON('/api/maintenance/reset', { confirm });
    },
};
