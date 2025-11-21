from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from caja.models import Order, State

class Command(BaseCommand):
    help = 'Cancela pedidos en estado "Pendiente" con más de 15 minutos desde initialTime y devuelve stock'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=15)
        pending_qs = State.objects.filter(name__iexact='pendiente')
        if not pending_qs.exists():
            self.stdout.write(self.style.WARNING("No existe estado 'Pendiente'"))
            return
        pending_state = pending_qs.first()

        cancel_qs = State.objects.filter(name__iexact='cancelado')
        if not cancel_qs.exists():
            self.stdout.write(self.style.WARNING("No existe estado 'Cancelado'"))
            return
        cancel_state = cancel_qs.first()

        to_cancel = Order.objects.filter(status=pending_state, initialTime__lt=cutoff)
        self.stdout.write(f"Encontradas {to_cancel.count()} orden(es) para cancelar")
        for order in to_cancel:
            try:
                order.change_status(cancel_state.name)
                self.stdout.write(self.style.SUCCESS(f"Orden {order.id} cancelada y stock restaurado"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al cancelar orden {order.id}: {e}"))