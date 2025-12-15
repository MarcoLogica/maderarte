from django.contrib import admin
from .models import Accion, Operacion, Cartera, DecisionBot, Producto, DatosContacto, Venta

admin.site.register(Accion)
admin.site.register(Operacion)
admin.site.register(Cartera)
admin.site.register(DecisionBot)
admin.site.register(Venta)
admin.site.register(Producto)
admin.site.register(DatosContacto)

# Register your models here.
