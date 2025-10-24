from django.http import JsonResponse
import mercadopago
from django.conf import settings
from caja.models import Order, Payment, PaymentMethod, PaymentStatus, State
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

class PaymentService:
    @staticmethod
    def create_payment_preference(order_id, return_url):
        """Crea una preferencia de pago en Mercado Pago"""
        try:
            order = Order.objects.get(id=order_id)
            
            # Inicializar SDK
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            
            # Datos para la preferencia
            preference_data = {
                "items": [
                    {
                        "title": f"Pedido #{order.id} - Shatalito",
                        "quantity": 1,
                        "unit_price": float(order.amount),
                        "currency_id": "ARS"
                    }
                ],
                "back_urls": {
                    "success": return_url + "?status=success",
                    "failure": return_url + "?status=failure",
                    "pending": return_url + "?status=pending"
                },
                "auto_return": "approved",
                "external_reference": str(order.id),
                "notification_url": settings.MERCADOPAGO_WEBHOOK_URL,
            }
            
            # Crear preferencia
            preference_response = sdk.preference().create(preference_data)
            print("Mercado Pago response:", preference_response)  
            preference = preference_response["response"]

            if "id" not in preference or "init_point" not in preference:
                error_message = preference.get("message", "Respuesta inválida de Mercado Pago")
                return {
                    "success": False,
                    "error": error_message
                }
            
            # Guardar preference_id en la orden si el campo existe
            preference = preference_response.get("response", {})
            if "id" in preference and hasattr(order, 'preference_id'):
                try:
                    order.preference_id = preference["id"]
                    order.save(update_fields=['preference_id'])
                except Exception:
                    # no bloquear la creación de la preferencia si el guardado falla
                    pass

            return {
                "success": True,
                "init_point": preference["init_point"],
                "payment_id": preference["id"]
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def process_payment_result(payment_id, status, order_id):
        """Procesa el resultado de un pago"""
        try:
            order = Order.objects.get(id=order_id)
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info.get("response", {})
            mp_status = payment_data.get("status", "pending")
            external_reference = payment_data.get("external_reference")

            # Mapeo de estados de Mercado Pago a tu sistema
            status_mapping = {
                "approved": "Aprobado",
                "in_process": "Pendiente",
                "rejected": "Rechazado",
                "cancelled": "Cancelado"
            }
            mapped_status = status_mapping.get(mp_status, "Pendiente")
            payment_method = PaymentMethod.objects.get(name='Billetera Electrónica')
            payment_status = PaymentStatus.objects.get(name=mapped_status)
            Payment.objects.create(
                idOrder=order,
                idPaymentMethod=payment_method,
                amount=order.amount,
                idPaymentStatus=payment_status,
                token=str(payment_id)
            )
            # Actualiza el estado de la orden usando el modelo State
            if mp_status == "approved":
                preparado_state = State.objects.get(name="En Preparación")
                order.status = preparado_state
            elif mp_status == "in_process":
                pendiente_state = State.objects.get(name="Pendiente")
                order.status = pendiente_state
            elif mp_status in ["rejected", "cancelled"]:
                cancelado_state = State.objects.get(name="Cancelado")
                order.status = cancelado_state
            order.save()

            return {
                "success": True,
                "order_id": order.id,
                "status": mp_status
            }
        except Exception as e:
            print("Error en process_payment_result:", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
