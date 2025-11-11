from django.urls import path
from . import views

app_name = 'cocina'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('update-redirect/<int:order_id>/', views.update_order_status_redirect, name='update_order_status_redirect'),

    # API endpoints
    path('api/tables/', views.get_active_tables, name='api_get_active_tables'),
    path('api/orders/<int:table_num>/', views.get_orders_for_table, name='api_get_orders_for_table'),
]
