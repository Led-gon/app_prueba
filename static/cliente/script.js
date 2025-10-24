document.addEventListener('DOMContentLoaded', () => {


    // --- Preguntas frecuentes ---

    document.querySelectorAll('.pregunta').forEach(function(pregunta) {
        console.log('Pregunta clickeada');
        pregunta.addEventListener('click', function() {
            const respuesta = pregunta.nextElementSibling;
            if (respuesta && respuesta.classList.contains('respuesta')) {
                respuesta.classList.toggle('abierta');
                const flecha = pregunta.querySelector('.flecha');
                if (flecha) {
                    flecha.classList.toggle('abierta');
                }
            }
        });
    });

    // Oculta todas las respuestas al cargar
    document.querySelectorAll('.respuesta').forEach(function(respuesta) {
        console.log('Preguntas cerradas');
        respuesta.classList.remove('abierta');
    });

    // --- Utilidades de carrito ---
    function cargarCarrito() {
        const carritoGuardado = localStorage.getItem('carrito');
        console.log('Carrito cargado:', carritoGuardado);
        return carritoGuardado ? JSON.parse(carritoGuardado) : [];
    }

    function guardarCarrito(carrito) {
        console.log('Carrito guardado:', carrito);
        localStorage.setItem('carrito', JSON.stringify(carrito));
    }

    function obtenerNumeroMesaDesdeURL() {
        const partes = window.location.pathname.split('/');
        // Busca el primer número en la URL
        for (let i = 0; i < partes.length; i++) {
            if (/^\d+$/.test(partes[i])) {
                return partes[i];
            }
        }
        return null;
    }

    function actualizarVistaProducto(id, cantidad) {
        const botonAgregar = document.querySelector(`.agregar-carrito[data-id="${id}"]`);
        const controlCantidad = document.querySelector(`.control-cantidad[data-id="${id}"]`);
        if (botonAgregar && controlCantidad) {
            if (cantidad > 0) {
                botonAgregar.style.display = 'none';
                controlCantidad.style.display = 'inline-block';
                controlCantidad.querySelector('.cantidad').textContent = cantidad;
                console.log(`Producto ${id} cantidad actualizada a ${cantidad}`);
            } else {
                botonAgregar.style.display = 'inline-block';
                controlCantidad.style.display = 'none';
                console.log(`Producto ${id} removido del carrito`);
            }
        }
    }

    function actualizarCarritoVisual() {
        let carrito = cargarCarrito();
        document.querySelectorAll('#cantidad-items-carrito').forEach(span => {
            span.textContent = carrito.reduce((sum, item) => sum + item.cantidad, 0);
            console.log('Cantidad total en carrito actualizada:', span.textContent);
        });
        // Actualiza cada producto
        document.querySelectorAll('.agregar-carrito').forEach(boton => {
            const id = boton.dataset.id;
            const item = carrito.find(p => p.id == id);
            actualizarVistaProducto(id, item ? item.cantidad : 0);
            console.log(`Vista del producto ${id} actualizada` );
        });
    }

    function agregarAlCarrito(evento) {
        const boton = evento.target.closest('.agregar-carrito');
        const id = boton.dataset.id;
        const nombre = boton.dataset.nombre;
        const precio = parseFloat(boton.dataset.precio);
        console.log(`Agregando al carrito: ${nombre} (ID: ${id}, Precio: ${precio})`);
        let carrito = cargarCarrito();
        let item = carrito.find(p => p.id == id);
        if (item) {
            item.cantidad += 1;
        } else {
            carrito.push({ id, nombre, precio, cantidad: 1, sugerency: '' });
        }
        guardarCarrito(carrito);
        actualizarCarritoVisual();
        console.log(`Producto ${nombre} agregado al carrito.`);
    }

    function cambiarCantidad(evento, delta) {
        const control = evento.target.closest('.control-cantidad');
        const id = control.dataset.id;
        let carrito = cargarCarrito();
        let item = carrito.find(p => p.id == id);
        console.log(`Cambiando cantidad del producto ID ${id} en ${delta}`);
        if (item) {
            item.cantidad += delta;
            if (item.cantidad <= 0) {
                carrito = carrito.filter(p => p.id != id);
            }
            guardarCarrito(carrito);
            actualizarCarritoVisual();
        }
        console.log(`Cantidad del producto ID ${id} actualizada a ${item ? item.cantidad : 0}`);
    }

    // --- Asignar eventos ---
    document.querySelectorAll('.agregar-carrito').forEach(boton => {
        console.log('Asignando evento para agregar al carrito');
        boton.addEventListener('click', agregarAlCarrito);
    });

    document.querySelectorAll('.control-cantidad .mas').forEach(boton => {
        console.log('Asignando evento para aumentar cantidad');
        boton.addEventListener('click', e => cambiarCantidad(e, 1));
    });
    document.querySelectorAll('.control-cantidad .menos').forEach(boton => {
        console.log('Asignando evento para disminuir cantidad');
        boton.addEventListener('click', e => cambiarCantidad(e, -1));
    });

    document.querySelectorAll('.sugerency-input').forEach(input => {
        input.addEventListener('blur', function() {
            let carrito = cargarCarrito();
            let item = carrito.find(p => p.id == this.dataset.id);
            if (item) {
                item.sugerency = this.value;
                guardarCarrito(carrito);
            }
        });
    });

    // --- Mostrar carrito en la página del carrito ---
    function mostrarCarritoEnPagina() {
        const listaCarrito = document.getElementById('lista-de-productos-carrito');
        if (!listaCarrito) return;
        const carrito = cargarCarrito();
        listaCarrito.innerHTML = '';
        let total = 0;
        console.log('Mostrando carrito en la página:', carrito);
        if (carrito.length === 0) {
            listaCarrito.innerHTML = '<p>Tu carrito está vacío.</p>';
            console.log('Carrito vacío');
        } else {
            carrito.forEach(item => {
                const div = document.createElement('div');
                div.classList.add('item-carrito');
                div.innerHTML = `
                    <span>${item.nombre} x ${item.cantidad}</span>
                    <span>$${(item.precio * item.cantidad).toFixed(2)}</span>
                    <input type="text" class="sugerency-input" data-id="${item.id}" placeholder="Preferencias (opcional)" value="${item.sugerency || ''}">
                    <button class="eliminar-item" data-id="${item.id}">Eliminar</button>
                `;
                // Evento para eliminar
                div.querySelector('.eliminar-item').addEventListener('click', function() {
                    mostrarModalEliminar(item.id, item.nombre);
                });
                // Evento para guardar sugerencia
                div.querySelector('.sugerency-input').addEventListener('blur', function() {
                    let carritoActual = cargarCarrito();
                    let itemActual = carritoActual.find(p => p.id == this.dataset.id);
                    if (itemActual) {
                        itemActual.sugerency = this.value;
                        guardarCarrito(carritoActual);
                    }
                });
                listaCarrito.appendChild(div);
                total += item.precio * item.cantidad;
            });
            console.log('Total calculado:', total);
        }
        // Si tienes un elemento para el total, actualízalo aquí
        const totalElement = document.getElementById('total');
        if (totalElement) totalElement.textContent = total.toFixed(2);
        console.log('Total del carrito mostrado en la página:', total.toFixed(2));
    }

    function mostrarModalEliminar(id, nombre) {
    // Si ya existe, elimínalo primero
        const modalExistente = document.getElementById('modal-eliminar-item');
        if (modalExistente) modalExistente.remove();

        const modal = document.createElement('div');
        modal.id = 'modal-eliminar-item';
        modal.style.position = 'fixed';
        modal.style.top = 0;
        modal.style.left = 0;
        modal.style.width = '100vw';
        modal.style.height = '100vh';
        modal.style.background = 'rgba(0,0,0,0.4)';
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.zIndex = 9999;

        modal.innerHTML = `
            <div style="background:#fff;padding:2em 1.5em;border-radius:8px;max-width:320px;text-align:center;">
                <h3>¿Eliminar "${nombre}" del carrito?</h3>
                <div style="margin-top:18px;">
                    <button id="confirmarEliminarItem" style="background:#d9534f;color:#fff;padding:8px 18px;border:none;border-radius:4px;margin-right:10px;cursor:pointer;">Eliminar</button>
                    <button id="cancelarEliminarItem" style="background:#aaa;color:#fff;padding:8px 18px;border:none;border-radius:4px;cursor:pointer;">Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('confirmarEliminarItem').onclick = function() {
            eliminarDelCarrito(id);
            modal.remove();
        };
        document.getElementById('cancelarEliminarItem').onclick = function() {
            modal.remove();
        };
    }

    function eliminarDelCarrito(id) {
        let carrito = cargarCarrito();
        carrito = carrito.filter(item => item.id != id);
        guardarCarrito(carrito);
        mostrarCarritoEnPagina();
        actualizarCarritoVisual();
        console.log(`Producto ID ${id} eliminado del carrito`);
    }


    // --- Inicialización ---
    actualizarCarritoVisual();
    if (document.getElementById('lista-de-productos-carrito')) {
        mostrarCarritoEnPagina();
        
    }

    // --- Botón Ir a Pagar ---
    const irAPagarBoton = document.getElementById('ir-a-pagar');
    if (irAPagarBoton) {
        irAPagarBoton.addEventListener('click', function() {
            const table = obtenerNumeroMesaDesdeURL();
            window.location.href = `/${table}/pagar/`;
        });
    }

    // --- Resumen del Pedido ---
    function mostrarResumenPedido() {
        const lista = document.getElementById('lista-items-pedido');
        const totalSpan = document.getElementById('total-pagar');
        if (!lista || !totalSpan) return;

        const carrito = localStorage.getItem('carrito');
        const items = carrito ? JSON.parse(carrito) : [];
        lista.innerHTML = '';
        let total = 0;

        if (items.length === 0) {
            lista.innerHTML = '<li>Tu carrito está vacío.</li>';
        } else {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = `${item.nombre} x ${item.cantidad} - $${(item.precio * item.cantidad).toFixed(2)}`;
                if (item.sugerency) {
                    li.textContent += ` (Pref: ${item.sugerency})`;
                }
                lista.appendChild(li);
                total += item.precio * item.cantidad;
            });
        }
        totalSpan.textContent = total.toFixed(2);
    }

    if (document.getElementById('lista-items-pedido')) {
        mostrarResumenPedido();
    }


    // MODAL de confirmación
    const modal = document.getElementById('modal-confirmacion-pago');
    const btnConfirmar = document.getElementById('btn-confirmar-pago');
    const btnCancelar = document.getElementById('btn-cancelar-pago');
    const formPago = document.getElementById('formulario-pago');

    if (formPago && modal && btnConfirmar && btnCancelar) {
        formPago.addEventListener('submit', function(e) {
            e.preventDefault();
            modal.style.display = 'flex';
        });

        btnCancelar.onclick = function() {
            modal.style.display = 'none';
        };

        btnConfirmar.onclick = function() {
            modal.style.display = 'none';

            // Recopilar datos del formulario
            const nombre = document.getElementById('nombre').value;
            const email = document.getElementById('email').value;
            const dni = document.getElementById('dni') ? document.getElementById('dni').value : '';
            const table = obtenerNumeroMesaDesdeURL();
            const carrito = JSON.parse(localStorage.getItem('carrito') || '[]');
            if (carrito.length === 0) {
                alert('El carrito está vacío.');
                return;
            }
        
            // Obtener IP pública
            fetch('https://api.ipify.org?format=json')
            .then(res => res.json())
            .then(ipData => {
                const ip = ipData.ip || '';
            
                // 1. Guardar la orden en el backend
                fetch('/caja/api/guardar_pedido_cliente/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        carrito: carrito,
                        nombre: nombre,
                        email: email,
                        ip: ip,
                        table: table
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.order_id) {
                        localStorage.removeItem('carrito');
                        localStorage.setItem('ultimo_pedido_id', data.order_id);
                    
                        // 2. Crear preferencia de pago en el backend
                        fetch('/caja/api/payments/create/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                order_id: data.order_id,
                                return_url: window.location.origin + `/${table}/pedido_pagado/`
                            })
                        })
                        .then(res => res.json())
                        .then(payData => {
                            if (payData.success && payData.init_point) {
                                window.location.href = payData.init_point;
                            } else {
                                alert('Error al crear el pago: ' + (payData.error || ''));
                                window.location.href = `/${table}/pedido_pagado/`;
                            }
                        })
                        .catch(err => {
                            alert('Error de red al crear el pago: ' + err);
                            window.location.href = `/${table}/pedido_pagado/`;
                        });
                    } else {
                        alert('Error al guardar el pedido: ' + (data.error || ''));
                    }
                })
                .catch(err => {
                    alert('Error de red: ' + err);
                });
            });
        };
    }

    // Mostrar número de pedido en pedido_pagado.html
    if (document.getElementById('numero-pedido')) {
        const pedidoId = localStorage.getItem('ultimo_pedido_id');
        if (pedidoId) {
            document.getElementById('numero-pedido').textContent = pedidoId;
            localStorage.removeItem('ultimo_pedido_id');
        }
    }

    const botones = document.querySelectorAll(".filtro");
    const secciones = document.querySelectorAll(".categoria");

    botones.forEach(boton => {
        boton.addEventListener("click", function() {
            const cat = this.getAttribute("data-cat");

             // Quita la clase active de todos los botones
             botones.forEach(b => b.classList.remove("active"));
             // Activa solo el botón seleccionado
             this.classList.add("active");

            // manejar estilo activo multiple seleccion
            /*
            if (cat === "all") {
                botones.forEach(b => b.classList.remove("active"));
                this.classList.add("active");
            } else {
                document.querySelector(".filtro[data-cat='all']").classList.remove("active");
                this.classList.toggle("active");
            }

            // categorías seleccionadas
            const seleccionadas = Array.from(botones)
                .filter(b => b.classList.contains("active") && b.getAttribute("data-cat") !== "all")
                .map(b => b.getAttribute("data-cat"));
            */

            /*if (seleccionadas.length === 0 || cat === "all") */
            if (cat === "all") {
                // mostrar todas las categorias
                secciones.forEach(sec => sec.style.display = "block");
                //document.querySelector(".filtro[data-cat='all']").classList.add("active");
            } else {
                // mostrar solo las categorias seleccionadas
                secciones.forEach(sec => {
                    sec.style.display = (sec.id === cat) ? "block" : "none";
                    //sec.style.display = seleccionadas.includes(sec.id) ? "block" : "none";
                });
            }
        });
    });

document.querySelectorAll('.plato-item').forEach(plato => {
    const desc = plato.querySelector('.descripcion');
    const verMas = plato.querySelector('.ver-mas');

    if (!desc || !verMas) return;

    const lineHeight = parseFloat(getComputedStyle(desc).lineHeight);
    const maxLines = 3;
    const maxHeight = lineHeight * maxLines;

    // Mostrar/ver-más solo si realmente se corta
    if (desc.scrollHeight > maxHeight + 1) { // +1 para evitar errores de redondeo
        verMas.style.display = 'inline';
        verMas.textContent = 'Ver más';
        verMas.addEventListener('click', () => {
            const isExpanded = desc.classList.toggle('expandida');
            verMas.textContent = isExpanded ? 'Ver menos' : 'Ver más';
        });
    } else {
        verMas.style.display = 'none';
    }
});
const formContacto = document.getElementById('form-contacto');

if (formContacto) {
    formContacto.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Creamos un FormData del form
        const formData = new FormData(formContacto);

        // Obtenemos el CSRF token del input oculto que Django genera
        const csrfToken = formData.get('csrfmiddlewaretoken');

        try {
            const resp = await fetch(formContacto.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData  // enviamos como FormData, no JSON
            });

            if (!resp.ok) throw new Error('Error en la petición');

            const result = await resp.json();

            if (result.success) {
                alert('✅ ¡Mensaje enviado con éxito!');
                formContacto.reset();
            } else {
                alert('❌ Error al enviar el mensaje.');
            }

        } catch (err) {
            alert('⚠️ Error de red: ' + err.message);
        }
    });
}

const paymentResult = document.getElementById('payment-result');
if (paymentResult) {
    // Obtener parámetros de URL
    const urlParams = new URLSearchParams(window.location.search);
    const status = urlParams.get('status');
    const payment_id = urlParams.get('payment_id');
    const external_reference = urlParams.get('external_reference');

    // Notificar al backend
    if (status) {
        fetch('/caja/api/payments/process_result/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                payment_id: payment_id || 'unknown',
                status: status,
                order_id: external_reference || localStorage.getItem('ultimo_pedido_id')
            })
        })
        .then(response => response.json())
        .then(data => {
            let message = '';
            if (data.success) {
                if (data.status === 'approved') {
                    message = `<h2>¡Pago completado!</h2>
                        <p>Tu pedido está siendo preparado.</p>
                        <p>Número de Pedido: <strong>${data.order_id || external_reference}</strong></p>`;
                    localStorage.removeItem('carrito');
                } else if (data.status === 'in_process') {
                    message = `<h2>Pago pendiente</h2>
                        <p>Tu pedido será procesado una vez confirmado el pago.</p>
                        <p>Número de Pedido: <strong>${data.order_id || external_reference}</strong></p>
                        <p>Recibirás un correo electrónico con los detalles de tu pedido.</p>`;
                } else {
                    message = `<h2>Pago rechazado</h2>
                        <p>Por favor, intenta nuevamente con otro método de pago.</p>
                    <p>Número de Pedido: <strong>${data.order_id || external_reference}</strong></p>`;
                }
            } else {
                message = `<h2>Error</h2>
                    <p>Hubo un problema procesando tu pago. Por favor, contacta a soporte.</p>`;
            }
            paymentResult.innerHTML = message;
        })
        .catch(error => {
            console.error('Error:', error);
            paymentResult.innerHTML = `<h2>Error de conexión</h2>
                <p>No pudimos verificar el estado de tu pago.</p>`;
        });
    }
}
});
