from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.core.cache import cache
from django.core import signing
from django.utils.http import urlencode
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import PatientProfileSerializer
from .models import PatientProfile

User = get_user_model()


class PasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=128)

# 1. Login View
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        if access_token and refresh_token:
            set_auth_cookies(response, access_token, refresh_token)
            response.data.pop('access', None)
            response.data.pop('refresh', None)
        return response


def set_auth_cookies(response, access_token, refresh_token=None):
    cookie_secure = settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', not settings.DEBUG)
    cookie_httponly = settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True)
    cookie_samesite = settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    cookie_path = settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/')

    access_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'medicare_access')
    refresh_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'medicare_refresh')

    access_lifetime = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    refresh_lifetime = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

    response.set_cookie(
        key=access_cookie_name,
        value=access_token,
        max_age=access_lifetime,
        httponly=cookie_httponly,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path=cookie_path,
    )

    if refresh_token:
        response.set_cookie(
            key=refresh_cookie_name,
            value=refresh_token,
            max_age=refresh_lifetime,
            httponly=cookie_httponly,
            secure=cookie_secure,
            samesite=cookie_samesite,
            path=cookie_path,
        )


def clear_auth_cookies(response):
    cookie_path = settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/')
    access_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'medicare_access')
    refresh_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'medicare_refresh')

    response.delete_cookie(access_cookie_name, path=cookie_path)
    response.delete_cookie(refresh_cookie_name, path=cookie_path)


class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'medicare_refresh')
        refresh_token = request.COOKIES.get(refresh_cookie_name) or request.data.get('refresh')
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get('access')
        rotated_refresh = serializer.validated_data.get('refresh')

        response = Response({"detail": "Token refreshed."}, status=status.HTTP_200_OK)
        set_auth_cookies(response, access_token, rotated_refresh)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'medicare_refresh')
        refresh_token = request.COOKIES.get(refresh_cookie_name)

        if refresh_token and 'rest_framework_simplejwt.token_blacklist' in settings.INSTALLED_APPS:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response

# 2. Registration View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({"email": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        verified_key = f"email_otp_verified:{email}"
        if not cache.get(verified_key):
            return Response(
                {"detail": "Please verify your email with OTP before registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = super().create(request, *args, **kwargs)
        if response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            cache.delete(verified_key)
        return response

class UserListView(generics.ListCreateAPIView):
    # ... your other code ...
    permission_classes = [IsAuthenticated]

class MyMedicalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated] # Make sure IsAuthenticated is imported

    def get_object(self):
        profile, created = PatientProfile.objects.get_or_create(user=self.request.user)
        return profile


class PasswordResetEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()

        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                return Response(
                    {"detail": "SMTP is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        user = User.objects.filter(email=email).first()
        if user:
            try:
                token = signing.dumps({'email': email}, salt='password-reset')
                reset_page = getattr(
                    settings,
                    'FRONTEND_RESET_PASSWORD_URL',
                    'http://127.0.0.1:5500/templates/reset-password.html',
                )
                reset_link = f"{reset_page}?{urlencode({'email': email, 'token': token})}"

                send_mail(
                    subject='MediCare password reset request',
                    message=(
                        "We received a password reset request for your MediCare account.\n\n"
                        "Click the link below to reset your password (valid for 1 hour):\n"
                        f"{reset_link}\n\n"
                        "If you did not request this, please ignore this email."
                    ),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medicare.local'),
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as exc:
                error_message = "Unable to send reset email. Check email server configuration."
                if settings.DEBUG:
                    error_message = f"{error_message} ({exc.__class__.__name__}: {str(exc)})"
                return Response({"detail": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"detail": "If this email is registered, reset instructions have been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            payload = signing.loads(token, salt='password-reset', max_age=3600)
        except signing.BadSignature:
            return Response({"detail": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.SignatureExpired:
            return Response({"detail": "Reset token has expired."}, status=status.HTTP_400_BAD_REQUEST)

        token_email = (payload.get('email') or '').strip().lower()
        if token_email != email:
            return Response({"detail": "Invalid reset token for this email."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "Invalid reset request."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)