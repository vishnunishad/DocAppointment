from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Base Fields
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Role Fields
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    # Doctor Specific Fields
    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    
    # Patient Specific Fields
    age = models.IntegerField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

# --- NEW MODEL ADDED HERE ---

class PatientProfile(models.Model):
    # Links this profile to one specific User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patientprofile')
    
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    medical_history = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.email}"