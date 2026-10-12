from django.contrib import admin

from .models import Aporte, Meta


class AporteInline(admin.TabularInline):
    model = Aporte
    extra = 1


@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ("nome", "valor_alvo", "prazo")
    inlines = [AporteInline]