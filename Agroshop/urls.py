from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('', include('cart.urls')),
    path('', include('checkout.urls')),
    path('', include('orders.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)