from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('caja/', include('caja.urls')), # Tu app 'caja' manejará la raíz y otras URLs
    # Tu app 'cliente' manejará la raíz y otras URLs - path('', include('cliente.urls')), 
    path('', include('cliente.urls')), # Ahora /cliente/ va a index de cliente
    path('cocina/', include('cocina.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)