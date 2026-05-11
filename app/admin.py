from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


class CustomUserAdmin(UserAdmin):
    model = Usuario

    fieldsets = UserAdmin.fieldsets + (
        ('Tipo de Usuário', {
            'fields': ('tipo',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Tipo de Usuário', {
            'fields': ('tipo',)
        }),
    )


admin.site.register(Usuario, CustomUserAdmin)