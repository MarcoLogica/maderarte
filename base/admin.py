from django.contrib import admin
from .models import Accion, Operacion, Cartera, DecisionBot, Producto, DatosContacto, Venta, Perfil, UsuarioPerfil, \
    QuiebreStock, ProductoVideo

admin.site.register(Accion)
admin.site.register(Operacion)
admin.site.register(Cartera)
admin.site.register(DecisionBot)
admin.site.register(Venta)
admin.site.register(Producto)
admin.site.register(DatosContacto)
admin.site.register(Perfil)
admin.site.register(UsuarioPerfil)

from django.contrib import admin
from .models import Orden, OrdenItem

admin.site.register(Orden)
admin.site.register(OrdenItem)
admin.site.register(QuiebreStock)





# Register your models here.
