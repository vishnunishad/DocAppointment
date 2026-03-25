from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PatientProfile
from .forms import EmailAdminAuthenticationForm

admin.site.login_form = EmailAdminAuthenticationForm

@admin.register(User)
class CustomUserAdmin(UserAdmin):
	ordering = ('email',)
	list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_staff')
	search_fields = ('email', 'username', 'first_name', 'last_name')

	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone', 'address', 'profile_image', 'age', 'bio')}),
		('Doctor info', {'fields': ('specialization', 'experience', 'consultation_fee', 'is_verified')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
	)

	add_fieldsets = (
		(
			None,
			{
				'classes': ('wide',),
				'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_staff', 'is_superuser', 'is_active'),
			},
		),
	)

admin.site.register(PatientProfile)