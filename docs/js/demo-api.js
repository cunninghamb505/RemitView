/* Demo API — replaces server calls with client-side data operations */
const API = {
    async request(url, options = {}) {
        // For blob responses (export), return a mock
        return { ok: true, blob: () => Promise.resolve(new Blob(['Demo mode'])), json: () => Promise.resolve({}) };
    },

    async getJSON(url) {
        const [path, qs] = url.split('?');
        const params = new URLSearchParams(qs || '');

        if (path === '/api/info') {
            return { name: 'RemitView', version: '2.1.0', author: 'Brandon Cunningham', demo: true };
        }

        if (path === '/api/files') {
            return { files: DEMO_DATA.files };
        }

        if (path === '/api/settings') {
            return { underpayment_threshold: '70' };
        }

        if (path === '/api/dashboard') {
            const fileId = params.get('file_id');
            let claims = DEMO_DATA.claims;
            let files = DEMO_DATA.files;
            if (fileId) {
                const fid = parseInt(fileId);
                claims = claims.filter(c => c.file_id === fid);
                files = files.filter(f => f.id === fid);
            }
            const totalPayment = claims.reduce((s, c) => s + (c.clp_total_payment || 0), 0);
            const totalCharge = claims.reduce((s, c) => s + (c.clp_total_charge || 0), 0);
            const totalAdj = claims.reduce((s, c) => s + (c.total_adjustments || 0), 0);
            const denied = claims.filter(c => c.clp_status_code === '4').length;
            const statusCounts = {};
            claims.forEach(c => { statusCounts[c.clp_status_code] = (statusCounts[c.clp_status_code] || 0) + 1; });
            return {
                total_files: files.length, total_claims: claims.length,
                total_payment: totalPayment, total_charges: totalCharge,
                total_adjustments: totalAdj, denied_claims: denied,
                status_breakdown: Object.entries(statusCounts).map(([code, count]) => ({ status_code: code, count })),
                files: files.map(f => ({ id: f.id, filename: f.filename })),
            };
        }

        if (path === '/api/claims') {
            let claims = [...DEMO_DATA.claims];
            const fileId = params.get('file_id');
            const status = params.get('status');
            const search = params.get('search');
            if (fileId) claims = claims.filter(c => c.file_id === parseInt(fileId));
            if (status) claims = claims.filter(c => c.clp_status_code === status);
            if (search) {
                const q = search.toLowerCase();
                claims = claims.filter(c =>
                    (c.clp_claim_id || '').toLowerCase().includes(q) ||
                    (c.patient_name || '').toLowerCase().includes(q) ||
                    (c.rendering_provider_name || '').toLowerCase().includes(q)
                );
            }
            // Add payer_name from file
            claims = claims.map(c => {
                const f = DEMO_DATA.files.find(f => f.id === c.file_id);
                return { ...c, payer_name: f ? f.payer_name : '', filename: f ? f.filename : '' };
            });
            return { claims, total: claims.length };
        }

        const claimMatch = path.match(/^\/api\/claims\/(\d+)$/);
        if (claimMatch) {
            const id = parseInt(claimMatch[1]);
            const claim = DEMO_DATA.claims.find(c => c.id === id);
            if (!claim) return { error: 'Not found' };
            const file = DEMO_DATA.files.find(f => f.id === claim.file_id);
            const svcLines = DEMO_DATA.service_lines.filter(s => s.claim_id === id);
            const claimAdjs = DEMO_DATA.claim_adjustments.filter(a => a.claim_id === id);
            const svcsWithAdjs = svcLines.map(s => ({
                ...s,
                adjustments: DEMO_DATA.service_adjustments.filter(a => a.service_line_id === s.id),
            }));
            return {
                ...claim,
                payer_name: file ? file.payer_name : '',
                filename: file ? file.filename : '',
                service_lines: svcsWithAdjs,
                adjustments: claimAdjs,
                flags: [],
            };
        }

        if (path === '/api/codes/carc') {
            const search = (params.get('search') || '').toLowerCase();
            let codes = Object.entries(DEMO_CODES.carc).map(([code, desc]) => ({ code, description: desc }));
            if (search) codes = codes.filter(c => c.code.toLowerCase().includes(search) || c.description.toLowerCase().includes(search));
            return { codes: codes.slice(0, 50) };
        }

        if (path === '/api/codes/rarc') {
            const search = (params.get('search') || '').toLowerCase();
            let codes = Object.entries(DEMO_CODES.rarc).map(([code, desc]) => ({ code, description: desc }));
            if (search) codes = codes.filter(c => c.code.toLowerCase().includes(search) || c.description.toLowerCase().includes(search));
            return { codes: codes.slice(0, 50) };
        }

        if (path === '/api/analytics/denial-trends') {
            const groupBy = params.get('group_by') || 'reason';
            const claims = DEMO_DATA.claims;
            const denied = claims.filter(c => c.clp_status_code === '4');
            const data = {};
            denied.forEach(c => {
                const month = (c.claim_date_start || '').substring(0, 6);
                let key;
                if (groupBy === 'payer') {
                    const f = DEMO_DATA.files.find(f => f.id === c.file_id);
                    key = f ? f.payer_name : 'Unknown';
                } else if (groupBy === 'provider') {
                    key = c.rendering_provider_name || 'Unknown';
                } else {
                    const adjs = DEMO_DATA.claim_adjustments.filter(a => a.claim_id === c.id);
                    key = adjs.length > 0 ? adjs[0].reason_code : 'Unknown';
                }
                if (!data[key]) data[key] = {};
                data[key][month] = (data[key][month] || 0) + 1;
            });
            return { trends: data };
        }

        if (path === '/api/analytics/payer-comparison') {
            const payers = {};
            DEMO_DATA.claims.forEach(c => {
                const f = DEMO_DATA.files.find(f => f.id === c.file_id);
                const payer = f ? f.payer_name : 'Unknown';
                if (!payers[payer]) payers[payer] = { total_claims: 0, total_charge: 0, total_payment: 0, denied: 0 };
                payers[payer].total_claims++;
                payers[payer].total_charge += c.clp_total_charge || 0;
                payers[payer].total_payment += c.clp_total_payment || 0;
                if (c.clp_status_code === '4') payers[payer].denied++;
            });
            return {
                payers: Object.entries(payers).map(([name, stats]) => ({
                    payer_name: name, ...stats,
                    payment_rate: stats.total_charge > 0 ? ((stats.total_payment / stats.total_charge) * 100).toFixed(1) : 0,
                    denial_rate: stats.total_claims > 0 ? ((stats.denied / stats.total_claims) * 100).toFixed(1) : 0,
                })),
            };
        }

        if (path === '/api/analytics/adjustment-summary') {
            const groups = {};
            const reasons = {};
            [...DEMO_DATA.claim_adjustments, ...DEMO_DATA.service_adjustments].forEach(a => {
                const gc = a.group_code || 'Unknown';
                groups[gc] = (groups[gc] || 0) + Math.abs(a.amount || 0);
                const rc = a.reason_code || 'Unknown';
                if (!reasons[rc]) reasons[rc] = { count: 0, total: 0 };
                reasons[rc].count++;
                reasons[rc].total += Math.abs(a.amount || 0);
            });
            return {
                group_totals: Object.entries(groups).map(([code, total]) => ({
                    group_code: code, total, description: DEMO_CODES.group[code] || code,
                })),
                reason_details: Object.entries(reasons).map(([code, data]) => ({
                    reason_code: code, count: data.count, total: data.total,
                    description: DEMO_CODES.carc[code] || code,
                })).sort((a, b) => b.total - a.total).slice(0, 20),
            };
        }

        if (path === '/api/compare') {
            const f1 = parseInt(params.get('file1') || '0');
            const f2 = parseInt(params.get('file2') || '0');
            const claims1 = DEMO_DATA.claims.filter(c => c.file_id === f1);
            const claims2 = DEMO_DATA.claims.filter(c => c.file_id === f2);
            const ids1 = new Set(claims1.map(c => c.clp_claim_id));
            const ids2 = new Set(claims2.map(c => c.clp_claim_id));
            return {
                file1: DEMO_DATA.files.find(f => f.id === f1) || {},
                file2: DEMO_DATA.files.find(f => f.id === f2) || {},
                removed: claims1.filter(c => !ids2.has(c.clp_claim_id)),
                added: claims2.filter(c => !ids1.has(c.clp_claim_id)),
                changed: [],
            };
        }

        if (path === '/api/search') {
            const q = (params.get('q') || '').toLowerCase();
            if (q.length < 2) return { results: [] };
            const results = [];
            DEMO_DATA.claims.forEach(c => {
                if ((c.clp_claim_id || '').toLowerCase().includes(q) ||
                    (c.patient_name || '').toLowerCase().includes(q)) {
                    const f = DEMO_DATA.files.find(f => f.id === c.file_id);
                    results.push({ type: 'claim', id: c.id, title: c.clp_claim_id, subtitle: c.patient_name, payer: f ? f.payer_name : '' });
                }
            });
            DEMO_DATA.service_lines.forEach(s => {
                if ((s.procedure_code || '').toLowerCase().includes(q)) {
                    results.push({ type: 'procedure', id: s.claim_id, title: s.procedure_code, subtitle: `$${s.payment_amount}` });
                }
            });
            return { results: results.slice(0, 20) };
        }

        if (path === '/api/flags') return { flags: [] };

        if (path === '/api/developer/files') return { files: DEMO_DATA.files };

        const devRawMatch = path.match(/^\/api\/developer\/files\/(\d+)\/raw$/);
        if (devRawMatch) {
            const id = parseInt(devRawMatch[1]);
            const f = DEMO_DATA.files.find(f => f.id === id);
            return f ? { id: f.id, filename: f.filename, source_type: f.source_type, raw_content: f.raw_content, uploaded_at: f.uploaded_at } : {};
        }

        if (path === '/api/listeners/status') {
            return { ftp: { running: false }, email: { running: false }, webhook: { endpoint: '/api/ingest' } };
        }
        if (path === '/api/listeners/settings') return {};
        if (path === '/api/keys') return { keys: [] };

        return {};
    },

    async postJSON(url, body) {
        if (url.includes('/load-sample')) return { message: 'Samples already loaded in demo mode' };
        return { status: 'error', message: 'Not available in demo mode' };
    },

    async putJSON(url, body) {
        return { status: 'error', message: 'Not available in demo mode' };
    },

    async uploadFile(file) { throw new Error('Uploads disabled in demo mode'); },
    async loadSample() { return { message: 'Samples pre-loaded in demo' }; },
    async listFiles() { return this.getJSON('/api/files'); },
    async deleteFile(id) { throw new Error('Deleting disabled in demo mode'); },
    async getDashboard(fileId) { return this.getJSON(`/api/dashboard${fileId ? '?file_id=' + fileId : ''}`); },
    async listClaims(params = {}) {
        const qs = new URLSearchParams();
        for (const [k, v] of Object.entries(params)) { if (v !== null && v !== undefined && v !== '') qs.set(k, v); }
        return this.getJSON(`/api/claims?${qs}`);
    },
    async getClaim(id) { return this.getJSON(`/api/claims/${id}`); },
    async searchCodes(type, search) { return this.getJSON(`/api/codes/${type}${search ? '?search=' + encodeURIComponent(search) : ''}`); },
    async exportClaims(fileId) { throw new Error('CSV export not available in demo mode'); },
};
