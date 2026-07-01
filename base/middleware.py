from django.shortcuts import redirect
from django.urls import reverse
from .models import UsuarioPerfil

class PermisosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Si no está autenticado → permitir solo login, registro y home
        if not request.user.is_authenticated:
            rutas_publicas = [
                reverse('home'),
                reverse('login'),
                reverse('logout'),
                reverse('detalle_producto', kwargs={'id': 1}).replace('/1/', ''),  # patrón
            ]
            if not any(request.path.startswith(r) for r in rutas_publicas):
                return redirect('login')

        else:
            # Usuario autenticado → obtener su perfil
            try:
                usuario_perfil = UsuarioPerfil.objects.get(usuario=request.user)
                perfil = usuario_perfil.perfil
            except UsuarioPerfil.DoesNotExist:
                return redirect('acceso_denegado')

            # Reglas de permisos por URL
            reglas = [
                ('/administracion/', perfil.puede_ver_ventas),
                ('/ventas/', perfil.puede_ver_ventas),
                ('/panel-ventas/', perfil.puede_ver_panel_ventas),
                ('/importar/', perfil.puede_importar_excel),
                ('/ejecutar-ia/', perfil.puede_ejecutar_ia),
                ('/crear/', perfil.puede_crear_productos),
                ('/producto/', perfil.puede_ver_productos),
                ('/carrito/', perfil.puede_ver_carrito),
                ('/pago/', perfil.puede_procesar_pagos),
            ]

            for ruta, permiso in reglas:
                if request.path.startswith(ruta) and not permiso:
                    return redirect('acceso_denegado')

        return self.get_response(request)