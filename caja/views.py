from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db import IntegrityError
import json
import re
from decimal import Decimal

from .services import PaymentService
import json

from .models import CustomUser, Product, Order, OrderItem, State

# --- Decorador de Rol (revisado para Django) ---
def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    def decorator(view_func):
        @login_required(login_url='caja:login')
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('caja:login') 
            if request.user.role not in allowed_roles:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Forbidden: Insufficient permissions'}, status=403)
                return redirect('caja:determine_dashboard') 
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# --- Función de validación de contraseña ---
def validate_password_requirements(password):
    """
    Valida que la contraseña cumpla con los requisitos de seguridad.
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos un número
    - Al menos un carácter especial (no alfanumérico)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): # Caracteres especiales comunes
        return False, "La contraseña debe contener al menos un carácter especial."
    return True, "" # La contraseña es válida

# --- Vistas de Autenticación y Navegación ---
@ensure_csrf_cookie 
def login_view(request):
    if request.user.is_authenticated:
        return redirect('caja:determine_dashboard')
    
    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                redirect_url = ''
                if user.role == 'cocinero':
                    redirect_url = reverse('cocina:dashboard')
                elif user.role in ['Empleado', 'Administrador', 'Super Usuario']:
                    redirect_url = reverse('caja:dashboard')
                else:
                    redirect_url = reverse('cliente:index')

                return JsonResponse({
                    'message': 'Login successful', 
                    'role': user.role, 
                    'username': user.username, 
                    'redirect_url': redirect_url
                })
            else:
                return JsonResponse({'error': 'Usuario o contraseña inválidos'}, status=401)
    return render(request, 'caja/login.html')

@login_required(login_url='caja:login')
def logout_view(request):
    auth_logout(request)
    return redirect('caja:login')

@login_required(login_url='caja:login')
def determine_dashboard_view(request):
    user = request.user
    if user.role in ['Empleado', 'Administrador', 'Super Usuario']:
        return redirect('caja:dashboard')
    auth_logout(request)
    return redirect('caja:login')

# --- Vistas de Dashboard ---

@login_required(login_url='caja:login')
@role_required(allowed_roles=['Empleado', 'Administrador', 'Super Usuario'])
def dashboard_view(request):
    role = request.user.role
    sections = {
        'orders': role in ['Empleado', 'Administrador', 'Super Usuario'],
        'orders_management': role in ['Empleado'],
        'products': role in ['Administrador', 'Super Usuario'],
        'users': role in ['Super Usuario'],
    }
    return render(request, 'caja/admin_dashboard.html', {
        'user': request.user,
        'sections': sections,
        'role': role
    })


# --- API Endpoints ---

@login_required(login_url='caja:login')
def api_session_status(request):
    return JsonResponse({
        "logged_in": True, 
        "username": request.user.username,
        "role": request.user.role
    })


@login_required(login_url='caja:login')
def api_orders_list_create(request):
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        date_filter_str = request.GET.get('date')
        
        orders_qs = Order.objects.select_related('status').prefetch_related('order_items__product').order_by('-order_date', 'id', )

        if date_filter_str:
            parsed_date = parse_date(date_filter_str)
            if parsed_date: 
                orders_qs = orders_qs.filter(order_date=parsed_date)
            else: 
                return JsonResponse({"error": "Formato de fecha inválido."}, status=400)
        
        if status_filter: 
            orders_qs = orders_qs.filter(status_id=status_filter) 

        orders_data = [{
            "id": order.id,
            "customer_name": order.customer_name,
            "date": order.order_date.strftime('%Y-%m-%d'),
            "status": order.status.name,  
            "total": float(order.amount),
            "table": order.tableNumber,
            "items": [
                {
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "sugerency": item.sugerency
                }
                for item in order.order_items.all()
            ]
        } for order in orders_qs]
        return JsonResponse(orders_data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name', '').strip()
            table_number = data.get('table_number')
            if not table_number or not isinstance(table_number, (int, float)):
                return JsonResponse({'error': 'Número de mesa es requerido y debe ser un número.'}, status=400)

            order = Order.objects.create(customer_name=customer_name, tableNumber=table_number)
            return JsonResponse({
                'message': 'Pedido creado', 
                'order_id': order.id, 
                'customer_name': order.customer_name,
                'table_number': order.tableNumber
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON Inválido'}, status=400)
        except IntegrityError:
            return JsonResponse({'error': 'Error de base de datos, posible duplicado.'}, status=409)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required(login_url='caja:login')
@role_required(allowed_roles=['Empleado', 'Administrador', 'Super Usuario'])
def api_order_detail_update_delete(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == 'GET': 
        order_data = {
            "id": order.id, "customer_name": order.customer_name,
            "date": order.order_date.strftime('%Y-%m-%d'), "status": order.status.name, 
            "total": float(order.amount),
            "items": [{"product_name": item.product.name, "quantity": item.quantity, "sugerency": item.sugerency, "price": float(item.price)} for item in order.order_items.all()]
        }
        return JsonResponse(order_data)

    elif request.method == 'PUT': 
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            if new_status:
                try:
                    new_state = State.objects.get(pk=new_status)
                    order.status = new_state
                    order.save()
                    return JsonResponse({'message': f'Pedido {order_id} actualizado a {new_status}', 'status': order.status.name})
                except State.DoesNotExist:
                    return JsonResponse({'error': 'Estado inválido o faltante'}, status=400)
            return JsonResponse({'error': 'Estado inválido o faltante'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON Inválido'}, status=400)

    elif request.method == 'DELETE': 
        try:
            cancelled_state = State.objects.get(name='Cancelado') 
            order.status = cancelled_state
            order.save()
            return JsonResponse({'message': f'Pedido {order_id} cancelado', 'status': order.status.name})
        except State.DoesNotExist:
            return JsonResponse({'error': 'El estado "Cancelado" no existe en la base de datos. Por favor, créalo.'}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='caja:login')
@role_required(allowed_roles=['Administrador', 'Super Usuario'])
def api_products_list_create(request):
    if request.method == 'GET':
        from collections import defaultdict
        grouped = defaultdict(list)
        products = Product.objects.select_related('idCategoria').all().order_by('id')
        for p in products:
            categoria = p.idCategoria.name if p.idCategoria else "Sin categoría"
            grouped[categoria].append({
                "id": p.id,
                "name": p.name,
                "categoria": categoria,
                "price": float(p.price),
                "stock": p.stock,
            })
        return JsonResponse(dict(grouped), safe=False)
    
    elif request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price_str = request.POST.get('price')
            stock_str = request.POST.get('stock')
            category_id = request.POST.get('category')
            image_file = request.FILES.get('image')  # aquí viene la imagen

            if not name or price_str is None or stock_str is None or category_id is None:
                return JsonResponse({'error': 'Nombre, precio, stock y categoria son requeridos'}, status=400)
            
            try:
                price = Decimal(price_str)
                stock = int(stock_str)
                if price <= 0 or stock < 0:
                    raise ValueError("Precio debe ser positivo y stock no negativo.")
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Precio o stock inválido.'}, status=400)

            if Product.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': f"Producto '{name}' ya existe."}, status=409)

            product = Product.objects.create(name=name, description=description, price=price, stock=stock, idCategoria_id=int(category_id), image=image_file)
            return JsonResponse({
                'message': 'Producto añadido', 
                'product': {"id": product.id, "name": product.name, "description": product.description, "price": float(product.price), "stock": product.stock, "idCategory": product.idCategoria.id, "image": product.image.url if product.image else None}
            }, status=201)
        except json.JSONDecodeError: return JsonResponse({'error': 'JSON Inválido'}, status=400)
        except IntegrityError: return JsonResponse({'error': 'Error de base de datos, posible duplicado.'}, status=409)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='caja:login')
@role_required(allowed_roles=['Administrador', 'Super Usuario'])
def api_get_product_by_name(request):
    name_query = request.GET.get('name')
    if not name_query:
        return JsonResponse({"error": "Parámetro 'name' requerido"}, status=400)
    try:
        product = Product.objects.get(name__iexact=name_query)
        return JsonResponse({"id": product.id, "name": product.name, "price": float(product.price), "stock": product.stock})
    except Product.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)


@login_required(login_url='caja:login')
@role_required(allowed_roles=['Administrador', 'Super Usuario'])
def api_update_product_stock(request, product_id):
    if request.method == 'PUT':
        product = get_object_or_404(Product, pk=product_id)
        try:
            data = json.loads(request.body)
            new_stock_str = data.get('stock')
            if new_stock_str is None:
                return JsonResponse({'error': 'Valor de stock faltante'}, status=400)
            new_stock = int(new_stock_str)
            if new_stock >= 0:
                product.stock = new_stock
                product.save()
                return JsonResponse({'message': 'Stock actualizado', 'product': {"id": product.id, "name": product.name, "stock": product.stock}})
            return JsonResponse({'error': 'Stock debe ser no-negativo'}, status=400)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Dato de stock inválido'}, status=400)
    return JsonResponse({'error': 'Solo método PUT permitido'}, status=405)

# --- APIs de Super Usuario (CRUD de Usuarios) ---
@login_required(login_url='caja:login')
@role_required(allowed_roles=['Super Usuario'])
def api_superuser_users_list_create(request):
    if request.method == 'GET':
        # FILTRO AGREGADO: Solo usuarios activos (is_active=True)
        users = CustomUser.objects.filter(is_active=True).order_by('username')
        data = [{"username": u.username, "email": u.email, "role": u.role, "first_name": u.first_name, "last_name": u.last_name} for u in users]
        return JsonResponse(data, safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            role = data.get('role')
            email = data.get('email', '')

            if not all([username, password, role]):
                return JsonResponse({'error': 'Username, password y role son requeridos'}, status=400)
            
            is_valid, error_message = validate_password_requirements(password)
            if not is_valid:
                return JsonResponse({'error': error_message}, status=400)

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username ya existe'}, status=409)
            if role not in [choice[0] for choice in CustomUser.ROLE_CHOICES]: 
                return JsonResponse({'error': 'Rol inválido'}, status=400)
            
            # Al crear un usuario, por defecto es activo
            user = CustomUser.objects.create_user(username=username, password=password, email=email, role=role, is_active=True)
            return JsonResponse({'message': f'Usuario {user.username} creado', 'username': user.username, 'role': user.role}, status=201)
        except (json.JSONDecodeError, IntegrityError) as e:
            return JsonResponse({'error': f'Datos inválidos o error: {str(e)}'}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required(login_url='caja:login')
@role_required(allowed_roles=['Super Usuario'])
def api_superuser_modify_user(request, username):
    user = get_object_or_404(CustomUser, username=username)
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            updated_fields = []
            
            # Actualizar rol
            if 'role' in data and data['role']: 
                if data['role'] in [choice[0] for choice in CustomUser.ROLE_CHOICES]: 
                    user.role = data['role']
                    updated_fields.append('role')
                else:
                    return JsonResponse({'error': 'Rol inválido especificado'}, status=400)

            # Actualizar contraseña
            if 'password' in data and data['password']: 
                new_password = data['password']
                is_valid, error_message = validate_password_requirements(new_password)
                if not is_valid:
                    return JsonResponse({'error': error_message}, status=400)
                user.set_password(new_password)
                updated_fields.append('password (changed)')

            # Permitir activar/desactivar el usuario lógicamente
            if 'is_active' in data: # Verificar si 'is_active' fue enviado en el payload
                # Convertir el valor a booleano de forma segura
                new_is_active = bool(data['is_active'])
                
                # Impedir que un Super Usuario se desactive a sí mismo (opcional, pero buena práctica)
                if user.username == request.user.username and not new_is_active:
                    return JsonResponse({'error': 'Un Super Usuario no puede desactivarse a sí mismo.'}, status=403)
                
                user.is_active = new_is_active
                updated_fields.append('is_active')
            
            if not updated_fields:
                return JsonResponse({'error': 'No se proveyeron campos válidos para actualizar'}, status=400)
            
            user.save() 
            return JsonResponse({'message': f'Usuario {username} actualizado ({", ".join(updated_fields)})'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON Inválido'}, status=400)
    elif request.method == 'DELETE':
        # CAMBIADO: Implementación de baja lógica
        if user.role == 'Super Usuario' and user.username == request.user.username:
            return JsonResponse({'error': 'Un Super Usuario no puede eliminarse a sí mismo lógicamente.'}, status=403)
        elif user.role == 'Super Usuario':
            return JsonResponse({'error': 'No se puede eliminar un Super Usuario.'}, status=403) # Impedir eliminar otros Super Usuarios
        
        user.is_active = False # Baja lógica
        user.save()
        return JsonResponse({'message': f'Usuario {username} deshabilitado correctamente (baja lógica).'})
    return JsonResponse({'error': 'Solo métodos PUT y DELETE permitidos'}, status=405)

@csrf_exempt
def api_guardar_pedido_cliente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito = data.get('carrito', [])
            nombre = data.get('nombre')
            email = data.get('email')
            dni = data.get('dni')
            sugerency = data.get('sugerency', '')
            ip = data.get('ip', '')
            table_number = data.get('table', 0)

            if not carrito or not nombre or not email:
                return JsonResponse({'error': 'Datos incompletos'}, status=400)

            estado = State.objects.first()
            order = Order.objects.create(
                customer_name=nombre,
                amount=0,
                status=estado,
                IP=ip,
                initialTime=timezone.now(),
                order_date=timezone.now().date(),
                tableNumber=table_number
            )

            total = 0
            for item in carrito:
                producto = Product.objects.get(pk=item['id'])
                cantidad = int(item['cantidad'])
                precio = float(producto.price)
                subtotal = cantidad * precio
                sugerency = item.get('sugerency', '')
                OrderItem.objects.create(
                    product=producto,
                    order=order,
                    quantity=cantidad,
                    price=precio,
                    subtotal=subtotal,
                    sugerency=sugerency
                )
                total += subtotal

            order.amount = total
            order.save()

            return JsonResponse({'success': True, 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

######################################################
#               Procesamiento de pagos
#
######################################################

@require_http_methods(["POST"])
@csrf_exempt
def create_payment(request):
    """Endpoint para crear un pago desde el frontend"""
    data = json.loads(request.body)
    order_id = data.get('order_id')
    return_url = data.get('return_url')
    print("Received create_payment request with data:", data)  # Debug log
    print("Order ID:", order_id, "Return URL:", return_url)  # Debug log
    
    if not order_id or not return_url:
        return JsonResponse({"success": False, "error": "Missing required parameters"}, status=400)
    
    result = PaymentService.create_payment_preference(order_id, return_url)
    return JsonResponse(result)

@require_http_methods(["POST"])
@csrf_exempt
def process_payment_result(request):
    """Endpoint para procesar el resultado del pago"""
    data = json.loads(request.body)
    payment_id = data.get('payment_id')
    status = data.get('status')
    order_id = data.get('order_id')
    
    result = PaymentService.process_payment_result(payment_id, status, order_id)
    return JsonResponse(result)

@csrf_exempt
def mercadopago_webhook(request):
    if request.method == 'POST':
        notification = request.POST or json.loads(request.body)
        topic = notification.get('topic') or notification.get('type')
        payment_id = notification.get('data.id') or notification.get('id') or notification.get('payment_id')
    elif request.method == 'GET':
        topic = request.GET.get('topic')
        payment_id = request.GET.get('id')
    else:
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    if topic == 'payment' and payment_id:
        import mercadopago
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(payment_id)
        payment_data = payment_info.get("response", {})
        mp_status = payment_data.get("status", "pending")
        external_reference = payment_data.get("external_reference")

        # Actualiza el estado de la orden y el pago
        from caja.models import Order, Payment, PaymentMethod, PaymentStatus
        try:
            order = Order.objects.get(id=external_reference)
            status_mapping = {
                "approved": "Aprobado",
                "in_process": "Pendiente",
                "rejected": "Rechazado",
                "cancelled": "Cancelado"
            }
            mapped_status = status_mapping.get(mp_status, "Pendiente")
            payment_method = PaymentMethod.objects.get(name='Mercado Pago')
            payment_status = PaymentStatus.objects.get(name=mapped_status)
            Payment.objects.create(
                idOrder=order,
                idPaymentMethod=payment_method,
                amount=order.amount,
                idPaymentStatus=payment_status,
                token=str(payment_id)
            )
            # Actualiza el estado de la orden
            if mp_status == "approved":
                order.status_id = 2  # En Preparación
            elif mp_status == "in_process":
                order.status_id = 1  # Pendiente
            elif mp_status in ["rejected", "cancelled"]:
                order.status_id = 5  # Cancelado
            order.save()
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Datos insuficientes"}, status=400)