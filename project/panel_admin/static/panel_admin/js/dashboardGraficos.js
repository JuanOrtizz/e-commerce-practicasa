const leerDatos = (id) => {
    const elemento = document.getElementById(id);
    if (!elemento) return null;
    return JSON.parse(elemento.textContent);
};

const datos = {
    consultasPorMes: leerDatos('datos-consultas-mes') || [],
    consultasPorEstado: leerDatos('datos-consultas-estado') || { pendiente: 0, resuelta: 0 },
    categorias: leerDatos('datos-categorias') || [],
    tags: leerDatos('datos-tags') || [],
    enPromocion: leerDatos('datos-en-promocion') ?? 0,
    productosActivos: leerDatos('datos-productos-activos') ?? 0,
};

const COLORES = {
    terracota: '#A25630',
    verde: '#3D9B4F',
    amarillo: '#D9A021',
    gris: '#C4C4C4',
    grisClaro: '#E8E8E8',
    texto: '#ADADAD',
};

const COLORES_TAGS = {
    'Nuevo': '#198754',
    'Oferta': '#DC3545',
    'Destacado': '#0DCAF0',
    'Sin Stock': '#6C757D',
    'Última unidad': '#FFC107',
};

const crearSparkline = (canvas, serie, color) => {
    new Chart(canvas, {
        type: 'line',
        data: {
            labels: serie.map((punto) => punto[0]),
            datasets: [{
                data: serie.map((punto) => punto[1]),
                borderColor: color,
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 10,
                fill: false,
                tension: 0.4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: { x: { display: false }, y: { display: false } },
        },
    });
};

document.querySelectorAll('.sparkline-canvas').forEach((canvas) => {
    const serie = canvas.dataset.series;
    if (serie === 'consultas') crearSparkline(canvas, datos.consultasPorMes, COLORES.terracota);
});

const pluginTextoCentro = {
    id: 'textoCentro',
    afterDatasetsDraw(chart, _args, options) {
        if (!options || !options.activo) return;
        const { ctx } = chart;
        const { width, height } = chart.chartArea;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 26px Roboto, sans-serif';
        ctx.fillStyle = '#000000';
        ctx.fillText(String(options.total), width / 2, height / 2 - (options.etiqueta ? 8 : 0));
        if (options.etiqueta) {
            ctx.font = '12px Roboto, sans-serif';
            ctx.fillStyle = COLORES.texto;
            ctx.fillText(options.etiqueta, width / 2, height / 2 + 18);
        }
        ctx.restore();
    },
};

const totalConsultas = datos.consultasPorEstado.pendiente + datos.consultasPorEstado.resuelta;
const graficoConsultasEstado = document.getElementById('graficoConsultasEstado');
if (graficoConsultasEstado) {
    new Chart(graficoConsultasEstado, {
        type: 'doughnut',
        data: {
            labels: ['Pendientes', 'Resueltas'],
            datasets: [{
                data: [datos.consultasPorEstado.pendiente, datos.consultasPorEstado.resuelta],
                backgroundColor: [COLORES.amarillo, COLORES.verde],
                borderWidth: 0,
                hoverOffset: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        boxWidth: 8,
                        padding: 16,
                        font: { family: 'Roboto', size: 12 },
                    },
                },
                textoCentro: { activo: true, total: totalConsultas, etiqueta: 'consultas' },
            },
        },
        plugins: [pluginTextoCentro],
    });
}

const graficoCategorias = document.getElementById('graficoCategorias');
if (graficoCategorias) {
    new Chart(graficoCategorias, {
        type: 'bar',
        data: {
            labels: datos.categorias.map((categoria) => categoria[0]),
            datasets: [{
                data: datos.categorias.map((categoria) => categoria[1]),
                backgroundColor: 'rgba(162, 86, 48, 0.75)',
                hoverBackgroundColor: COLORES.terracota,
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 22,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
                y: { grid: { display: false } },
            },
        },
    });
}

const graficoTags = document.getElementById('graficoTags');
if (graficoTags) {
    new Chart(graficoTags, {
        type: 'bar',
        data: {
            labels: datos.tags.map((tag) => tag[0]),
            datasets: [{
                data: datos.tags.map((tag) => tag[1]),
                backgroundColor: datos.tags.map((tag) => COLORES_TAGS[tag[0]] || COLORES.gris),
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 30,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
                x: { grid: { display: false } },
            },
        },
    });
}

const graficoGauge = document.getElementById('graficoGauge');
if (graficoGauge) {
    const enPromocion = Math.max(0, datos.enPromocion);
    const sinPromocion = Math.max(0, datos.productosActivos - enPromocion);
    new Chart(graficoGauge, {
        type: 'doughnut',
        data: {
            labels: ['En promoción', 'Sin promoción'],
            datasets: [{
                data: [enPromocion, sinPromocion],
                backgroundColor: [COLORES.amarillo, COLORES.grisClaro],
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            plugins: {
                legend: { display: false },
                textoCentro: { activo: true, total: enPromocion, etiqueta: 'en promoción' },
            },
        },
        plugins: [pluginTextoCentro],
    });
}
