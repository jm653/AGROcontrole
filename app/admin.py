from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario,
    Propriedade,
    Lavoura,
    LoteDeCafe
)


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
admin.site.register(Propriedade)
admin.site.register(Lavoura)
admin.site.register(LoteDeCafe)