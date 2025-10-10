from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet, UserRegistrationView, CustomTokenObtainPairView, VerifyOTPView,
    EmailVerificationView, PasswordResetRequestView, PasswordResetConfirmView,
    AdminUserViewSet, UserAuditLogViewSet
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')
router.register(r'admin/audit-logs', UserAuditLogViewSet, basename='audit-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]