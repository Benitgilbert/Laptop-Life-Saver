/**
 * Export Utilities — CSV & PDF generation
 */

/**
 * Export an array of objects as a CSV file.
 * @param {Object[]} data - Array of row objects
 * @param {string[]} columns - Column keys to include
 * @param {Object} headers - Map of key → display header
 * @param {string} filename - Output filename (without extension)
 */
export function exportCSV(data, columns, headers, filename = 'export') {
    const headerRow = columns.map(c => headers[c] || c).join(',')
    const rows = data.map(row =>
        columns.map(c => {
            const val = row[c]
            if (val == null) return ''
            const str = String(val)
            // Escape commas and quotes
            return str.includes(',') || str.includes('"')
                ? `"${str.replace(/"/g, '""')}"`
                : str
        }).join(',')
    )

    const csv = [headerRow, ...rows].join('\n')
    downloadBlob(csv, `${filename}.csv`, 'text/csv;charset=utf-8;')
}

/**
 * Export an array of objects as a simple styled PDF.
 * Uses browser print for clean PDF generation.
 * @param {Object[]} data - Array of row objects
 * @param {string[]} columns - Column keys to include
 * @param {Object} headers - Map of key → display header
 * @param {string} title - Report title
 */
export function exportPDF(data, columns, headers, title = 'Report') {
    const now = new Date().toLocaleString()

    const tableHeaders = columns.map(c =>
        `<th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e2e8f0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">${headers[c] || c}</th>`
    ).join('')

    const tableRows = data.map((row, i) =>
        `<tr style="background:${i % 2 === 0 ? '#fff' : '#f8fafc'}">
            ${columns.map(c => {
            const val = row[c]
            return `<td style="padding:8px 12px;font-size:12px;color:#334155;border-bottom:1px solid #f1f5f9">${val != null ? val : '—'}</td>`
        }).join('')}
        </tr>`
    ).join('')

    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>${title}</title>
    <style>
        @page { size: landscape; margin: 20mm; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1e293b; }
        .header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 3px solid #6366f1; }
        .title { font-size: 20px; font-weight: 700; color: #1e293b; }
        .subtitle { font-size: 11px; color: #94a3b8; }
        table { width: 100%; border-collapse: collapse; }
        .footer { margin-top: 24px; font-size: 10px; color: #94a3b8; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">${title}</div>
            <div class="subtitle">Laptop Life-Saver • Nyanza District</div>
        </div>
        <div class="subtitle">Generated: ${now}</div>
    </div>
    <table>
        <thead><tr>${tableHeaders}</tr></thead>
        <tbody>${tableRows}</tbody>
    </table>
    <div class="footer">
        ${data.length} records • Laptop Life-Saver Monitoring System
    </div>
</body>
</html>`

    const printWindow = window.open('', '_blank', 'width=1000,height=700')
    printWindow.document.write(html)
    printWindow.document.close()
    printWindow.focus()
    setTimeout(() => printWindow.print(), 500)
}

function downloadBlob(content, filename, type) {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
}
