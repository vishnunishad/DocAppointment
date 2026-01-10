from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=15, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    experience = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    blood_group = models.CharField(max_length=5, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.role})"