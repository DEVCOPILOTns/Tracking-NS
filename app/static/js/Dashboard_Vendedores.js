/**
 * Script mejorado para el dashboard de vendedores
 */
let orders = [];
const itemsPerPage = 10; 
let currentPage = 1;
let totalItems = 0;
let totalPages = 1;
let vendedorName = "";
let isLoading = false;

// ✨ NUEVAS VARIABLES PARA CACHE
let cachedResults = null;
let cacheTimestamp = null;
let lastFilters = null;
const CACHE_DURATION = 5 * 60 * 1000;

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    vendedorName = document.getElementById('vendedorName').value;
    
    // Configurar eventos
    document.getElementById('prevPage').addEventListener('click', goToPreviousPage);
    document.getElementById('nextPage').addEventListener('click', goToNextPage);
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
    
    // Cargar la primera página de datos DIRECTAMENTE
    fetchPageData(currentPage);
    
    // Añadir manejador para cerrar el filtro al hacer clic fuera
    document.addEventListener('click', closeFilterOnClickOutside);
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

function getCurrentFiltersKey() {
    const cliente = document.getElementById('clienteFilter').value;
    const pedido = document.getElementById('pedidoFilter').value;
    const factura = document.getElementById('facturaFilter').value;
    const estadoActual = sessionStorage.getItem('estadoFiltro') || '';
    
    return `${vendedorName}_${cliente}_${pedido}_${factura}_${estadoActual}`;
}

function hasFiltersChanged() {
    const currentFilters = getCurrentFiltersKey();
    const changed = lastFilters !== currentFilters;
    lastFilters = currentFilters;
    return changed;
}

function displayCachedPage(page) {
    console.log(`📋 Mostrando página ${page} desde CACHE`);
    
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = cachedResults.slice(startIndex, endIndex);

    // Simular respuesta del servidor
    updateUI({
        orders: pageData,
        totalPages: Math.ceil(cachedResults.length / itemsPerPage),
        currentPage: page,
        totalItems: cachedResults.length,
        total_count: cachedResults.length
    });
}

/**
 * Cierra el filtro de estado si se hace clic fuera
 */
function closeFilterOnClickOutside(event) {
    const filterDiv = document.getElementById('estadoFilter');
    const filterButton = document.querySelector('.filter-button');
    
    if (filterButton && filterDiv && !filterButton.contains(event.target) && !filterDiv.contains(event.target)) {
        filterDiv.classList.remove('show');
        const filterIcon = document.querySelector('.filter-button i');
        if (filterIcon) {
            filterIcon.style.transform = 'rotate(0deg)';
        }
    }
}

/**
 * Navega a la página anterior
 */
function goToPreviousPage() {
    if (currentPage > 1 && !isLoading) {
        showButtonSpinner('prevPage');
        fetchPageData(currentPage - 1, true); // isPagination = true
    }
}

/**
 * Navega a la página siguiente
 */
function goToNextPage() {
    if (currentPage < totalPages && !isLoading) {
        showButtonSpinner('nextPage');
        fetchPageData(currentPage + 1, true); // isPagination = true
    }
}

/**
 * Aplica los filtros indicados por el usuario
 */
function applyFilters() {
    if (isLoading) return;
    
    // Mostrar spinner en el botón
    showButtonSpinner('applyFilters');
    
    console.log('🔄 Aplicando filtros - invalidando cache');
    
    // 🗑️ INVALIDAR CACHE
    cachedResults = null;
    cacheTimestamp = null;
    lastFilters = null;
    
    // Restablecer filtro de estado al aplicar otros filtros
    sessionStorage.removeItem('estadoFiltro');
    
    // Cargar datos con filtros desde página 1
    fetchPageData(1, false, () => {
        hideButtonSpinner('applyFilters');
    });
}

/**
 * Limpia todos los filtros
 */
function clearFilters() {
    if (isLoading) return;
    showButtonSpinner('clearFilters');
    console.log('🧹 Limpiando filtros - invalidando cache');

    // Limpiar campos de filtro
    const clienteInput = document.getElementById('clienteFilter');
    if (clienteInput) clienteInput.value = '';
    const pedidoInput = document.getElementById('pedidoFilter');
    if (pedidoInput) pedidoInput.value = '';
    const facturaInput = document.getElementById('facturaFilter');
    if (facturaInput) facturaInput.value = '';
    const referenciaInput = document.getElementById('referenciaFilter');
    if (referenciaInput) referenciaInput.value = '';

    // Limpiar filtro de estado visual y en sessionStorage
    sessionStorage.removeItem('estadoFiltro');
    const estadoFilterDiv = document.getElementById('estadoFilter');
    if (estadoFilterDiv) estadoFilterDiv.classList.remove('show');
    const filterButtonIcon = document.querySelector('.filter-button i');
    if (filterButtonIcon) filterButtonIcon.style.transform = 'rotate(0deg)';

    // 🗑️ INVALIDAR CACHE
    cachedResults = null;
    cacheTimestamp = null;
    lastFilters = null;

    // Recargar datos sin filtros y ocultar barra de progreso si está visible
    fetchPageData(1, false, () => {
        hideButtonSpinner('clearFilters');
        const loadingPopup = document.getElementById('loadingPopup');
        if (loadingPopup) loadingPopup.style.display = 'none';
    });
}
        hideButtonSpinner('clearFilters');
    
/**
 * Filtra los pedidos por estado
 */
function sortTableByEstado(estado) {
    if (isLoading) return;
    
    console.log(`🔍 Filtrando por estado: ${estado} - invalidando cache`);
    
    // Guardar estado seleccionado
    sessionStorage.setItem('estadoFiltro', estado);
    
    // 🗑️ INVALIDAR CACHE porque cambió el filtro
    cachedResults = null;
    cacheTimestamp = null;
    lastFilters = null;
    
    // Mostrar barra de progreso principal
    document.getElementById('loadingPopup').style.display = 'flex';
    const progressInterval = showMainProgressBar();
    
    // Cargar primera página con este filtro
    fetchPageData(1, false, () => {
        setTimeout(() => {
            clearInterval(progressInterval);
            document.getElementById('loadingPopup').style.display = 'none';
            showEstadoFilter();
        }, 500);  // aqui se oculta la barra de progreso
    });
}

/**
 * Muestra u oculta el filtro de estado
 */
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

/**
 * Recupera datos paginados del servidor
 */
function fetchPageData(page, isPagination = false, callback = null) {
    if (isLoading) return;
    
    const now = Date.now();
    const filtersChanged = hasFiltersChanged();
    
    // 🎯 VERIFICAR SI PODEMOS USAR CACHE
    if (cachedResults && 
        cacheTimestamp && 
        (now - cacheTimestamp) < CACHE_DURATION &&
        !filtersChanged &&
        isPagination) {
        
        console.log(`⚡ Usando CACHE para página ${page}`);
        currentPage = page;
        displayCachedPage(page);
        
        // Ocultar spinners de paginación si es necesario
        if (isPagination) {
            hideButtonSpinner('prevPage');
            hideButtonSpinner('nextPage');
        }
        
        if (callback) callback();
        return;
    }
    
    // 🔄 NECESITAMOS HACER NUEVA CONSULTA
    console.log(`🌐 Consulta NUEVA para página ${page} ${filtersChanged ? '(filtros cambiaron)' : '(cache expirado)'}`);
    
    isLoading = true;
    
    // Solo mostrar barra de progreso si NO es paginación
    let progressInterval = null;
    if (!isPagination) {
        document.getElementById('loadingPopup').style.display = 'flex';
        progressInterval = showMainProgressBar();
    }
    
    // Obtener valores de filtro
    const cliente = document.getElementById('clienteFilter').value;
    const pedido = document.getElementById('pedidoFilter').value;
    const factura = document.getElementById('facturaFilter').value;
    const estadoActual = sessionStorage.getItem('estadoFiltro') || '';
    
    // 💡 PARA CACHE: Siempre pedimos TODOS los datos (sin limit)
    const url = `/api/vendedor_orders?vendedor=${encodeURIComponent(vendedorName)}` +
        `&page=${page}&limit=${itemsPerPage}` +
        `&cliente=${encodeURIComponent(cliente)}` +
        `&pedido=${encodeURIComponent(pedido)}` +
        `&factura=${encodeURIComponent(factura)}` +
        `&estado=${encodeURIComponent(estadoActual)}` +
        `&_=${new Date().getTime()}`;

    setTimeout(() => {
        fetch(url)
            .then(handleResponse)
            .then(data => {
                // 💾 GUARDAR EN CACHE SOLO SI QUIERES CACHE GLOBAL (opcional)
                // cachedResults = data.orders;
                // cacheTimestamp = now;

                // Mostrar la página solicitada con los datos del backend
                currentPage = page;
                updateUI(data);
            })
            .catch(handleError)
            .finally(() => {
                isLoading = false;
                
                // Ocultar barra de progreso principal si se mostró
                if (!isPagination && progressInterval) {
                    setTimeout(() => {
                        clearInterval(progressInterval);
                        document.getElementById('loadingPopup').style.display = 'none';
                    }, 500); //aqui se oculta la barra de progreso
                }
                
                // Ocultar spinners de paginación
                if (isPagination) {
                    hideButtonSpinner('prevPage');
                    hideButtonSpinner('nextPage');
                }
                
                if (callback) callback();
            });
    }, isPagination ? 300 : 5); // Menos delay para paginación
}

/**
 * Verifica la respuesta HTTP
 */
function handleResponse(response) {
    if (!response.ok) {
        throw new Error('Error al obtener datos');
    }
    return response.json();
}

/**
 * Actualiza la interfaz con los datos obtenidos
 */
function updateUI(data) {
    console.log('Actualizando UI con datos:', data);
    // Actualizar estado global
    orders = data.orders;
    totalItems = data.totalItems || data.total_count;
    currentPage = data.currentPage;
    totalPages = data.totalPages;
    
    // Si no hay resultados con un filtro, mostrar mensaje
    if (orders.length === 0 && sessionStorage.getItem('estadoFiltro')) {
        Swal.fire({
            icon: 'info',
            title: 'Sin resultados',
            text: `No se encontraron pedidos con el estado: ${sessionStorage.getItem('estadoFiltro')}`,
            confirmButtonText: 'Entendido',
            confirmButtonColor: '#00a3b4'
        });
        return;
    }
    
    // Mostrar datos en la tabla
    renderTable();
    
    // Actualizar controles de paginación
    updatePagination();
    
    // Mostrar tabla si hay datos
    if (orders.length > 0) {
        document.querySelector('.table-container').style.display = 'block';
        document.getElementById('initialMessage').style.display = 'none';
    } else {
        document.getElementById('initialMessage').textContent = 'No se encontraron datos para mostrar';
        document.getElementById('initialMessage').style.display = 'block';
    }
}

/**
 * Maneja errores en la solicitud
 */
function handleError(error) {
    console.error('Error:', error);
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'Ocurrió un error al cargar los datos.',
        confirmButtonColor: '#00a3b4'
    });
}

/**
 * Actualiza los controles de paginación
 */
function updatePagination() {
    const cacheIndicator = cachedResults ? ' 📋' : ' 🌐';
    
    document.getElementById('pageInfo').textContent =
        `Página ${currentPage}/${totalPages} (${totalItems})${cacheIndicator}`;

    document.getElementById('prevPage').disabled = currentPage <= 1;
    document.getElementById('nextPage').disabled = currentPage >= totalPages;
}

/**
 * Renderiza la tabla con los pedidos actuales
 */
function renderTable() {
    const tableBody = document.getElementById('ordersTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';

    orders.forEach((order, index) => {
        const row = document.createElement('tr');
        
        // Determinar clase de estilo según el estado
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
        
        // Aplicar clase a la fila
        row.className = estadoClass;
        
        // Crear ID único para el objeto order
        const orderID = `order_${index}`;
        window[orderID] = order;
        
        // Crear HTML de la fila
        row.innerHTML = `
            <td>
                <div class="pedido-circle ${estadoClass}" onclick="showTraceModal(window['${orderID}'])">
                    ${order.numero_pedido || 'No disponible'}
                </div>
            </td>
            <td>${order.estado_documento || 'No disponible'}</td>
            <td>${order.cliente || 'N/A'}</td>
            <td>${order.numero_factura || 'N/A'}</td>
            <td>${order.razon_social_vendedor || 'N/A'}</td>
        `;
        
        // Agregar fila a la tabla
        tableBody.appendChild(row);
    });
}

/**
 * Formatea una fecha para mostrarla en español
 */
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


/**
 * Muestra el modal con la información detallada del pedido
 */
function showTraceModal(order) {
    const modal = document.getElementById('traceModal');
    const timeline = document.getElementById('pedidoTimeline');
    const modalPedidoNumero = document.getElementById('modalPedidoNumero');
    
    modalPedidoNumero.textContent = order.numero_pedido;
    timeline.innerHTML = '';
    
    console.log("Datos del pedido:", order);
    
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
            fecha: order['Fecha Preparacion de pedido'] || order.fecha_preparacion || order.fecha_preparacion_de_pedido,
            icono: 'fas fa-box-open',
            descripcion: 'Pedido en preparación',
            mensajePendiente: 'Pendiente de preparación'
        },
        {
            titulo: 'Picking',
            fecha: order['Fecha picking'] || order.fecha_picking,
            icono: 'fas fa-people-carry',
            descripcion: 'Proceso de picking completado',
            mensajePendiente: 'Pendiente de picking',
            numeroPicking: order.numero_de_picking || 'No disponible'
        },
        {
            titulo: 'Alistamiento',
            fecha: order['Fecha picking'] || order.fecha_picking,
            icono: 'fas fa-dolly',
            descripcion: 'Pedido alistado para despacho',
            mensajePendiente: 'Pendiente de alistamiento'
        },
        {
            titulo: 'Despacho',
            fecha: order['Fecha de despacho de Pedido'] || order.fecha_despacho,
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

        // Si la fecha es 'Completado' (para Picking/Alistamiento), marcar como completado
        if (estado.fecha === 'Completado') {
            tieneFecha = true;
            fecha = 'Completado';
        } else if (estado.fecha && estado.fecha !== 'No disponible' && estado.fecha !== '') {
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
                    ${estado.titulo === 'Picking' && estado.numeroPicking ? `<span style="color:#00a3b4; font-weight:bold; margin-left:10px;">#${estado.numeroPicking}</span>` : ''}

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