from django.urls import path
from . import views

app_name = 'cocina'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('update/<int:order_id>/', views.update_order_status, name='update_order'),
]