from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from products.api import ProductViewSet
from django.conf import settings
from django.conf.urls.static import static
from orders.views import checkout, test_cloudinary, test_cloudinary_connection


router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/checkout/', checkout),
    path('test-cloudinary/', test_cloudinary),
    # In urls.py
    path('test-cloudinary-connection/', test_cloudinary_connection),

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
