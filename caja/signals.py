from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    order = instance.order
    total = sum(item.subtotal for item in order.order_items.all())
    order.amount = total
    order.save()