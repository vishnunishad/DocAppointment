from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    # Dedicated Profile URL (Must be first)
    path('my-medical-profile/', UserViewSet.as_view({'get': 'profile_details', 'patch': 'profile_details'}), name='my-medical-profile'),

    # Standard Router URLs
    path('', include(router.urls)),
]