from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from caja.models import Order, State

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
    # Obtener pedidos en preparación y ordenarlos por mesa y tiempo
    orders = Order.objects.filter(status_id=PREPARACION_STATE_ID).order_by('tableNumber', 'initialTime')
    
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
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status_id != PREPARACION_STATE_ID:
        messages.error(request, 'Este pedido no está en preparación.')
        return redirect('cocina:dashboard')
    order.status_id = LISTO_STATE_ID
    order.save()
    messages.success(request, f'Pedido {order.id} marcado como listo para entregar.')
    return redirect('cocina:dashboard')
