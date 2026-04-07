let orders = [];
const itemsPerPage = 20;
let currentPage = 1;
let totalPages = 1;
let totalCount = 0;

document.getElementById('dateFilterForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    sessionStorage.removeItem('currentFilter');
    
    // Mostrar spinner en el botón de filtro
    const filterBtn = document.querySelector('.filter-btn');
    const btnText = filterBtn.querySelector('.btn-text');
    const btnSpinner = filterBtn.querySelector('.btn-spinner');
    
    btnText.style.opacity = '0';
    btnSpinner.style.display = 'block';
    filterBtn.disabled = true;
    
    try {
        await fetchOrders(true);
    } finally {
        // Ocultar spinner del botón de filtro
        btnText.style.opacity = '1';
        btnSpinner.style.display = 'none';
        filterBtn.disabled = false;
    }
});

// Función para mostrar la barra de progreso principal
function showMainProgressBar() {
    const progressBar = document.getElementById('progressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const progressText = document.querySelector('.progress-text');
    
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 20) {
            progress += Math.random() * 5;
            progressText.textContent = 'Conectando con la base de datos...';
        } else if (progress < 50) {
            progress += Math.random() * 8;
            progressText.textContent = 'Procesando consulta...';
        } else if (progress < 80) {
            progress += Math.random() * 10;
            progressText.textContent = 'Organizando datos...';
        } else if (progress < 95) {
            progress += Math.random() * 5;
            progressText.textContent = 'Finalizando...';
        } else {
            progress = Math.min(progress + 1, 100);
            progressText.textContent = 'Completado!';
        }

        progressBar.style.width = progress + '%';
        progressPercentage.textContent = Math.round(progress) + '%';

        if (progress >= 100) {
            clearInterval(interval);
        }
    }, 100);

    return interval;
}

// Función para mostrar spinner en botón
function showButtonSpinner(buttonId) {
    const button = document.getElementById(buttonId);
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.btn-spinner, .pagination-spinner');
    
    console.log(`Mostrando spinner para botón: ${buttonId}`);
    console.log('Botón encontrado:', button);
    console.log('Texto encontrado:', btnText);
    console.log('Spinner encontrado:', spinner);
    
    if (btnText) {
        btnText.style.opacity = '0';
        btnText.style.visibility = 'hidden';
    }
    if (spinner) {
        spinner.style.display = 'block';
        spinner.classList.add('show');
    }
    button.disabled = true;
}

// Función para ocultar spinner en botón
function hideButtonSpinner(buttonId) {
    const button = document.getElementById(buttonId);
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.btn-spinner, .pagination-spinner');
    
    console.log(`Ocultando spinner para botón: ${buttonId}`);
    
    if (btnText) {
        btnText.style.opacity = '1';
        btnText.style.visibility = 'visible';
    }
    if (spinner) {
        spinner.style.display = 'none';
        spinner.classList.remove('show');
    }
    button.disabled = false;
}

async function fetchOrders(resetPage = true, isPagination = false) {

    let startDate = document.getElementById('startDate').value;
    let endDate = document.getElementById('endDate').value;
    // Si no hay fechas, asignar por defecto: hace 1 año y hoy
    const today = new Date();
    if (!endDate) {
        // Formato YYYY-MM-DD
        endDate = today.toISOString().slice(0, 10);
    }
    if (!startDate) {
        const lastYear = new Date(today);
        lastYear.setFullYear(today.getFullYear() - 1);
        startDate = lastYear.toISOString().slice(0, 10);
    }

    const guia = document.getElementById('guia').value;
    const cliente = document.getElementById('cliente').value;
    const transportadora = document.getElementById('transportadora').value;
    const pedido = document.getElementById('pedido').value;
    const vendedor = document.getElementById('vendedor').value;
    // Ya no es necesario el return porque siempre habrá valores

    if (resetPage) {
        currentPage = 1;
    }

    let progressInterval = null;
    
    // Solo mostrar barra de progreso principal si NO es paginación
    if (!isPagination) {
        document.getElementById('loadingPopup').style.display = 'flex';
        progressInterval = showMainProgressBar();
    }

    try {
        const response = await fetch(
            `/api/orders?start_date=${startDate}&end_date=${endDate}&guia=${guia}&cliente=${cliente}&transportadora=${transportadora}&pedido=${pedido}&vendedor=${vendedor}&page=${currentPage}&limit=${itemsPerPage}`
        );
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const data = await response.json();
        
        console.log("Datos recibidos:", data);
        console.log("Página actual:", currentPage);
        console.log("Total count:", data.total_count);
        
        orders = data.orders || [];
        totalCount = data.total_count || 0;
        totalPages = Math.ceil(totalCount / itemsPerPage);
        
        document.querySelector('.table-container').style.display = 'block';
        document.getElementById('initialMessage').style.display = 'none';
        
        renderTable();
        updatePaginationControls();
        
    } catch (error) {
        console.error('Error:', error);
        if (progressInterval) clearInterval(progressInterval);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Error al cargar los datos',
            confirmButtonColor: '#00a3b4'
        });
    } finally {
        // Solo cerrar la barra de progreso si NO es paginación
        if (!isPagination) {
            setTimeout(() => {
                if (progressInterval) clearInterval(progressInterval);
                document.getElementById('loadingPopup').style.display = 'none';
            }, 500);
        }
    }
}

async function fetchOrdersWithEstado(estado, resetPage = true, isPagination = false) {
    let startDate = document.getElementById('startDate').value;
    let endDate = document.getElementById('endDate').value;
    // Si no hay fechas, asignar por defecto: hace 1 año y hoy
    const today = new Date();
    if (!endDate) {
        endDate = today.toISOString().slice(0, 10);
    }
    if (!startDate) {
        const lastYear = new Date(today);
        lastYear.setFullYear(today.getFullYear() - 1);
        startDate = lastYear.toISOString().slice(0, 10);
    }
    const guia = document.getElementById('guia').value;
    const cliente = document.getElementById('cliente').value;
    const transportadora = document.getElementById('transportadora').value;
    const pedido = document.getElementById('pedido').value;
    const vendedor = document.getElementById('vendedor').value;

    // Ya no es necesario el return porque siempre habrá valores

    if (resetPage) {
        currentPage = 1;
    }

    let progressInterval = null;
    
    // Solo mostrar barra de progreso principal si NO es paginación
    if (!isPagination) {
        document.getElementById('loadingPopup').style.display = 'flex';
        progressInterval = showMainProgressBar();
    }

    try {
        const response = await fetch(
            `/api/orders?start_date=${startDate}&end_date=${endDate}&guia=${guia}&cliente=${cliente}&transportadora=${transportadora}&pedido=${pedido}&vendedor=${vendedor}&estado=${estado}&page=${currentPage}&limit=${itemsPerPage}`
        );
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const data = await response.json();
        
        orders = data.orders || [];
        totalCount = data.total_count || 0;
        totalPages = Math.ceil(totalCount / itemsPerPage);
        
        renderTable();
        updatePaginationControls();
        
        document.getElementById('pageInfo').textContent = `Página ${currentPage} de ${totalPages} (${totalCount} pedidos con estado ${estado})`;
        
    } catch (error) {
        console.error('Error:', error);
        if (progressInterval) clearInterval(progressInterval);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Error al cargar los datos',
            confirmButtonColor: '#00a3b4'
        });
    } finally {
        // Solo cerrar la barra de progreso si NO es paginación
        if (!isPagination) {
            setTimeout(() => {
                if (progressInterval) clearInterval(progressInterval);
                document.getElementById('loadingPopup').style.display = 'none';
            }, 500);
        }
    }
}

function updatePaginationControls() {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    // Actualizar estado de botones
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    
    // Actualizar información de página
    pageInfo.textContent = `Página ${currentPage}/${totalPages} (${totalCount})`;
    
    console.log(`Controles actualizados - Página: ${currentPage}/${totalPages}, Total: ${totalCount}`);
}

async function sortTableByEstado(estado) {
    let startDate = document.getElementById('startDate').value;
    let endDate = document.getElementById('endDate').value;
    // Si no hay fechas, asignar por defecto: hace 1 año y hoy
    const today = new Date();
    if (!endDate) {
        endDate = today.toISOString().slice(0, 10);
    }
    if (!startDate) {
        const lastYear = new Date(today);
        lastYear.setFullYear(today.getFullYear() - 1);
        startDate = lastYear.toISOString().slice(0, 10);
    }
    const guia = document.getElementById('guia').value;
    const cliente = document.getElementById('cliente').value;
    const transportadora = document.getElementById('transportadora').value;
    const pedido = document.getElementById('pedido').value;
    const vendedor = document.getElementById('vendedor').value;

    // Ya no es necesario el return porque siempre habrá valores

    currentPage = 1;
    
    // Mostrar barra de progreso principal (no es paginación)
    document.getElementById('loadingPopup').style.display = 'flex';
    const progressInterval = showMainProgressBar();

    try {
        const response = await fetch(
            `/api/orders?start_date=${startDate}&end_date=${endDate}&guia=${guia}&cliente=${cliente}&transportadora=${transportadora}&pedido=${pedido}&vendedor=${vendedor}&estado=${estado}&page=1&limit=${itemsPerPage}`
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al cargar los datos');
        }

        const data = await response.json();
        
        if (!data.orders || data.orders.length === 0) {
            clearInterval(progressInterval);
            Swal.fire({
                icon: 'info',
                title: 'Sin resultados',
                text: `No hay pedidos con el estado: ${estado}`,
                confirmButtonColor: '#00a3b4'
            });
            document.getElementById('loadingPopup').style.display = 'none';
            return;
        }

        orders = data.orders;
        totalCount = data.total_count;
        totalPages = Math.ceil(totalCount / itemsPerPage);
        
        renderTable();
        updatePaginationControls();
        
        document.getElementById('pageInfo').textContent = `Página ${currentPage} de ${totalPages} (${totalCount} pedidos con estado ${estado})`;

        // Almacenar el estado actual para usarlo en la paginación
        sessionStorage.setItem('currentFilter', JSON.stringify({
            tipo: 'estado',
            valor: estado
        }));

    } catch (error) {
        console.error('Error:', error);
        clearInterval(progressInterval);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Error al cargar los datos',
            confirmButtonColor: '#00a3b4'
        });
    } finally {
        setTimeout(() => {
            clearInterval(progressInterval);
            document.getElementById('loadingPopup').style.display = 'none';
            showEstadoFilter();
        }, 500);
    }
}

function renderTable() {
    const tableBody = document.getElementById('ordersTableBody');
    tableBody.innerHTML = '';

    if (!orders || orders.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align: center;">No hay datos para mostrar</td>';
        tableBody.appendChild(row);
        return;
    }

    orders.forEach(order => {
        const row = document.createElement('tr');
        
        let estadoClass = 'estado-default-row';
        const estado = (order.estado_documento || '').toLowerCase();
        if (estado.includes('facturado') || estado.includes('despachado')) {
            estadoClass = 'estado-ok-row';
        } else if (estado.includes('anulado')) {
            estadoClass = 'estado-anulado-row';
        } else if (estado.includes('aprobado')) {
            estadoClass = 'estado-aprobado-row';
        } else if (estado.includes('comprometido')) {
            estadoClass = 'estado-comprometido-row';
        } else if (estado.includes('cumplido')) {
            estadoClass = 'estado-cumplido-row';
        } else if (estado.includes('en elaboración')) {
            estadoClass = 'estado-elaboracion-row';
        } else if (estado.includes('retenido')) {
            estadoClass = 'estado-retenido-row';
        }

        row.className = estadoClass;

        row.innerHTML = `
            <td>
                <div class="pedido-circle ${estadoClass}" onclick='showTraceModal(${JSON.stringify(order).replace(/'/g, "&#39;")})'>
                    ${order.numero_pedido || 'No disponible'}
                </div>
            </td>
            <td>${order.estado_documento || 'No disponible'}</td>
            <td>${formatearFecha(order.fecha_registro_pedido)}</td>
            <td>${order.cliente || 'No disponible'}</td>
            <td>${order.numero_factura || 'No disponible'}</td>
            <td>${order.razon_social_vendedor || 'No disponible'}</td>
        `;

        tableBody.appendChild(row);
    });
}

// Event listeners para los botones de paginación
document.getElementById('prevPage').addEventListener('click', async () => {
    console.log('Botón anterior clickeado. Página actual:', currentPage);
    
    if (currentPage <= 1) {
        console.log('Ya estamos en la primera página');
        return;
    }
    
    // Mostrar spinner en el botón
    showButtonSpinner('prevPage');
    
    const currentFilter = JSON.parse(sessionStorage.getItem('currentFilter') || '{}');
    
    currentPage--;
    console.log('Cambiando a página:', currentPage);
    
    try {
        if (currentFilter.tipo === 'estado') {
            await fetchOrdersWithEstado(currentFilter.valor, false, true); // isPagination = true
        } else {
            await fetchOrders(false, true); // isPagination = true
        }
    } finally {
        hideButtonSpinner('prevPage');
    }
});

document.getElementById('nextPage').addEventListener('click', async () => {
    console.log('Botón siguiente clickeado. Página actual:', currentPage, 'de', totalPages);
    
    if (currentPage >= totalPages) {
        console.log('Ya estamos en la última página');
        return;
    }
    
    // Mostrar spinner en el botón
    showButtonSpinner('nextPage');
    
    const currentFilter = JSON.parse(sessionStorage.getItem('currentFilter') || '{}');
    
    currentPage++;
    console.log('Cambiando a página:', currentPage);
    
    try {
        if (currentFilter.tipo === 'estado') {
            await fetchOrdersWithEstado(currentFilter.valor, false, true); // isPagination = true
        } else {
            await fetchOrders(false, true); // isPagination = true
        }
    } finally {
        hideButtonSpinner('nextPage');
    }
});

function formatearFecha(fechaStr) {
    if (!fechaStr || fechaStr === 'No disponible') return 'No disponible';
    
    try {
        const fecha = new Date(fechaStr);
        if (isNaN(fecha.getTime())) return 'No disponible';
        
        fecha.setHours(fecha.getHours() + 5);
        
        return fecha.toLocaleString('es-CO', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'America/Bogota'
        });
    } catch (e) {
        return 'No disponible';
    }
}

function showEstadoFilter() {
    const filterDiv = document.getElementById('estadoFilter');
    const filterButton = document.querySelector('.filter-button i');
    const isVisible = filterDiv.classList.contains('show');
    
    if (isVisible) {
        filterDiv.classList.remove('show');
        filterButton.style.transform = 'rotate(0deg)';
    } else {
        filterDiv.classList.add('show');
        filterButton.style.transform = 'rotate(180deg)';
    }
}

document.addEventListener('click', function(event) {
    const filterDiv = document.getElementById('estadoFilter');
    const filterButton = document.querySelector('.filter-button');
    
    if (!filterButton.contains(event.target) && !filterDiv.contains(event.target)) {
        filterDiv.classList.remove('show');
        document.querySelector('.filter-button i').style.transform = 'rotate(0deg)';
    }
});

// LIMITE CALENDARIO
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = String(currentDate.getMonth() + 1).padStart(2, '0');
    const currentDay = String(currentDate.getDate()).padStart(2, '0');
    const currentDateFormatted = `${currentYear}-${currentMonth}-${currentDay}`;

    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(currentYear - 1);
    const oneYearAgoYear = oneYearAgo.getFullYear();
    const oneYearAgoMonth = String(oneYearAgo.getMonth() + 1).padStart(2, '0');
    const oneYearAgoDay = String(oneYearAgo.getDate()).padStart(2, '0');
    const oneYearAgoFormatted = `${oneYearAgoYear}-${oneYearAgoMonth}-${oneYearAgoDay}`;

    startDateInput.max = currentDateFormatted;
    endDateInput.max = currentDateFormatted;
    startDateInput.min = oneYearAgoFormatted;
    endDateInput.min = oneYearAgoFormatted;
});

$(function() {
    if ($.datepicker && $.datepicker.regional && $.datepicker.regional["es"]) {
        $.datepicker.setDefaults($.datepicker.regional["es"]);
    }

    const currentDate = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(currentDate.getFullYear() - 1);

    $("#startDate, #endDate").datepicker({
        dateFormat: "yy-mm-dd",
        changeMonth: true,
        changeYear: true,
        yearRange: `${oneYearAgo.getFullYear()}:${currentDate.getFullYear()}`,
        minDate: oneYearAgo,
        maxDate: currentDate,
        showButtonPanel: true
    });
});

// Función para mostrar el modal de trazabilidad
function showTraceModal(order) {
    const modal = document.getElementById('traceModal');
    const timeline = document.getElementById('pedidoTimeline');
    const modalPedidoNumero = document.getElementById('modalPedidoNumero');
    
    modalPedidoNumero.textContent = order.numero_pedido;
    timeline.innerHTML = '';
    
    document.getElementById('modalGuia').textContent = order.guia || 'No disponible';
    
    const transportadorOriginal = order.transportadora || 'Sin transportador';
    let transportadorContent = transportadorOriginal;
    if (transportadorOriginal === 'TCC') {
        transportadorContent = `<a href="https://www.tcc.com.co" target="_blank">${transportadorOriginal}</a>`;
    } else if (transportadorOriginal === 'TACMO SAS') {
        transportadorContent = `<a href="https://tacmosas.com/" target="_blank">${transportadorOriginal}</a>`;
    } else if (transportadorOriginal === 'IMD & CIA SAS' || transportadorOriginal === 'IMD Y CIA SAS') {
        transportadorContent = `<a href="https://www.imd.com.co" target="_blank">${transportadorOriginal}</a>`;
    }
    

    // Mostrar el contenido del pedido en el modal
    document.getElementById('modalTransportador').innerHTML = transportadorContent;
    document.getElementById('modalRuta').textContent = order.ruta || transportadorOriginal || 'Sin transportador';
    document.getElementById('modalFechaEntrega').textContent = order.fecha_entrega || 'No disponible';
    document.getElementById('modalEstadoTransportadora').textContent = order.estado_transportadora || 'No disponible';
    document.getElementById('modalDireccionDespacho').textContent = order.Direccion_Despacho || 'No disponible';
    document.getElementById('modalCiudad_Despacho').textContent = order.Ciudad_Despacho || 'No disponible';

    const estados = [
        {
            titulo: 'Registro del Pedido',
            fecha: order.fecha_registro_pedido,
            icono: 'fa-solid fa-file-signature',
            descripcion: 'Pedido registrado en el sistema',
            mensajePendiente: 'Pedido no registrado'
        },
        {
            titulo: 'Preparación',
            fecha: order.fecha_preparacion_pedido,
            icono: 'fas fa-box-open',
            descripcion: 'Pedido en preparación',
            mensajePendiente: 'Pendiente de preparación'
        },
        {
            titulo: 'Picking',
            fecha: order.fecha_picking || '',
            icono: 'fas fa-people-carry',
            descripcion: 'Proceso de picking completado',
            mensajePendiente: 'Pendiente de picking'
        },
        {
            titulo: 'Alistamiento',
            fecha: order.fecha_de_alistamiento,
            icono: 'fas fa-dolly',
            descripcion: 'Pedido alistado para despacho',
            mensajePendiente: 'Pendiente de alistamiento'
        },
        {
            titulo: 'Despacho',
            fecha: order.fecha_despacho,
            icono: 'fas fa-shipping-fast',
            descripcion: 'Pedido despachado al cliente',
            mensajePendiente: 'No se ha despachado'
        }
    ];

    let estadoActual = 0;
    for (let i = estados.length - 1; i >= 0; i--) {
        if (estados[i].fecha && estados[i].fecha !== 'No disponible') {
            estadoActual = i;
            break;
        }
    }

    estados.forEach((estado, index) => {
        let tieneFecha = false;
        let fecha = estado.mensajePendiente;
    
        if (estado.fecha && estado.fecha !== 'No disponible') {
            try {
                const fechaObj = new Date(estado.fecha);
                if (!isNaN(fechaObj.getTime())) {
                    fechaObj.setHours(fechaObj.getHours() + 5);
                    
                    tieneFecha = true;
                    fecha = fechaObj.toLocaleString('es-CO', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            } catch (e) {
                fecha = estado.mensajePendiente;
            }
        }
        
        const timelineItem = document.createElement('div');
        timelineItem.className = 'timeline-item';
        
        const isActive = index <= estadoActual;
        const estadoColor = tieneFecha ? (isActive ? '#00a3b4' : '#e0e0e0') : '#ff6b6b';
        
        timelineItem.innerHTML = `
            <div class="timeline-line"></div>
            <div class="timeline-icon ${tieneFecha ? (isActive ? 'active' : '') : 'pending'}" 
                 style="background-color: ${estadoColor}">
                <i class="${estado.icono}"></i>
            </div>
            <div class="timeline-content ${tieneFecha ? (isActive ? 'active' : '') : 'pending'}" 
                 style="border-left: 4px solid ${estadoColor}; ${!tieneFecha ? 'background-color: #ffe5e5;' : ''}">
                <div class="timeline-title">
                    <i class="${estado.icono}" style="margin-right: 8px; color: ${estadoColor}"></i>
                    ${estado.titulo}
                </div>
                <div class="timeline-date" style="color: ${tieneFecha ? (isActive ? '#00a3b4' : '#666') : '#ff6b6b'}">
                    ${fecha}
                </div>
                <div class="timeline-description">
                    ${tieneFecha ? estado.descripcion : 'Estado no registrado'}
                </div>
            </div>
        `;

        timeline.appendChild(timelineItem);
    });

    modal.style.display = 'block';

    const closeBtn = document.querySelector('.close-modal');
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

function showInfoMessage(icon) {
    const message = icon.nextElementSibling;
    const allMessages = document.querySelectorAll('.info-message');
    
    allMessages.forEach(msg => {
        if (msg !== message) {
            msg.classList.remove('show');
        }
    });
    
    message.classList.toggle('show');
    
    document.addEventListener('click', function closeMessage(e) {
        if (!icon.contains(e.target) && !message.contains(e.target)) {
            message.classList.remove('show');
            document.removeEventListener('click', closeMessage);
        }
    });
}