from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from products.api import ProductViewSet
from django.conf import settings
from django.conf.urls.static import static
from orders.views import checkout


router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/checkout/', checkout),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
