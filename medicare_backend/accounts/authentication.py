from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def get_header(self, request):
        header = super().get_header(request)
        if header is not None:
            return header

        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token:
            return f"Bearer {raw_token}".encode('utf-8')
        return None
