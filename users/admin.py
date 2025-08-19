from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


from .models import CustomUser

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_active', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
