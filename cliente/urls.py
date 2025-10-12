from django.urls import path
from . import views
from cliente import views

app_name = 'cliente'

urlpatterns = [
    # Nueva ruta para la página de clientes 

    path('<int:table>/', views.index, name='index'),  # La raíz de cliente es el index
    path('<int:table>/menu/', views.menu, name='menu'),
    path('<int:table>/ayuda/', views.ayuda, name='ayuda'),
    path('<int:table>/contacto/', views.contacto, name='contacto'),
    path('<int:table>/pagar/', views.pagar, name='pagar'),
    path('<int:table>/carrito/', views.carrito, name='carrito'),
    path('<int:table>/pedido_pagado/', views.pedido_pagado, name='pedido_pagado'),
    path('<int:table>/producto/<int:id>/', views.detalle_producto, name='detalle_producto'),  # Detalle de producto


]