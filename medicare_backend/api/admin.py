from django.contrib import admin
from .models import Appointment, PatientProfile

# Register these so you can manage appointments in the dashboard
admin.site.register(Appointment)
admin.site.register(PatientProfile)