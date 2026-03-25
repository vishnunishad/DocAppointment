from django.contrib.admin.forms import AdminAuthenticationForm


class EmailAdminAuthenticationForm(AdminAuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'autofocus': True,
            'placeholder': 'Email',
        })