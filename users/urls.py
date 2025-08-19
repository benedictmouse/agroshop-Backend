from django.urls import path
from .views import(
    UserRegistrationView,
    UserProfileView,
    CustomTokenObtainPairView,
    LogoutView,
    PasswordChangeView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('login/', CustomTokenObtainPairView.as_view(), name='user-login'),
    path('changepassword/', PasswordChangeView.as_view(), name='change-password'),
]
