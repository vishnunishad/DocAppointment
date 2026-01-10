from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    # --- THIS WAS MISSING ---
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        # Returns the logged-in user's data
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    # ------------------------

    @action(detail=False, methods=['get'])
    def doctors(self, request):
        doctors = User.objects.filter(role='doctor', is_verified=True)
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Intercept the request to check if the user sent an email
        login_input = request.data.get('username')
        
        if login_input:
            # Check if a user exists with this Email
            user = User.objects.filter(email=login_input).first()
            if user:
                # If found, swap the email for the real username
                request.data['username'] = user.username
        
        return super().post(request, *args, **kwargs)