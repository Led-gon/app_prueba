import mercadopago
from django.conf import settings
from caja.models import Order, Payment, PaymentMethod, PaymentStatus

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
            
            # Guardar preference_id en la orden
            order.preference_id = preference["id"]
            order.save(update_fields=['preference_id'])

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
            
            # Mapeo de estados de Mercado Pago a tu sistema
            status_mapping = {
                "success": "Aprobado",
                "pending": "Pendiente",
                "failure": "Rechazado"
            }
            
            # Actualizar pago
            payment_method = PaymentMethod.objects.get(name='Mercado Pago')
            payment_status = PaymentStatus.objects.get(name=status_mapping.get(status, "Pendiente"))
            
            payment = Payment.objects.create(
                idOrder=order,
                idPaymentMethod=payment_method,
                amount=order.amount,
                idPaymentStatus=payment_status,
                token=payment_id
            )
            
            # Actualizar orden según el estado
            if status == "success":
                order.status_id = 2  # Actualizar al estado correspondiente
                order.payment_status = "Aprobado"
                order.save()
            elif status == "pending":
                order.status_id = 1  # Pendiente de pago
                order.payment_status = "Pendiente"
                order.save()
            else:
                order.status_id = 5  # Cancelado
                order.payment_status = "Rechazado"
                order.save()
            
            return {
                "success": True,
                "payment_id": payment.token,
                "order_id": order.id,
                "status": status
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }