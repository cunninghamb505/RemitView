/* Chart.js wrapper with theme-aware colors */
const ChartHelper = {
    getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            text: isDark ? '#e9ecef' : '#212529',
            textSecondary: isDark ? '#adb5bd' : '#6c757d',
            grid: isDark ? '#495057' : '#dee2e6',
            bg: isDark ? '#212529' : '#ffffff',
            palette: [
                '#0d6efd', '#198754', '#dc3545', '#ffc107',
                '#0dcaf0', '#6f42c1', '#fd7e14', '#20c997',
                '#d63384', '#6ea8fe', '#75b798', '#ea868f',
            ],
        };
    },

    defaultOptions(title) {
        const colors = this.getThemeColors();
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: !!title,
                    text: title || '',
                    color: colors.text,
                    font: { size: 14, weight: '600' },
                },
                legend: {
                    labels: { color: colors.text, padding: 12, usePointStyle: true },
                },
                tooltip: {
                    backgroundColor: colors.bg,
                    titleColor: colors.text,
                    bodyColor: colors.textSecondary,
                    borderColor: colors.grid,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: (ctx) => {
                            const val = ctx.parsed.y ?? ctx.parsed;
                            if (typeof val === 'number') {
                                return ` ${ctx.dataset.label || ctx.label}: $${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                            }
                            return ` ${ctx.dataset.label || ctx.label}: ${val}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: colors.textSecondary },
                    grid: { color: colors.grid, drawBorder: false },
                },
                y: {
                    ticks: {
                        color: colors.textSecondary,
                        callback: (v) => '$' + v.toLocaleString(),
                    },
                    grid: { color: colors.grid, drawBorder: false },
                },
            },
        };
    },

    createLine(canvas, labels, datasets, title) {
        const colors = this.getThemeColors();
        return new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: datasets.map((ds, i) => ({
                    borderColor: colors.palette[i % colors.palette.length],
                    backgroundColor: colors.palette[i % colors.palette.length] + '33',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: datasets.length === 1,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    ...ds,
                })),
            },
            options: this.defaultOptions(title),
        });
    },

    createBar(canvas, labels, datasets, title) {
        const colors = this.getThemeColors();
        return new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: datasets.map((ds, i) => ({
                    backgroundColor: colors.palette[i % colors.palette.length] + 'cc',
                    borderColor: colors.palette[i % colors.palette.length],
                    borderWidth: 1,
                    borderRadius: 4,
                    ...ds,
                })),
            },
            options: this.defaultOptions(title),
        });
    },

    createDoughnut(canvas, labels, data, title) {
        const colors = this.getThemeColors();
        return new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: colors.palette.slice(0, data.length).map(c => c + 'cc'),
                    borderColor: colors.palette.slice(0, data.length),
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!title,
                        text: title || '',
                        color: colors.text,
                        font: { size: 14, weight: '600' },
                    },
                    legend: {
                        position: 'right',
                        labels: { color: colors.text, padding: 10, usePointStyle: true },
                    },
                    tooltip: {
                        backgroundColor: colors.bg,
                        titleColor: colors.text,
                        bodyColor: colors.textSecondary,
                        borderColor: colors.grid,
                        borderWidth: 1,
                        callbacks: {
                            label: (ctx) => {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: $${ctx.parsed.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    },

    destroy(chart) {
        if (chart && typeof chart.destroy === 'function') chart.destroy();
    },
};
