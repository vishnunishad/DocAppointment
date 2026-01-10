from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import Appointment, PatientProfile
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    AppointmentSerializer, 
    PatientProfileSerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User created successfully",
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # THIS IS THE FUNCTION WE NEED FOR THE PROFILE PAGE
    @action(detail=False, methods=['get', 'patch'])
    def profile_details(self, request):
        user = request.user
        profile, created = PatientProfile.objects.get_or_create(user=user)

        if request.method == 'GET':
            serializer = PatientProfileSerializer(profile)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
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
        if user.role == 'doctor':
            return Appointment.objects.filter(doctor=user)
        elif user.role == 'patient':
            return Appointment.objects.filter(patient=user)
        return Appointment.objects.all()

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)