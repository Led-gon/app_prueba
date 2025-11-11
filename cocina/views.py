from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from caja.models import Order, State
from django.db.models import Min

EN_ESPERA_STATE_ID = 2  # "En espera"
PREPARACION_STATE_ID = 3  # "En Preparación"
LISTO_STATE_ID = 4  # "Listo para Entregar"

from django.contrib.auth.models import Group
import logging
logger = logging.getLogger(__name__)
def chef_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning("User not authenticated")
            return HttpResponseForbidden("No autenticado.")
        groups = request.user.groups.all()
        logger.info(f"User {request.user.username} groups: {[g.name for g in groups]}")
        if not request.user.groups.filter(name='Cocineros').exists():
            logger.warning(f"User {request.user.username} not in Cocineros group")
            return HttpResponseForbidden("Acceso denegado. Solo cocineros pueden acceder.")
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@chef_required
def dashboard(request):
    # Obtener pedidos en espera o en preparación, y ordenarlos por mesa y tiempo
    orders = Order.objects.filter(status__id__in=[EN_ESPERA_STATE_ID, PREPARACION_STATE_ID]).order_by('tableNumber', 'initialTime')
    
    # Agrupar pedidos por mesa
    orders_by_table = {}
    for order in orders:
        table_num = int(order.tableNumber)
        if table_num not in orders_by_table:
            orders_by_table[table_num] = []
        orders_by_table[table_num].append(order)
    
    context = {
        'orders_by_table': orders_by_table
    }
    return render(request, 'cocina/dashboard.html', context)

@login_required
@chef_required
def get_active_tables(request):
    # Obtener todas las órdenes activas
    active_orders = Order.objects.filter(status__id__in=[EN_ESPERA_STATE_ID, PREPARACION_STATE_ID])

    # Agrupar por número de mesa y obtener el tiempo inicial más antiguo para cada una
    tables = active_orders.values('tableNumber').annotate(oldest_order_time=Min('initialTime')).order_by('oldest_order_time')

    table_data = []
    for table in tables:
        table_num = table['tableNumber']
        # Verificar si alguna orden de esta mesa está 'En espera'
        has_pending = active_orders.filter(tableNumber=table_num, status_id=EN_ESPERA_STATE_ID).exists()
        
        status_color = 'amarillo' if has_pending else 'celeste'
        
        table_data.append({
            'table_number': table_num,
            'status': status_color,
        })

    return JsonResponse(table_data, safe=False)

@login_required
@chef_required
def get_orders_for_table(request, table_num):
    orders = Order.objects.filter(
        tableNumber=table_num,
        status__id__in=[EN_ESPERA_STATE_ID, PREPARACION_STATE_ID]
    ).order_by('initialTime')

    orders_data = []
    for order in orders:
        items_data = [{
            'quantity': item.quantity,
            'product_name': item.product.name,
            'sugerency': item.sugerency
        } for item in order.order_items.all()]

        orders_data.append({
            'id': order.id,
            'status': order.status.name,
            'initial_time': order.initialTime.strftime('%H:%M del %d/%m'),
            'items': items_data,
        })
    
    return JsonResponse(orders_data, safe=False)

@login_required
@chef_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        if order.status.id == EN_ESPERA_STATE_ID:
            order.status_id = PREPARACION_STATE_ID
            order.save()
            return JsonResponse({'success': True, 'message': f'Pedido {order.id} ahora en preparación.'})
        elif order.status.id == PREPARACION_STATE_ID:
            order.status_id = LISTO_STATE_ID
            order.save()
            return JsonResponse({'success': True, 'message': f'Pedido {order.id} marcado como listo.'})
        else:
            return JsonResponse({'success': False, 'message': 'El estado del pedido no se puede cambiar.'}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

@login_required
@chef_required
def update_order_status_redirect(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.status.id == EN_ESPERA_STATE_ID:
        order.status_id = PREPARACION_STATE_ID
        order.save()
        messages.success(request, f'Pedido {order.id} ahora en preparación.')
    elif order.status.id == PREPARACION_STATE_ID:
        order.status_id = LISTO_STATE_ID
        order.save()
        messages.success(request, f'Pedido {order.id} marcado como listo para entregar.')
    else:
        messages.warning(request, f'El estado del pedido {order.id} no se puede cambiar desde esta vista.')
        
    return redirect('cocina:dashboard')
