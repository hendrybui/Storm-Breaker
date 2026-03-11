/**
 * Storm-Breaker Report Generator UI Module
 * Frontend for professional pentest report generation
 */

const ReportGeneratorUI = {
    reports: [],

    init() {
        this.loadReports();
        this.bindEvents();
    },

    async loadReports() {
        try {
            const resp = await $.get('/api/reports');
            this.reports = resp.reports || [];
            this.renderReportList();
        } catch (e) {
            console.error('Failed to load reports', e);
        }
    },

    renderReportList() {
        const container = $('#report-list');
        container.empty();
        if (this.reports.length === 0) {
            container.html('<div class="text-center text-gray-400 py-8"><i class="fas fa-file-alt text-4xl mb-3"></i><p>No reports generated yet</p></div>');
            return;
        }
        this.reports.forEach(r => {
            const stats = typeof r.stats === 'string' ? JSON.parse(r.stats) : (r.stats || {});
            const overallRisk = stats.overall_risk != null ? parseFloat(stats.overall_risk).toFixed(1) : '—';
            const maxCvss = stats.max_cvss != null ? parseFloat(stats.max_cvss).toFixed(1) : '—';
            const riskColor = overallRisk >= 9 ? 'red' : overallRisk >= 7 ? 'orange' : overallRisk >= 4 ? 'yellow' : 'green';
            const riskLabel = overallRisk >= 9 ? 'CRITICAL' : overallRisk >= 7 ? 'HIGH' : overallRisk >= 4 ? 'MEDIUM' : 'LOW';

            container.append(`
                <div class="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 bg-${riskColor}-600 rounded-lg flex items-center justify-center flex-col">
                                <span class="text-white font-bold text-sm">${overallRisk}</span>
                                <span class="text-white text-[8px] uppercase">${riskLabel}</span>
                            </div>
                            <div>
                                <div class="font-semibold text-white">${this.escapeHtml(r.name)}</div>
                                <div class="text-xs text-gray-400">
                                    ${r.generated_at || ''} • ${stats.findings || 0} findings • ${stats.total_evidence || 0} evidence items
                                    ${maxCvss !== '—' ? ` • Max CVSS: ${maxCvss}` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-1 text-xs rounded bg-red-900 text-red-300">${stats.critical || 0} Critical</span>
                            <span class="px-2 py-1 text-xs rounded bg-orange-900 text-orange-300">${stats.high || 0} High</span>
                            <span class="px-2 py-1 text-xs rounded bg-yellow-900 text-yellow-300">${stats.medium || 0} Medium</span>
                            <button onclick="ReportGeneratorUI.viewReport(${r.id})" class="px-3 py-1 bg-cyan-600 text-white rounded text-sm hover:bg-cyan-500"><i class="fas fa-eye mr-1"></i>View</button>
                            <button onclick="ReportGeneratorUI.downloadReport(${r.id})" class="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-500"><i class="fas fa-download mr-1"></i>HTML</button>
                            <button onclick="ReportGeneratorUI.deleteReport(${r.id})" class="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-500"><i class="fas fa-trash mr-1"></i></button>
                        </div>
                    </div>
                </div>
            `);
        });
    },

    bindEvents() {
        $('#btn-generate-report').on('click', () => this.generateReport());
    },

    async generateReport() {
        const config = {
            title: $('#report-title').val() || 'Storm-Breaker Penetration Test Report',
            organization: $('#report-org').val() || 'Security Assessment Team',
            target: $('#report-target').val() || 'Target Organization',
            author: $('#report-author').val() || 'Operator',
            classification: $('#report-classification').val() || 'CONFIDENTIAL',
        };

        $('#btn-generate-report').prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-2"></i>Generating...');

        try {
            const resp = await $.ajax({
                url: '/api/reports/generate',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(config),
            });

            const overallRisk = resp.stats.overall_risk != null ? parseFloat(resp.stats.overall_risk).toFixed(1) : '—';
            const riskColor = overallRisk >= 9 ? '#dc2626' : overallRisk >= 7 ? '#ea580c' : overallRisk >= 4 ? '#ca8a04' : '#16a34a';

            Swal.fire({
                title: 'Report Generated!',
                html: `
                    <div class="text-left" style="font-size:14px;">
                        <div style="text-align:center;margin-bottom:16px;">
                            <div style="display:inline-block;width:60px;height:60px;border-radius:50%;background:${riskColor};line-height:60px;text-align:center;">
                                <span style="color:#fff;font-size:20px;font-weight:bold;">${overallRisk}</span>
                            </div>
                            <div style="color:#94a3b8;font-size:11px;margin-top:4px;">Overall Risk Score</div>
                        </div>
                        <table style="width:100%;border-collapse:collapse;">
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Findings</td><td style="padding:4px 8px;font-weight:600;">${resp.stats.findings}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Critical</td><td style="padding:4px 8px;color:#f87171;font-weight:600;">${resp.stats.critical}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">High</td><td style="padding:4px 8px;color:#fb923c;font-weight:600;">${resp.stats.high}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Medium</td><td style="padding:4px 8px;color:#facc15;font-weight:600;">${resp.stats.medium || 0}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Evidence Items</td><td style="padding:4px 8px;">${resp.stats.total_evidence}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Timeline Events</td><td style="padding:4px 8px;">${resp.stats.timeline_events}</td></tr>
                            <tr><td style="padding:4px 8px;color:#94a3b8;">Max CVSS</td><td style="padding:4px 8px;font-weight:600;">${resp.stats.max_cvss || '—'}</td></tr>
                        </table>
                    </div>
                `,
                icon: 'success',
                confirmButtonText: 'View Report',
                showCancelButton: true,
                cancelButtonText: 'Close',
            }).then(result => {
                if (result.isConfirmed) {
                    window.open(`/api/reports/${resp.id}/view`, '_blank');
                }
            });

            this.loadReports();
        } catch (e) {
            Swal.fire('Error', 'Failed to generate report', 'error');
        } finally {
            $('#btn-generate-report').prop('disabled', false).html('<i class="fas fa-file-pdf mr-2"></i>Generate Report');
        }
    },

    viewReport(id) {
        window.open(`/api/reports/${id}/view`, '_blank');
    },

    async downloadReport(id) {
        try {
            const resp = await $.get(`/api/reports/${id}`);
            const blob = new Blob([resp.html_content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${id}_${new Date().toISOString().slice(0, 10)}.html`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            Swal.fire('Error', 'Failed to download report', 'error');
        }
    },

    async deleteReport(id) {
        const result = await Swal.fire({
            title: 'Delete Report?',
            text: 'This action cannot be undone',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            confirmButtonText: 'Delete',
        });
        if (result.isConfirmed) {
            await $.ajax({ url: `/api/reports/${id}`, method: 'DELETE' });
            this.loadReports();
            GrowlNotification.notify({ title: 'Deleted', description: 'Report removed', type: 'info', position: 'top-right', closeTimeout: 3000 });
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};
