from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'caja'

urlpatterns = [

    # Vistas de Páginas
    path('login/', views.login_view, name='login'), # Raíz será la página de login
    path('logout/', views.logout_view, name='logout'),
    path('determine_dashboard/', views.determine_dashboard_view, name='determine_dashboard'),


    # API Endpoints
    path('api/session_status/', views.api_session_status, name='api_session_status'),
    
    # Orders API
    path('api/orders/', views.api_orders_list_create, name='api_orders_list_create'), # GET para listar, POST para crear (si aplica)
    path('api/orders/<int:order_id>/', views.api_order_detail_update_delete, name='api_order_detail_update_delete'), # GET detalle, PUT update status, DELETE cancel

    # Products API (Admin/Superuser)
    path('api/admin/products/', views.api_products_list_create, name='api_products_list_create'),
    path('api/admin/products/by_name/', views.api_get_product_by_name, name='api_get_product_by_name'),
    path('api/admin/products/<int:product_id>/stock/', views.api_update_product_stock, name='api_update_product_stock'),
    
    # Users API (Superuser)
    path('api/session-status/', views.api_session_status, name='api_session_status'),
    path('api/superuser/users/', views.api_superuser_users_list_create, name='api_superuser_users_list_create'),
    path('api/superuser/users/<str:username>/', views.api_superuser_modify_user, name='api_superuser_modify_user'),

    # Nueva ruta para el dashboard administrativo
    path('dashboard/', views.dashboard_view, name='dashboard'),


    # Nueva ruta para guardar pedido de cliente
    path('api/guardar_pedido_cliente/', views.api_guardar_pedido_cliente, name='api_guardar_pedido_cliente'),

    # Rutas para integración con Mercado Pago
    path('api/payments/create/', views.create_payment, name='api_create_payment'),
    path('api/payments/process_result/', views.process_payment_result, name='api_process_payment_result'),
    path('api/payments/webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

