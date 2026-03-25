from rest_framework import serializers
from .models import Appointment
from django.contrib.auth import get_user_model

# --- CRITICAL CHANGE ---
# We import the serializers from 'accounts' because that is where 
# we defined the logic to include the Medical Profile.
from accounts.serializers import UserSerializer, UserDetailSerializer

User = get_user_model()

class AppointmentSerializer(serializers.ModelSerializer):
    # 1. Doctor Details: Uses basic info (Name, Spec)
    doctor_details = UserSerializer(source='doctor', read_only=True)
    
    # 2. Patient Details: Uses UserDetailSerializer 
    # This serializer INCLUDES the 'profile' (Medical History, Allergies)
    patient_details = UserDetailSerializer(source='patient', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'date', 'time', 'notes', 
                  'status', 'consultation_fee', 'doctor_details', 'patient_details']
        extra_kwargs = {
            'patient': {'read_only': True}
        }