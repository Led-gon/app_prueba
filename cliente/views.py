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

import threading
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.conf import settings

def enviar_mail_async(mail):
    """
    Envía el mail en segundo plano.
    """
    try:
        mail.send(fail_silently=False)
    except Exception as e:
        # Aquí podrías loguear el error si querés
        print("Error al enviar mail en segundo plano:", e)

def enviar_contacto(request, table):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        telefono = request.POST.get("telefono")
        motivo = request.POST.get("motivo")
        mensaje = request.POST.get("mensaje")
        acepta_novedades = request.POST.get("acepta_novedades")
        acepta_politica = request.POST.get("acepta_politica")

        if not acepta_politica:
            return JsonResponse({"success": False, "error": "Debe aceptar la política de privacidad"})

        try:
            cuerpo = f"""
            Nuevo contacto: {motivo}

            Nombre: {nombre}
            Email: {email}
            Teléfono: {telefono}
            Mensaje: {mensaje}
            Acepta novedades: {'Sí' if acepta_novedades else 'No'}
            """

            mail = EmailMessage(
                subject=f"Nuevo contacto: {motivo}",
                body=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.EMAIL_TO],   # o lista de destinatarios
                reply_to=[email],         # permite responder directamente al cliente
            )
            threading.Thread(target=enviar_mail_async, args=(mail,)).start()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})

