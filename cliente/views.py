from django.shortcuts import render, redirect, get_object_or_404
from caja.models import Product, Category
from collections import defaultdict
import random

#--- Vistas para Clientes (Frontend) ---

def index(request, table):
    destacados = Product.objects.filter(active=True).order_by('?')[:8]
    return render(request, 'cliente/index.html', {'table': table, 'destacados': destacados})

def menu(request, table):
    categorias = Category.objects.all()
    categorias_con_productos = []
    for categoria in categorias:
        productos = Product.objects.filter(idCategoria=categoria, active=True, stock__gt=0)
        if productos.exists():
            categorias_con_productos.append((categoria, productos))
    return render(request, 'cliente/menu.html', {'table': table, 'categorias_con_productos': categorias_con_productos})

def ayuda(request, table):
    return render(request,'cliente/ayuda.html', {'table': table})

def contacto(request, table):
    return render(request,'cliente/contacto.html', {'table': table})

def pagar(request, table):
    return render(request,'cliente/pagar.html', {'table': table})

def carrito(request, table):
    return render(request,'cliente/carrito.html', {'table': table})

def pedido_pagado(request, table):
    return render(request,'cliente/pedido_pagado.html', {'table': table})


def detalle_producto(request, table, id):
    producto = get_object_or_404(Product, id=id)
    return render(request, 'cliente/detalle_producto.html', {'table': table, 'producto': producto})
