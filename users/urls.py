from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,

)

from .views import MeView, RegisterView, CustomTokenObtainPairView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user_register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="user_me"),
]