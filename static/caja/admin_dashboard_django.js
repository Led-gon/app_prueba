document.addEventListener('DOMContentLoaded', async function() {
    // Asegurarse de que API_URLS y CSRF_TOKEN estén definidos en el HTML
    if (typeof API_URLS === 'undefined') {
        console.error("Error: API_URLS no están definidas. Asegúrate de incluirlas en tu plantilla HTML antes de cargar este script.");
        return;
    }

    // Referencias a elementos DOM (consolidadas desde ambos bloques originales)
    const ordersTableBody = document.querySelector('#ordersTable tbody');
    const ordersMessage = document.getElementById('ordersMessage');
    const filterDateInput = document.getElementById('filterDate');
    const filterStatusSelect = document.getElementById('filterStatus');
    const applyFiltersButton = document.getElementById('applyFiltersButton');
    const listUsersButton = document.getElementById('listUsersButton');

    const listProductsButton = document.getElementById('listProductsButton');
    const productsTableBody = document.querySelector('#productsTable tbody');
    const productsListMessage = document.getElementById('productsListMessage');
    const newProductNameInput = document.getElementById('newProductName');
    const newProductDescriptionInput = document.getElementById('newProductDescription');
    const newProductPriceInput = document.getElementById('newProductPrice');
    const newProductStockInput = document.getElementById('newProductStock');   
    const newProductCategoryInput = document.getElementById('newProductCategory');
    const newProductImageInput = document.getElementById('newProductImage');

    const addProductButton = document.getElementById('addProductButton');
    const addProductMessage = document.getElementById('addProductMessage');

    const searchProductNameStockInput = document.getElementById('searchProductNameStock');
    const searchProductStockButton = document.getElementById('searchProductStockButton');
    const productStockDetailsDiv = document.getElementById('productStockDetails');
    const modifyProductStockMessage = document.getElementById('modifyProductStockMessage');

    const navButtons = document.querySelectorAll('.nav-button');
    const sections = document.querySelectorAll('.dashboard-content');

    // Sub-tab navigation for products
    const productSubnavButtons = document.querySelectorAll('.products-subnav .subnav-button');
    const productSections = document.querySelectorAll('#productsSection .product-content');

    // Elementos específicos de Gestión de Usuarios
    const usersSubnavButtons = document.querySelectorAll('.users-subnav .subnav-button');
    const usersContentSections = document.querySelectorAll('#usersSection .users-content');

    const usersTableBody = document.querySelector('#usersTableBody');
    const usersListMessage = document.getElementById('usersListMessage');

    const newUsernameInput = document.getElementById('newUsername');
    const newUserPasswordInput = document.getElementById('newUserPassword');
    const newUserRoleSelect = document.getElementById('newUserRole');
    const createUserButton = document.getElementById('createUserButton');
    const createUserMessage = document.getElementById('createUserMessage');

    const modifyUsernameSearch = document.getElementById('modifyUsernameSearch');
    const searchUserToModifyButton = document.getElementById('searchUserToModifyButton');
    const modifyUserDetailsDiv = document.getElementById('modifyUserDetails');
    const editingUsername = document.getElementById('editingUsername');
    const modifyUserRoleSelect = document.getElementById('modifyUserRole');
    const modifyUserPasswordInput = document.getElementById('modifyUserPassword');
    const submitUserModificationButton = document.getElementById('submitUserModificationButton');
    const modifyUserMessage = document.getElementById('modifyUserMessage');

    // --- Gestión de Pedidos "Listo para Entregar" ---
    const readyOrdersCardsDiv = document.getElementById('readyOrdersCards');
    const ordersManagementMessage = document.getElementById('ordersManagementMessage');


    let currentUsernameToModify = null; // Variable para almacenar el usuario que se está editando

    // Elementos relacionados con la sesión y el logout (desde el segundo DCL original)
    // const usernameDisplay = document.getElementById('usernameDisplay'); // No se usa en el HTML proporcionado
    // const userRoleDisplay = document.getElementById('userRoleDisplay'); // No se usa en el HTML proporcionado
    const logoutForm = document.getElementById('logoutForm'); // Mantenemos la referencia

    // showMessage se encarga de mostrar mensajes de éxito o error en el dashboard
    // Función única, consolidada
    function showMessage(element, text, isError = false) {
        if (!element) return;
        element.textContent = text;
        element.className = 'message ' + (isError ? 'error' : 'success');
        // Eliminar mensaje después de 4 segundos, pero solo si no es un mensaje de error persistente (ej: cargando)
        if (text && !isError) { // Solo limpia mensajes de éxito o informativos
            setTimeout(() => { element.textContent = ''; element.className = 'message'; }, 4000);
        }
    }

    // Función auxiliar para obtener el token CSRF (necesario para POST/PUT/DELETE)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // checkSessionAndLoadAdminData se encarga de verificar la sesión y cargar los datos iniciales
    // Función única, consolidada. Se basa en la versión más completa y los requerimientos de rol.
    async function checkSessionAndLoadAdminData() {
        try {
            const response = await fetch(API_URLS.session_status);
            const data = await response.json();
            if (data.logged_in) {
                if (data.role === 'Empleado') {
                // Mostrar la grilla de pedidos listos para entregar
                    navButtons.forEach(btn => btn.classList.remove('active'));
                    sections.forEach(sec => sec.classList.remove('active'));
                    const ordersManagementBtn = document.querySelector('.nav-button[data-target="ordersManagementSection"]');
                    const ordersManagementSection = document.getElementById('ordersManagementSection');
                    if (ordersManagementBtn && ordersManagementSection) {
                        ordersManagementBtn.classList.add('active');
                        ordersManagementSection.classList.add('active');
                        fetchReadyOrders();
                    }
                }
                // Aquí se verifica el rol del usuario logueado para mostrar el dashboard apropiado
                // Si el rol no es válido para el dashboard de administración, redirige al login
                if (data.role === 'Empleado' || data.role === 'Administrador' || data.role === 'Super Usuario') {
                    // Si el usuario es Super Usuario, cargar usuarios al inicio.
                    // Esto inicializa el panel correctamente con los datos para su rol.
                    if (data.role === 'Super Usuario') {
                        // Asegurar que la sub-navegación de usuarios se inicialice correctamente activa la primera pestaña
                        if (usersSubnavButtons.length > 0 && usersContentSections.length > 0) {
                            usersSubnavButtons[0].classList.add('active-subtab');
                            usersContentSections[0].classList.add('active-subtab');
                            fetchUsers(); // Carga usuarios para la pestaña activa
                        }
                    }
                    // Para empleados y administradores, la gestión de pedidos es la primera pestaña activa por defecto
                    filterDateInput.value = new Date().toISOString().split('T')[0];
                    fetchOrders(); // Siempre se carga pedidos al inicio
                } else {
                    // Si el rol no es adecuado, redirige al login
                    showMessage(ordersMessage, "Acceso no autorizado para este panel. Redirigiendo...", true);
                    setTimeout(() => window.location.href = API_URLS.login || "/", 2000);
                    return;
                }
            } else {
                // Si no está logueado, redirige al login
                window.location.href = API_URLS.login || "/";
            }
        } catch (error) {
            console.error("Error de sesión en admin dashboard:", error);
            showMessage(ordersMessage, "Error de sesión. Redirigiendo...", true);
            setTimeout(() => window.location.href = API_URLS.login || "/", 2000);
        }
    }

    // --- Gestión de Pedidos ---

    // fetchOrders se encarga de obtener los pedidos del backend y renderizarlos
    async function fetchOrders() {
        showMessage(ordersMessage, 'Cargando pedidos...');
        const date = filterDateInput.value;
        const status = filterStatusSelect.value;
        let url = `${API_URLS.orders_list_create}?date=${date}`;
        if (status) url += `&status=${status}`;
        
        try {
            const response = await fetch(url);
            const orders = await response.json();
            if (!response.ok) throw new Error(orders.error || 'Error al cargar pedidos');
            renderOrders(orders);
            showMessage(ordersMessage, orders.length === 0 ? 'No hay pedidos para los filtros seleccionados.' : '');
        } catch (e) { showMessage(ordersMessage, e.message, true); }
    }

    // renderOrders se encarga de renderizar los pedidos en la tabla del dashboard
    function renderOrders(orders) {
        
        ordersTableBody.innerHTML = '';
        if (!orders || orders.length === 0) {
            ordersTableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No hay pedidos.</td></tr>';
            return;
        }
        orders.forEach(order => {
            const row = ordersTableBody.insertRow();
            row.insertCell().textContent = order.id;
            row.insertCell().textContent = order.customer_name || 'N/A';
            row.insertCell().textContent = order.table || 'N/A';
            row.insertCell().textContent = order.date;
            row.insertCell().textContent = order.status;
            row.insertCell().textContent = order.total ? `$${parseFloat(order.total).toFixed(2)}` : 'N/A';
            const actionsCell = row.insertCell();
            if (order.status !== 'Entregado' && order.status !== 'Cancelado') {
                const changeStatusBtn = document.createElement('button');
                changeStatusBtn.textContent = 'Mod. Estado'; changeStatusBtn.classList.add('action-button');
                changeStatusBtn.onclick = () => promptChangeOrderStatus(order.id, order.status);
                actionsCell.appendChild(changeStatusBtn);

                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancelar'; cancelBtn.classList.add('action-button', 'cancel');
                cancelBtn.onclick = () => cancelOrder(order.id);
                actionsCell.appendChild(cancelBtn);
            }

            // Evento click para mostrar modal con detalles
            row.addEventListener('click', function(e) {
            // Evita que el modal se abra si el click fue en un botón de acción
            if (
                e.target.classList.contains('action-button') ||
                e.target.classList.contains('cancel') ||
                e.target.classList.contains('modify-button')
            ) return;
                showOrderDetailsModal(order);
            });
        });
    }
    
    // promptChangeOrderStatus se encarga de mostrar un modal para cambiar el estado del pedido
    async function promptChangeOrderStatus(orderId, currentStatus) {
        console.log("promptChangeOrderStatus called", orderId, currentStatus);
        // Lista de estados válidos (basado en tu models.py)
        const validStatuses = [
            {id: 1, name: "Pendiente"},
            {id: 2, name: "En Preparación"},
            {id: 3, name: "Listo para Entregar"},
            {id: 4, name: "Entregado"}
        ];

        // Crear un modal simple usando prompt-like behavior con select (tu implementación original)
        const select = document.createElement('select');
        validStatuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status.id;
            option.textContent = status.name;
            if (status.id === currentStatus) option.selected = true;
            select.appendChild(option);
        });
        // Crear el modal
        const modal = document.createElement('div');
        modal.classList.add('custom-modal-overlay'); // Clase para estilos CSS del modal
        modal.innerHTML = `
            <div class="custom-modal-content">
                <p id="modalMessage">Nuevo estado para pedido #${orderId} (actual: <b>${validStatuses.find(s => s.id === currentStatus)?.name || currentStatus}</b>):</p>
                <select id="modalStatusSelect" class="modal-select">
                    ${validStatuses.map(status => `<option value="${status.id}" ${status.id === currentStatus ? 'selected' : ''}>${status.name}</option>`).join('')}
                </select>
                <div class="modal-buttons">
                    <button id="modalOkBtn" class="modal-button primary">Actualizar</button>
                    <button id="modalCancelBtn" class="modal-button secondary">Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        const modalOkBtn = document.getElementById('modalOkBtn');
        const modalCancelBtn = document.getElementById('modalCancelBtn');
        const modalStatusSelect = document.getElementById('modalStatusSelect');

        return new Promise((resolve) => {
            modalOkBtn.onclick = async () => {
                const newStatus = modalStatusSelect.value;
                document.body.removeChild(modal);
                if (newStatus && newStatus != currentStatus) { // Uso != para permitir comparar number con string si API lo envía así
                    try {
                        const url = API_URLS.order_detail_update_delete.replace('12345', orderId);
                        const response = await fetch(url, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                            body: JSON.stringify({ status: newStatus })
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.error || 'Error al actualizar estado');
                        showMessage(ordersMessage, data.message);
                        fetchOrders();
                    } catch (e) {
                        showMessage(ordersMessage, e.message, true);
                    }
                }
                resolve();
            };
            modalCancelBtn.onclick = () => {
                document.body.removeChild(modal);
                resolve();
            };
        });
    }

    // cancelOrder se encarga de cancelar un pedido (tu implementación original con confirm())
    async function cancelOrder(orderId) {
        // Usa tu showConfirmationModal personalizado
        const confirmed = await showConfirmationModal(`¿Seguro que desea cancelar el pedido #${orderId}? Esta acción es irreversible.`);
        if (!confirmed) {
            return; // El usuario canceló
        }

        try {
            const url = API_URLS.order_detail_update_delete.replace('12345', orderId); // Reemplazar placeholder
            const response = await fetch(url , {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error al cancelar pedido');
            showMessage(ordersMessage, data.message); fetchOrders();
        } catch (e) { showMessage(ordersMessage, e.message, true); }
    }
    
    // Función genérica para mostrar un modal de confirmación (tu implementación original)
    function showConfirmationModal(message) {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.classList.add('custom-modal-overlay');
            modal.innerHTML = `
                <div class="custom-modal-content">
                    <p>${message}</p>
                    <div class="modal-buttons">
                        <button id="confirmOkBtn" class="modal-button primary">Sí</button>
                        <button id="confirmCancelBtn" class="modal-button secondary">No</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            document.getElementById('confirmOkBtn').onclick = () => {
                document.body.removeChild(modal);
                resolve(true);
            };
            document.getElementById('confirmCancelBtn').onclick = () => {
                document.body.removeChild(modal);
                resolve(false);
            };
        });
    }

    if(applyFiltersButton) applyFiltersButton.addEventListener('click', fetchOrders);

    // --- Gestión de Productos ---
    // fetchProducts se encarga de obtener la lista de productos del backend y renderizarlos
    async function fetchProducts() {
        showMessage(productsListMessage, 'Cargando productos...');
        try {
            const response = await fetch(API_URLS.products_list_create);
            const products = await response.json();
            if(!response.ok) throw new Error(products.error || 'Error al cargar productos');
            renderProducts(products);

            let totalProductos = 0;
            if (Array.isArray(products)) {
                totalProductos = products.length;
            } else if (products && typeof products === 'object') {
                totalProductos = Object.values(products).reduce((acc, arr) => acc + (Array.isArray(arr) ? arr.length : 0), 0);
            }
            showMessage(productsListMessage, totalProductos === 0 ? 'No hay productos registrados.' : '');
        } catch(e){ showMessage(productsListMessage, e.message, true); }
    }

    // renderProducts se encarga de renderizar la lista de productos en la tabla del dashboard
    function renderProducts(products) {
        // Si es un array vacío, conviértelo a objeto vacío
        if (Array.isArray(products)) {
            products = {};
        }
        productsTableBody.innerHTML = '';
        // Si no hay productos, muestra mensaje
        if (!products || Object.keys(products).length === 0) {
            productsTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No hay productos.</td></tr>';
            return;
        }
        Object.keys(products).forEach(function(categoria) {
            // Fila de encabezado para la categoría
            const headerRow = productsTableBody.insertRow();
            const headerCell = headerRow.insertCell();
            headerCell.colSpan = 5;
            headerCell.textContent = categoria.toUpperCase();
            headerCell.className = 'categoria-header';
            // Listar productos de la categoría
            products[categoria].forEach(function(producto) {
                const r = productsTableBody.insertRow();
                r.insertCell().textContent = producto.id;
                r.insertCell().textContent = producto.name;
                r.insertCell().textContent = `$${parseFloat(producto.price).toFixed(2)}`;
                r.insertCell().textContent = producto.stock;
            });
        });

    }

    // Añadir evento click al botón de listar productos
    if(listProductsButton) listProductsButton.addEventListener('click', fetchProducts);

    // Añadir nuevo producto
    if(addProductButton) addProductButton.addEventListener('click', async () => {
        const name = newProductNameInput.value.trim();
        const description = newProductDescriptionInput.value.trim();
        const price = newProductPriceInput.value; // Se validará en backend como Decimal
        const stock = newProductStockInput.value;
        const category = newProductCategoryInput.value;
        const image = newProductImageInput.files[0];

        if (!name || !price || stock === '' || !category) { // Chequeo básico, backend hace el fuerte
            showMessage(addProductMessage, 'Nombre, precio, stock y categoria son requeridos.', true); return;
        }
        try {
             const formData = new FormData();
             formData.append('name', name);
             formData.append('description', description);
             formData.append('price', price);
             formData.append('stock', stock);
             formData.append('category', category);
             if(image) formData.append('image', image); // adjuntar archivo

             const response = await fetch(API_URLS.products_list_create, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCookie('csrftoken') } // NO Content-Type
            
            });
            const data = await response.json();
            if(!response.ok) throw new Error(data.error || "Error al añadir producto");
            showMessage(addProductMessage, data.message);
            newProductNameInput.value = '';
            newProductDescriptionInput.value = "";
            newProductPriceInput.value = '';
            newProductStockInput.value = '';
            newProductCategoryInput.value = '';
            newProductImageInput.value = '';
            fetchProducts(); // Refrescar lista
        } catch(e){ showMessage(addProductMessage, e.message, true); }
    });

    // Modificar stock de producto
    if(searchProductStockButton) searchProductStockButton.addEventListener('click', async () => {
        const name = searchProductNameStockInput.value.trim();
        if(!name) { showMessage(modifyProductStockMessage, "Ingrese nombre de producto.", true); return; }
        productStockDetailsDiv.innerHTML = 'Buscando...';
        try {
            const response = await fetch(`${API_URLS.get_product_by_name}?name=${encodeURIComponent(name)}`);
            const p = await response.json();
            if(!response.ok) throw new Error(p.error || 'Producto no encontrado');
            productStockDetailsDiv.innerHTML = `
                <p><strong>ID:</strong> ${p.id}, <strong>Nombre:</strong> ${p.name}, <strong>Stock Actual:</strong> ${p.stock}</p>
                <label for="newStockValue_${p.id}">Nuevo Stock:</label>
                <input type="number" id="newStockValue_${p.id}" value="${p.stock}" min="0" style="width: 80px; margin-right: 10px;">
                <button onclick="updateProductStock(${p.id})">Actualizar Stock</button>`; // Func global
            showMessage(modifyProductStockMessage, "Producto encontrado.");
        } catch(e){ showMessage(modifyProductStockMessage, e.message, true); productStockDetailsDiv.innerHTML = ''; }
    });

    // updateProductStock se encarga de actualizar el stock de un producto
    window.updateProductStock = async function(productId) { // Hacerla global para el botón
        const stockInput = document.getElementById(`newStockValue_${productId}`);
        const stock = parseInt(stockInput.value);
        if(isNaN(stock) || stock < 0) { showMessage(modifyProductStockMessage, "Stock debe ser un número >= 0.", true); return; }
        try {
            // **CORRECCIÓN AQUÍ:** Reemplazamos el '0' en la URL con el ID real del producto.
            const url = API_URLS.update_product_stock.replace('/0/', `/${productId}/`);
            const response = await fetch(url, {
                method: 'PUT', headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN},
                body: JSON.stringify({stock})
            });
            const data = await response.json();
            if(!response.ok) throw new Error(data.error || 'Error al actualizar stock');
            showMessage(modifyProductStockMessage, data.message);
            productStockDetailsDiv.innerHTML = ''; searchProductNameStockInput.value = '';
            fetchProducts(); // Refrescar
        } catch(e){ showMessage(modifyProductStockMessage, e.message, true); }
    }

    // --- Navegación entre secciones Principales (Pedidos, Productos, Usuarios) ---

    // Añadir evento click a los botones de navegación principales
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Eliminar 'active' de todos los botones y secciones
            navButtons.forEach(btn => btn.classList.remove('active'));
            sections.forEach(sec => sec.classList.remove('active'));

            // Añadir 'active' al botón clickeado y a la sección correspondiente
            this.classList.add('active');
            const targetId = this.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            // Lógica específica para cada sección principal
            if (targetId === 'ordersSection') {
                fetchOrders();
            } else if (targetId === 'productsSection') {
                fetchProducts();
                // Si es la sección de productos, asegurar que una sub-pestaña esté activa
                const anyActive = document.querySelector('#productsSection .subnav-button.active-subtab');
                if (!anyActive && productSubnavButtons.length > 0 && productSections.length > 0) {
                    productSubnavButtons.forEach(btn => btn.classList.remove('active-subtab'));
                    productSections.forEach(sec => sec.classList.remove('active-subtab'));
                    productSubnavButtons[0].classList.add('active-subtab');
                    productSections[0].classList.add('active-subtab');
                }
                // Limpiar campos de búsqueda de productos
                searchProductNameStockInput.value = '';
                productStockDetailsDiv.innerHTML = '';
                modifyProductStockMessage.textContent = '';
            } else if (targetId === 'usersSection') { // Lógica para Gestión de Usuarios
                fetchUsers(); // Cargar usuarios al entrar a la sección
                // Asegurar que una sub-pestaña de usuarios esté activa (generalmente la primera: Listado)
                const anyActiveUserSubtab = document.querySelector('#usersSection .subnav-button.active-subtab');
                if (!anyActiveUserSubtab && usersSubnavButtons.length > 0 && usersContentSections.length > 0) {
                    usersSubnavButtons.forEach(btn => btn.classList.remove('active-subtab'));
                    usersContentSections.forEach(sec => sec.classList.remove('active-subtab'));
                    usersSubnavButtons[0].classList.add('active-subtab');
                    usersContentSections[0].classList.add('active-subtab');
                }
                // Limpiar campos de búsqueda de usuarios
                modifyUsernameSearch.value = '';
                modifyUserDetailsDiv.style.display = 'none'; // Ocultar el formulario de modificación
                modifyUserMessage.textContent = '';
                currentUsernameToModify = null; // Resetear usuario a modificar
            }
        });
    });

    navButtons.forEach(btn=>{
        const target = document.getElementById(btn.dataset.target);
        if(!target) btn.remove();
    });

    // --- Manejo de subnavegación para productos ---
    productSubnavButtons.forEach(button => {
        button.addEventListener('click', function() {
            productSubnavButtons.forEach(btn => btn.classList.remove('active-subtab'));
            productSections.forEach(sec => sec.classList.remove('active-subtab'));

            this.classList.add('active-subtab');
            const targetId = this.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active-subtab');

            // Lógica específica para la sub-navegación de productos
            if (targetId === 'productsListSection') {
                fetchProducts(); // Recargar lista al ir a esta pestaña
            } else if (targetId === 'productsAddSection') {
                // Limpiar campos del formulario de añadir producto
                newProductNameInput.value = '';
                newProductPriceInput.value = '';
                newProductStockInput.value = '';
                addProductMessage.textContent = '';
            } else if (targetId === 'productsStockSection') {
                // Limpiar campos de la sección de modificar stock
                searchProductNameStockInput.value = '';
                productStockDetailsDiv.innerHTML = '';
                modifyProductStockMessage.textContent = '';
            }
        });
    });

    // --- Funciones de Gestión de Usuarios (CRUD) ---

    // Función para LISTAR usuarios
    async function fetchUsers() {
        showMessage(usersListMessage, 'Cargando usuarios...');
        try {
            const response = await fetch(API_URLS.api_superuser_users_list_create);
            const users = await response.json();
            if (!response.ok) throw new Error(users.error || 'Error al cargar usuarios');
            renderUsers(users);
            showMessage(usersListMessage, users.length === 0 ? 'No hay usuarios.' : '');
        } catch (error) {
            showMessage(usersListMessage, error.message, true);
            usersTableBody.innerHTML = '<tr><td colspan="3">Error al cargar usuarios.</td></tr>';
        }
    }

    // Renderizar usuarios en la tabla
    function renderUsers(users) {
        usersTableBody.innerHTML = '';
        if (!users || users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No hay usuarios.</td></tr>';
            return;
        }
        users.forEach(user => {
            const row = usersTableBody.insertRow();
            row.insertCell().textContent = user.username;
            row.insertCell().textContent = user.role;
            const actionsCell = row.insertCell();
            //boton modificar
            const modifyBtn = document.createElement('button');
            modifyBtn.textContent = 'Modificar';
            modifyBtn.classList.add('action-button', 'modify-button');
            // Al hacer clic en modificar, navega a la pestaña de modificar usuario y precarga los datos
            modifyBtn.onclick = () => {
                // Activar la pestaña de modificar usuario
                usersSubnavButtons.forEach(btn => btn.classList.remove('active-subtab'));
                usersContentSections.forEach(sec => sec.classList.remove('active-subtab'));
                const modifyButton = document.querySelector('.users-subnav button[data-target="usersModifySection"]');
                if (modifyButton) {
                    modifyButton.classList.add('active-subtab');
                    document.getElementById('usersModifySection').classList.add('active-subtab');
                }
                prepareUserModification(user.username, user.role);
            };
            actionsCell.appendChild(modifyBtn);
            // boton eliminar
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Eliminar';
            deleteBtn.classList.add('action-button', 'delete-button');
            deleteBtn.onclick = () => deleteUser(user.username);
            actionsCell.appendChild(deleteBtn);
        });
    }

    // --- Función para ELIMINAR usuario --- SE REENVIA LA FUNCIÓN deleteUser PARA UPDATE ESTETICO
    /**
     * Elimina un usuario del sistema.
     * @param {string} username - El nombre de usuario del usuario a eliminar.
     */
    async function deleteUser(username) {
        const confirmed = await showConfirmationModal(`¿Estás seguro de que quieres eliminar al usuario ${username}? Esta acción es irreversible.`);
        if (!confirmed) {
            return; // El usuario canceló la eliminación
        }

        try {
        // La URL para modificar/eliminar usuario usa el username como parámetro.
        // Se asume que el placeholder en API_URLS.api_superuser_modify_user es '0'.
        const deleteUrl = API_URLS.api_superuser_modify_user.replace('0', username);
        // console.log("URL de eliminación:", deleteUrl); // Comentado para evitar logs excesivos

        const response = await fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error desconocido al eliminar usuario.');
        }

        showMessage(usersListMessage, data.message || `Usuario ${username} eliminado exitosamente.`, false);
        fetchUsers();
        } catch (error) {
            console.error('Error al eliminar usuario:', error);
            showMessage(usersListMessage, error.message, true);
        }
    }

    // Event listener para el botón "Cargar Usuarios"
    
    if (listUsersButton) listUsersButton.addEventListener('click', fetchUsers);

    // Función para CREAR usuario
    if (createUserButton) createUserButton.addEventListener('click', async () => {
        const username = newUsernameInput.value.trim();
        const password = newUserPasswordInput.value;
        const role = newUserRoleSelect.value;
        if (!username || !password || !role) {
            showMessage(createUserMessage, 'Todos los campos son requeridos.', true);
            return;
        }
        try {
            const response = await fetch(API_URLS.api_superuser_users_list_create, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ username, password, role })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error al crear usuario');
            showMessage(createUserMessage, data.message);
            newUsernameInput.value = '';
            newUserPasswordInput.value = '';
            newUserRoleSelect.value = ''; // Reset select
            fetchUsers(); // Actualizar lista
        } catch (error) {
            showMessage(createUserMessage, error.message, true);
        }
    });

    // Función para preparar el formulario de MODIFICAR usuario
    function prepareUserModification(username, currentRole) {
        currentUsernameToModify = username;
        editingUsername.textContent = username;
        modifyUserRoleSelect.value = currentRole; // Establecer rol actual para conveniencia
        modifyUserPasswordInput.value = ""; // Limpiar campo de contraseña
        modifyUserDetailsDiv.style.display = 'block'; // Mostrar la sección de modificación
        modifyUsernameSearch.value = username; // Rellenar opcionalmente el campo de búsqueda
        showMessage(modifyUserMessage, `Editando usuario: ${username}. Deje campos vacíos para no modificarlos.`);
    }

    // Event listener para el botón "Buscar / Seleccionar" usuario para modificar
    if (searchUserToModifyButton) searchUserToModifyButton.addEventListener('click', () => {
        const usernameToSearch = modifyUsernameSearch.value.trim();
        if (!usernameToSearch) {
            showMessage(modifyUserMessage, "Ingrese un username para buscar y modificar.", true);
            return;
        }
        // Busca el usuario en la tabla actualmente renderizada
        const userRow = Array.from(usersTableBody.querySelectorAll('tr')).find(row => row.cells[0].textContent.toLowerCase() === usernameToSearch.toLowerCase());

        if (userRow) {
            const userRole = userRow.cells[1].textContent;
            prepareUserModification(usernameToSearch, userRole);
        } else {
            showMessage(modifyUserMessage, `Usuario '${usernameToSearch}' no encontrado en la lista actual. Cargue la lista primero o verifique el nombre.`, true);
            modifyUserDetailsDiv.style.display = 'none';
            currentUsernameToModify = null;
        }
    });

    // Event listener para el botón "Actualizar Usuario"
    if (submitUserModificationButton) submitUserModificationButton.addEventListener('click', async () => {
        if (!currentUsernameToModify) {
            showMessage(modifyUserMessage, "Primero busque y seleccione un usuario a modificar.", true);
            return;
        }
        const newRole = modifyUserRoleSelect.value;
        const newPassword = modifyUserPasswordInput.value;
        const payload = {};
        if (newRole && newRole !== modifyUserRoleSelect.options[0].value) payload.role = newRole; // Solo envía si se selecciona un nuevo rol
        if (newPassword) payload.password = newPassword; // Solo envía si se proporciona una nueva contraseña

        if (Object.keys(payload).length === 0) {
            showMessage(modifyUserMessage, "No se especificaron cambios (nuevo rol o contraseña).", true);
            return;
        }
        try {
            // La URL para modificar/eliminar usuario usa el username como parámetro.
            // Se asume que el placeholder en API_URLS.api_superuser_modify_user es '0'.
            const url = API_URLS.api_superuser_modify_user.replace('0', currentUsernameToModify);
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error al modificar usuario');
            showMessage(modifyUserMessage, data.message);
            modifyUserDetailsDiv.style.display = 'none'; // Ocultar sección de modificación
            currentUsernameToModify = null;
            modifyUsernameSearch.value = ''; // Limpiar campo de búsqueda
            fetchUsers(); // Actualizar lista de usuarios
        } catch (error) {
            showMessage(modifyUserMessage, error.message, true);
        }
    });



    // --- Manejo de subnavegación para USUARIOS ---
    usersSubnavButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Eliminar active-subtab de todos los botones de usuario y secciones de contenido de usuario
            usersSubnavButtons.forEach(btn => btn.classList.remove('active-subtab'));
            usersContentSections.forEach(sec => sec.classList.remove('active-subtab'));

            // Añadir active-subtab al botón clickeado y a la sección de contenido de usuario correspondiente
            this.classList.add('active-subtab');
            const targetId = this.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active-subtab');

            // Lógica específica para la sub-navegación de usuarios
            if (targetId === 'usersListSection') {
                fetchUsers(); // Recargar la lista de usuarios al ir a esta pestaña
                modifyUserDetailsDiv.style.display = 'none'; // Ocultar detalles de modificación si se vuelve a la lista
            } else if (targetId === 'usersAddSection') {
                // Limpiar campos del formulario de añadir usuario
                newUsernameInput.value = '';
                newUserPasswordInput.value = '';
                newUserRoleSelect.value = '';
                createUserMessage.textContent = '';
            } else if (targetId === 'usersModifySection') {
                // Limpiar campos de la sección de modificar usuario y ocultar detalles
                modifyUsernameSearch.value = '';
                modifyUserDetailsDiv.style.display = 'none'; // Asegurarse de que esté oculto inicialmente
                modifyUserMessage.textContent = '';
                currentUsernameToModify = null; // Resetear usuario a modificar
            }
        });
    });

    // --- Inicialización al cargar la página ---
    // Inicializar el primer botón de navegación principal como activo
    // Esto asegura que una sección principal (Pedidos, Productos, Usuarios) siempre esté visible
    if (navButtons.length > 0) {
        // Buscar el botón 'active' actual si existe, si no, activar el primero
        const currentActiveMainButton = document.querySelector('.nav-button.active');
        if (!currentActiveMainButton) {
            navButtons[0].classList.add('active');
            const firstSectionId = navButtons[0].getAttribute('data-target');
            document.getElementById(firstSectionId).classList.add('active');
        }

        // Después de activar la sección principal, asegurar que su sub-pestaña inicial esté activa
        const activeMainSectionId = document.querySelector('.dashboard-content.active')?.id;
        if (activeMainSectionId === 'productsSection' && productSubnavButtons.length > 0) {
            const currentActiveProductSubtab = document.querySelector('#productsSection .subnav-button.active-subtab');
            if (!currentActiveProductSubtab) {
                productSubnavButtons[0].classList.add('active-subtab');
                productSections[0].classList.add('active-subtab');
            }
        } else if (activeMainSectionId === 'usersSection' && usersSubnavButtons.length > 0) {
            const currentActiveUserSubtab = document.querySelector('#usersSection .subnav-button.active-subtab');
            if (!currentActiveUserSubtab) {
                usersSubnavButtons[0].classList.add('active-subtab');
                usersContentSections[0].classList.add('active-subtab');
            }
        }
    }
    
    // Inicia la verificación de sesión y carga de datos al cargar la página
    checkSessionAndLoadAdminData();

    // Cargar pedidos "Listo para Entregar"
    async function fetchReadyOrders() {
        showMessage(ordersManagementMessage, 'Cargando pedidos...');
        try {
            //Para agregar el filtrado por fecha, descomentar las siguientes líneas y comentar la línea del URL actual
            //const date = new Date().toISOString().split('T')[0];
            //const url = `${API_URLS.orders_list_create}?date=&status=${READY_STATE_ID}`;

            const READY_STATE_ID = 3; // El id de "Listo para Entregar"
            const url = `${API_URLS.orders_list_create}?status=${READY_STATE_ID}`; // <-- Sin date
            const response = await fetch(url);
            const orders = await response.json();
            if (!response.ok) throw new Error(orders.error || 'Error al cargar pedidos');
            renderReadyOrdersCards(orders);
            showMessage(ordersManagementMessage, orders.length === 0 ? 'No hay pedidos listos para entregar.' : '');
        } catch (e) {
            showMessage(ordersManagementMessage, e.message, true);
        }
    }

    // Renderizar tarjetas
    function renderReadyOrdersCards(orders) {
        readyOrdersCardsDiv.innerHTML = '';
        if (!orders || orders.length === 0) {
            readyOrdersCardsDiv.innerHTML = '<p style="text-align:center;">No hay pedidos listos para entregar.</p>';
            return;
        }
        // Ordenar por fecha y hora descendente
        orders.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });
        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-card';
            card.innerHTML = `
                <h3>Pedido #${order.id}</h3>
                <p><strong>Fecha:</strong> ${order.date}</p>
                <p><strong>Mesa:</strong> ${order.table || order.table_number || 'N/A'}</p>
                <p><strong>Productos:</strong></p>
                <ul>
                    ${order.items.map(item => `<li>${item.product_name} x${item.quantity} ${item.sugerency ? `<br><em>Preferencias:</em> ${item.sugerency}` : ''}</li>`).join('')}
                </ul>
                <button class="deliver-btn" data-id="${order.id}">Entregar</button>
            `;
            readyOrdersCardsDiv.appendChild(card);
        });

        // Botón entregar
        document.querySelectorAll('.deliver-btn').forEach(btn => {
            btn.onclick = async function() {
                const orderId = this.dataset.id;
                try {
                    const url = API_URLS.order_detail_update_delete.replace('12345', orderId);
                    const response = await fetch(url, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                        body: JSON.stringify({ status: 4 }) // 4 = Entregado
                    });
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.error || 'Error al entregar pedido');
                    showMessage(ordersManagementMessage, data.message);
                    fetchReadyOrders(); // Refresca la lista
                } catch (e) {
                    showMessage(ordersManagementMessage, e.message, true);
                }
            };
        });
    }

    // Evento para cargar la sección de manejo de pedidos
    const ordersManagementBtn = document.querySelector('.nav-button[data-target="ordersManagementSection"]');
    if (ordersManagementBtn) {
        ordersManagementBtn.addEventListener('click', fetchReadyOrders);
    }

    // Opcional: cargar automáticamente si la sección está activa al inicio
    if (document.getElementById('ordersManagementSection')?.classList.contains('active')) {
        fetchReadyOrders();
    }

    function showOrderDetailsModal(order) {
        // Construir el HTML del modal con todos los datos
        const modal = document.createElement('div');
        modal.className = 'custom-modal-overlay';
        modal.innerHTML = `
            <div class="custom-modal-content" style="max-width:500px;">
                <h2>Detalle del Pedido #${order.id}</h2>
                <p><strong>Cliente:</strong> ${order.customer_name || 'N/A'}</p>
                <p><strong>Fecha:</strong> ${order.date}</p>
                <p><strong>Mesa:</strong> ${order.table || 'N/A'}</p>
                <p><strong>Estado:</strong> ${order.status}</p>
                <p><strong>Monto:</strong> $${order.total ? parseFloat(order.total).toFixed(2) : 'N/A'}</p>
                <h3>Productos:</h3>
                <ul>
                    ${order.items.map(item => `
                        <li>
                            <strong>${item.product_name}</strong> x${item.quantity}
                            ${item.sugerency ? `<br><em>Preferencias:</em> ${item.sugerency}` : ''}
                        </li>
                    `).join('')}
                </ul>
                <div class="modal-buttons">
                    <button id="closeOrderDetailsBtn" class="modal-button primary">Cerrar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('closeOrderDetailsBtn').onclick = () => {
            document.body.removeChild(modal);
        };
    }
});
