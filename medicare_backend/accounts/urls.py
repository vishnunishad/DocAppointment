from django.urls import path
# 1. Import MyMedicalProfileView here
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    MyMedicalProfileView,
    PasswordResetEmailView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/password-reset-email/', PasswordResetEmailView.as_view(), name='password-reset-email'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # 2. Add the path for the Medical Profile
    # Assuming your main urls.py includes this file with 'api/' prefix
    # Resulting URL: http://127.0.0.1:8000/api/my-medical-profile/
    path('my-medical-profile/', MyMedicalProfileView.as_view(), name='my-medical-profile'),
]