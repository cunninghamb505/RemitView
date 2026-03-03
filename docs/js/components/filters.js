/* Filter bar component */
const Filters = {
    render(filters) {
        let html = '<div class="filter-bar">';
        for (const f of filters) {
            if (f.type === 'select') {
                html += `<label>${f.label}</label>
                    <select id="${f.id}">
                        ${f.options.map(o => `<option value="${o.value}" ${o.selected ? 'selected' : ''}>${o.label}</option>`).join('')}
                    </select>`;
            } else if (f.type === 'search') {
                html += `<input type="search" id="${f.id}" placeholder="${f.placeholder || 'Search...'}" value="${f.value || ''}">`;
            }
        }
        html += '</div>';
        return html;
    },

    bindEvents(container, onChange) {
        container.querySelectorAll('.filter-bar select, .filter-bar input').forEach(el => {
            const event = el.tagName === 'SELECT' ? 'change' : 'input';
            let debounceTimer;
            el.addEventListener(event, () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => onChange(), el.tagName === 'INPUT' ? 300 : 0);
            });
        });
    },
};
