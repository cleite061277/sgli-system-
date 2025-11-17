/**
 * SGLI Dashboard - Main JavaScript
 */

class SGLIDashboard {
    constructor() {
        this.apiBase = '/api/relatorios/';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
    }

    setupEventListeners() {
        // Filtros de período
        document.querySelectorAll('[id^="periodo-"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.changePeriod(e.target.id.replace('periodo-', ''));
            });
        });

        // Auto refresh a cada 5 minutos
        setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    changePeriod(period) {
        // Atualizar botões ativos
        document.querySelectorAll('[id^="periodo-"]').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-primary');
        });
        document.getElementById(`periodo-${period}`).classList.remove('btn-outline-primary');
        document.getElementById(`periodo-${period}`).classList.add('btn-primary');

        // Calcular datas
        const now = new Date();
        let startDate;

        switch(period) {
            case 'mes':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                break;
            case 'trimestre':
                startDate = new Date(now.getFullYear(), now.getMonth() - 2, 1);
                break;
            case 'ano':
                startDate = new Date(now.getFullYear(), 0, 1);
                break;
        }

        this.currentPeriod = { startDate, endDate: now };
        this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            const [dashboard, evolucao, ranking] = await Promise.all([
                this.fetchData('dashboard'),
                this.fetchData('evolucao_mensal'),
                this.fetchData('ranking_imoveis')
            ]);

            this.updateMetrics(dashboard);
            this.updateCharts(dashboard, evolucao);
            this.updateTables(ranking);
            this.updateAlerts(dashboard.alertas);

        } catch (error) {
            console.error('Erro ao carregar dados do dashboard:', error);
            this.showError('Erro ao carregar dados. Tentando novamente...');
        }
    }

    async fetchData(endpoint) {
        const url = new URL(this.apiBase + endpoint + '/', window.location.origin);
        
        if (this.currentPeriod) {
            url.searchParams.append('data_inicio', this.formatDate(this.currentPeriod.startDate));
            url.searchParams.append('data_fim', this.formatDate(this.currentPeriod.endDate));
        }

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }

    updateMetrics(data) {
        // Atualizar cards de métricas
        this.updateElement('locacoes-ativas', data.ocupacao?.total_imoveis || 0);
        this.updateElement('arrecadacao-mes', data.financeiro_mes?.valor_recebido_mes_formatado || 'R$ 0,00');
        this.updateElement('taxa-ocupacao', `${(data.ocupacao?.taxa_ocupacao || 0).toFixed(1)}%`);
        
        // Calcular inadimplência se disponível
        const inadimplencia = data.financeiro_mes?.valor_cobrado_mes > 0 ? 
            ((data.financeiro_mes.valor_cobrado_mes - data.financeiro_mes.valor_recebido_mes) / 
             data.financeiro_mes.valor_cobrado_mes * 100) : 0;
        this.updateElement('taxa-inadimplencia', `${inadimplencia.toFixed(1)}%`);
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    showError(message) {
        const alertsContainer = document.getElementById('alertas-container');
        if (alertsContainer) {
            alertsContainer.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }

    updateAlerts(alertas) {
        const container = document.getElementById('alertas-container');
        if (!container || !alertas) return;

        const alertsHtml = alertas.map(alerta => `
            <div class="alert alert-${alerta.tipo} alert-dismissible fade show" role="alert">
                <strong>${alerta.titulo}:</strong> ${alerta.mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `).join('');

        container.innerHTML = alertsHtml;
    }

    updateCharts(dashboard, evolucao) {
        this.createEvolucaoChart(evolucao);
        this.createStatusChart(dashboard);
    }

    createEvolucaoChart(data) {
        const ctx = document.getElementById('grafico-evolucao');
        if (!ctx || !data) return;

        // Destruir gráfico existente
        if (window.evolucaoChart) {
            window.evolucaoChart.destroy();
        }

        window.evolucaoChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(item => item.mes_formatado),
                datasets: [{
                    label: 'Valor Cobrado',
                    data: data.map(item => item.valor_cobrado),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1
                }, {
                    label: 'Valor Recebido',
                    data: data.map(item => item.valor_pago),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            }
                        }
                    }
                }
            }
        });
    }

    createStatusChart(data) {
        const ctx = document.getElementById('grafico-status');
        if (!ctx) return;

        // Destruir gráfico existente
        if (window.statusChart) {
            window.statusChart.destroy();
        }

        const financeiro = data.financeiro_mes || {};
        
        window.statusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pagas', 'Pendentes', 'Vencidas'],
                datasets: [{
                    data: [
                        financeiro.comandas_pagas || 0,
                        financeiro.comandas_pendentes || 0,
                        financeiro.comandas_vencidas || 0
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    updateTables(ranking) {
        this.updateRankingTable(ranking);
        this.updateComandasVencendo();
    }

    updateRankingTable(data) {
        const tbody = document.getElementById('ranking-imoveis');
        if (!tbody || !data) return;

        const html = data.slice(0, 5).map(item => `
            <tr>
                <td>${item.codigo}</td>
                <td>${item.endereco}</td>
                <td>${item.total_arrecadado_formatado}</td>
            </tr>
        `).join('');

        tbody.innerHTML = html;
    }

    async updateComandasVencendo() {
        // Implementar carregamento de comandas vencendo
        const tbody = document.getElementById('comandas-vencendo');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <i class="fas fa-spinner fa-spin"></i> Carregando...
                </td>
            </tr>
        `;
    }
}

// Inicializar dashboard quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.sgli = new SGLIDashboard();
});
