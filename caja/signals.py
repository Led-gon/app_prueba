from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem
from .models import Order

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    order = instance.order
    total = sum(item.subtotal for item in order.order_items.all())
    order.amount = total
    order.save()

@receiver(pre_save, sender=Order)
def notificar_cambio_estado(sender, instance, **kwargs):
    """Envía un mail automático al cliente cuando el estado del pedido cambia."""
    print(f"pk: {instance.pk}")

    if not instance.pk:
            cliente = instance.customer_name or "Cliente"
            asunto = f"Tu pedido está pendiente de pago⏳"

            mensaje_html = f"""
            <h2 style="color:#2980b9;">Pedido en espera ⏳</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido fue recibido y está <strong>pendiente de pago</strong>.</p>
            <p>Si queres reanudarlo, acercate al mostrador del local.</p>
            <p>Una vez confirmado el pago, comenzaremos la preparación.</p>
            <p>Gracias,<br>El equipo de <strong>Shatalito</strong> 🍽️</p>
            """
            destinatario = [instance.customer_email]
            email = EmailMultiAlternatives(asunto, '', settings.DEFAULT_FROM_EMAIL, destinatario)
            email.attach_alternative(mensaje_html, "text/html")
            email.send(fail_silently=True)
    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    print(f"status1: {old_order.status}")
    print(f"status2: {instance.status}")

    if old_order.status != instance.status:
        # Datos base
        cliente = instance.customer_name or "Cliente"
        estado = instance.status.name
        productos = instance.order_items.all()
        print(f"estado: {estado.lower}")

        # Contenido según estado
        if estado.lower() == "cancelado":
            asunto = f"Tu pedido #{instance.id} fue cancelado"
            mensaje_html = f"""
            <h2 style="color:#c0392b;">Pedido cancelado ❌</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> ha sido <strong>cancelado</strong>.</p>
            <p>Gracias,<br>El equipo de <strong>Shatalito</strong> 🍽️</p>
            """

        elif estado.lower() == "pendiente":
            asunto = f"Tu pedido #{instance.id} está pendiente de pago⏳"
            lista_productos = "".join([
                f"<li>{item.quantity} x {item.product.name}</li>"
                for item in productos
            ])
            mensaje_html = f"""
            <h2 style="color:#2980b9;">Pedido en espera ⏳</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> fue recibido y está <strong>pendiente de pago</strong>.</p>
            <p><strong>Detalle del pedido:</strong></p>
            <ul>{lista_productos}</ul>
            <p>Si queres reanudarlo, acercate al mostrador del local.</p>
            <p>Una vez confirmado el pago, comenzaremos la preparación.</p>
            <p>Gracias,<br>El equipo de <strong>Shatalito</strong> 🍽️</p>
            """

        elif estado.lower() == "en espera":
            asunto = f"Tu pedido #{instance.id} esta en espera de preparacion."
            lista_productos = "".join([
                f"<li>{item.quantity} x {item.product.name}</li>"
                for item in productos
            ])
            mensaje_html = f"""
            <h2 style="color:#2980b9;">¡Pedido en espera de preparación! 👨‍🍳</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> fue <strong>pagado exitosamente</strong> y está en espera para ser preparado por nuestro equipo.</p>
            <p><strong>Detalle del pedido:</strong></p>
            <ul>{lista_productos}</ul>
            <p>Te avisaremos cuando el pedido comienze a ser preparado.</p>
            <p>Gracias por tu compra en <strong>Shatalito</strong> 🍔🥗</p>
            """

        elif estado.lower() == "en preparación":
            asunto = f"Tu pedido #{instance.id} está siendo preparado 👨‍🍳"
            lista_productos = "".join([
                f"<li>{item.quantity} x {item.product.name}</li>"
                for item in productos
            ])
            mensaje_html = f"""
            <h2 style="color:#2980b9;">¡Pedido en preparación! 👨‍🍳</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> está siendo preparado por nuestro equipo.</p>
            <p><strong>Detalle del pedido:</strong></p>
            <ul>{lista_productos}</ul>
            <p>Te avisaremos cuando esté listo para entregar.</p>
            <p>Gracias por tu compra en <strong>Shatalito</strong> 🍔🥗</p>
            """

        elif estado.lower() == "listo para entregar":
            asunto = f"Tu pedido #{instance.id} ya está listo para entregar 🚀"
            lista_productos = "".join([
                f"<li>{item.quantity} x {item.product.name}</li>"
                for item in productos
            ])
            mensaje_html = f"""
            <h2 style="color:#27ae60;">¡Pedido listo para entregar! ✅</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> ya está <strong>listo para ser entregado</strong>.</p>
            <p><strong>Detalle del pedido:</strong></p>
            <ul>{lista_productos}</ul>
            <p>En la brevedad estaras recibiendo tu pedido.</p>
            <p>¡Gracias por elegir <strong>Shatalito</strong>! 😄</p>
            """

        else:
            asunto = f"Actualización de tu pedido #{instance.id}"
            mensaje_html = f"""
            <h2 style="color:#8e44ad;">Actualización de pedido</h2>
            <p>Hola {cliente},</p>
            <p>Tu pedido <strong>#{instance.id}</strong> cambió de estado a <strong>{estado}</strong>.</p>
            <p>Gracias por elegir <strong>Shatalito</strong> 🍽️</p>
            """

        # Envío del correo (HTML)
        destinatario = [instance.customer_email]
        email = EmailMultiAlternatives(asunto, '', settings.DEFAULT_FROM_EMAIL, destinatario)
        email.attach_alternative(mensaje_html, "text/html")
        email.send(fail_silently=True)
    else:  return
    
