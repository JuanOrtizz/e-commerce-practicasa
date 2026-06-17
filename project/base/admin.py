from django.contrib import admin
from .models import ConsultaModel

@admin.register(ConsultaModel)
class ConsultaModelAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "nombre", "telefono", "mensaje"]
    list_filter = ["email", "telefono"]
    search_fields = ["email", "nombre", "telefono"]
