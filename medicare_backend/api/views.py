from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView 
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import socket

# --- 1. LOCAL IMPORTS (From api folder) ---
from .models import Appointment
from .serializers import AppointmentSerializer

# --- 2. EXTERNAL IMPORTS (From accounts folder) ---
from accounts.models import PatientProfile
from accounts.serializers import (
    UserSerializer, 
    PatientProfileSerializer
)

User = get_user_model()


class OTPEmailSendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class SMTPTestSerializer(serializers.Serializer):
    email = serializers.EmailField()


def _otp_cache_key(email):
    return f"email_otp:{email.lower()}"


def _otp_verified_cache_key(email):
    return f"email_otp_verified:{email.lower()}"


class SendEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPEmailSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "An account with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rate_key = f"email_otp_rate:{email}"
        if cache.get(rate_key):
            return Response(
                {"detail": "Please wait before requesting another OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=10)
        cache.set(_otp_cache_key(email), {"otp": otp, "expires_at": expires_at.isoformat()}, timeout=600)
        cache.delete(_otp_verified_cache_key(email))
        cache.set(rate_key, True, timeout=45)

        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                cache.delete(_otp_cache_key(email))
                return Response(
                    {"detail": "SMTP is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            send_mail(
                subject='Your MediCare registration OTP',
                message=(
                    f"Your OTP is: {otp}\n"
                    "It is valid for 10 minutes."
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medicare.local'),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            cache.delete(_otp_cache_key(email))
            error_message = "Unable to send OTP email. Check email server configuration."
            if isinstance(exc, socket.gaierror):
                error_message = "Unable to send OTP email. DNS lookup failed for EMAIL_HOST. Check EMAIL_HOST and your network DNS."
            if settings.DEBUG:
                error_message = f"{error_message} ({exc.__class__.__name__}: {str(exc)})"
            return Response(
                {"detail": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"detail": "OTP sent to your email."}, status=status.HTTP_200_OK)


class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        otp = serializer.validated_data['otp']

        otp_payload = cache.get(_otp_cache_key(email))
        if not otp_payload:
            return Response(
                {"detail": "OTP expired or not requested."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_payload.get('otp') != otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(_otp_cache_key(email))
        cache.set(_otp_verified_cache_key(email), True, timeout=900)
        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)


class SMTPTestEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SMTPTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_email = serializer.validated_data['email'].lower()

        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                return Response(
                    {"detail": "SMTP is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            send_mail(
                subject='MediCare SMTP test email',
                message='SMTP is configured correctly for MediCare OTP delivery.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medicare.local'),
                recipient_list=[target_email],
                fail_silently=False,
            )
        except Exception as exc:
            error_message = "SMTP test failed. Check email server configuration."
            if isinstance(exc, socket.gaierror):
                error_message = "SMTP test failed. DNS lookup failed for EMAIL_HOST. Check EMAIL_HOST and your network DNS."
            if settings.DEBUG:
                error_message = f"{error_message} ({exc.__class__.__name__}: {str(exc)})"
            return Response({"detail": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "SMTP test email sent successfully."}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        # Allow anyone to register or see doctors list
        if self.action in ['create', 'doctors']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        email = (request.data.get('email') or '').lower()
        if not email:
            return Response({"email": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        if not cache.get(_otp_verified_cache_key(email)):
            return Response(
                {"detail": "Please verify your email with OTP before registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            cache.delete(_otp_verified_cache_key(email))
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User created successfully",
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'patch'])
    def profile(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def doctors(self, request):
        doctors = User.objects.filter(role='doctor')
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)


class MyMedicalProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Appointment.objects.all().order_by('-date')
        elif user.role == 'doctor':
            return Appointment.objects.filter(doctor=user).order_by('-date')
        else:
            return Appointment.objects.filter(patient=user).order_by('-date')

    def perform_create(self, serializer):
        if self.request.user.role != 'patient':
            raise PermissionDenied('Only patient accounts can create appointments.')
        serializer.save(patient=self.request.user)