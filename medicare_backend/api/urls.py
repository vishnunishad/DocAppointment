from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    AppointmentViewSet,
    MyMedicalProfileView,
    SendEmailOTPView,
    VerifyEmailOTPView,
    SMTPTestEmailView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', MyMedicalProfileView.as_view(), name='profile'),
    path('otp/smtp-test/', SMTPTestEmailView.as_view(), name='smtp-test-email'),
    path('otp/send/', SendEmailOTPView.as_view(), name='send-email-otp'),
    path('otp/verify/', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
]