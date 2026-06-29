from django.contrib import admin
from .models import UsuarioModel


@admin.register(UsuarioModel)
class UsuarioModelAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "nombre_completo", "tipo", "is_active", "is_staff"]
    list_filter = ["tipo", "is_active"]
    search_fields = ["email", "nombre_completo"]
