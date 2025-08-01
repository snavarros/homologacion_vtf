from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Region, PerfilUsuario


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = "Perfil Usuario"


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Region)
