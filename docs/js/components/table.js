/* Reusable sortable table component */
const Table = {
    render(columns, rows, options = {}) {
        const { onRowClick, sortBy, sortDir, onSort, emptyMessage } = options;

        if (!rows || rows.length === 0) {
            return `<div class="empty-state">
                <div class="empty-state-text">${emptyMessage || 'No data to display'}</div>
            </div>`;
        }

        let html = '<div class="table-wrapper"><table><thead><tr>';

        for (const col of columns) {
            const isSorted = sortBy === col.key;
            const sortClass = col.sortable ? 'sortable' : '';
            const dirClass = isSorted ? `sort-${sortDir}` : '';
            const sortAttr = col.sortable ? `data-sort-key="${col.key}"` : '';
            html += `<th class="${sortClass} ${dirClass} ${col.align === 'right' ? 'text-right' : ''}" ${sortAttr}>
                ${col.label}${col.sortable ? '<span class="sort-indicator"></span>' : ''}
            </th>`;
        }

        html += '</tr></thead><tbody>';

        for (const row of rows) {
            const clickAttr = onRowClick ? `data-row-id="${row.id}" class="clickable"` : '';
            html += `<tr ${clickAttr}>`;
            for (const col of columns) {
                const value = col.render ? col.render(row) : (row[col.key] ?? '');
                const align = col.align === 'right' ? 'text-right' : '';
                html += `<td class="${align}">${value}</td>`;
            }
            html += '</tr>';
        }

        html += '</tbody></table></div>';
        return html;
    },

    bindEvents(container, columns, options = {}) {
        const { onRowClick, onSort } = options;

        if (onSort) {
            container.querySelectorAll('th[data-sort-key]').forEach(th => {
                th.addEventListener('click', () => {
                    onSort(th.dataset.sortKey);
                });
            });
        }

        if (onRowClick) {
            container.querySelectorAll('tr[data-row-id]').forEach(tr => {
                tr.addEventListener('click', () => {
                    onRowClick(tr.dataset.rowId);
                });
            });
        }
    },
};
