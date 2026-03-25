from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PatientProfile  

User = get_user_model()

# 1. Custom Login Serializer
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        if 'username' in attrs:
            attrs[self.username_field] = attrs.pop('username')

        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            # We can also pass the image URL on login if you want
            # 'profile_image': self.user.profile_image.url if self.user.profile_image else None
        }
        return data

# 2. User Serializer (Registration & Profile Updates)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 
            'phone', 'address', 'role', 'specialization', 
            'experience', 'consultation_fee', 'is_verified', 'age', 'bio',
            'profile_image'  # <--- ADDED THIS FIELD
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

# 3. Patient Profile Serializers
class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'blood_group', 'allergies', 'medical_history', 'address']

class UserDetailSerializer(serializers.ModelSerializer):
    # This connects User -> Profile
    # Ensure 'source' matches your User model's related_name for the profile
    # If no related_name was set in models.py, Django defaults to 'patientprofile'
    profile = PatientProfileSerializer(source='patientprofile', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'address', 'age', 'profile', 'profile_image']