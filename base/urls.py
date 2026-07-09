from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

from .views import administrar_videos_producto, eliminar_video_producto, editar_video_producto, \
    administrar_beneficios_producto, editar_beneficio_producto, eliminar_beneficio_producto, editar_uso_real_producto, \
    eliminar_uso_real_producto, administrar_uso_real_producto, administrar_faq_producto, editar_faq_producto, \
    eliminar_faq_producto, administrar_productos_relacionados, editar_producto_relacionado, \
    eliminar_producto_relacionado

urlpatterns = [


                 path('importar/', views.importar_excel, name='importar_excel'),
                 path('ejecutar-ia/', views.run_predictor, name='run_predictor'),


    path('', views.home, name='home'),
    path('producto/<int:id>/', views.detalle_producto, name='detalle_producto'),
    path('crear/', views.crear_producto, name='crear_producto'),
    path('panel/', views.panel, name='panel'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('producto/<int:id>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('pago/', views.pago, name='pago'),
    path('exito/', views.exito, name='exito'),
    path('administracion/', views.administracion_ventas, name='administracion_ventas'),
    path('ventas/<int:id>/editar/', views.editar_venta, name='editar_venta'),
    path('ventas/<int:id>/eliminar/', views.eliminar_venta, name='eliminar_venta'),
    path('panel-ventas/', views.panel_ventas, name='panel_ventas'),
    path('perfiles/', views.panel_perfiles, name='panel_perfiles'),
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfiles/editar/<int:id>/', views.editar_perfil, name='editar_perfil'),
    path('subir-media/<int:id>/', views.subir_media_fortaleza, name='subir_media_fortaleza'),
    path('fortalezas/', views.lista_fortalezas, name='lista_fortalezas'),
    path('fortalezas/crear/', views.crear_fortaleza, name='crear_fortaleza'),
    path('fortalezas/editar/<int:id>/', views.editar_fortaleza, name='editar_fortaleza'),
    path('fortalezas/eliminar/<int:id>/', views.eliminar_fortaleza, name='eliminar_fortaleza'),
    path('ofertas/', views.lista_ofertas, name='lista_ofertas'),
    path('ofertas/crear/', views.crear_oferta, name='crear_oferta'),
    path('ofertas/editar/<int:id>/', views.editar_oferta, name='editar_oferta'),
    path('ofertas/eliminar/<int:id>/', views.eliminar_oferta, name='eliminar_oferta'),
    path('testimonios/', views.lista_testimonios, name='lista_testimonios'),
    path('testimonios/crear/', views.crear_testimonio, name='crear_testimonio'),
    path('testimonios/editar/<int:id>/', views.editar_testimonio, name='editar_testimonio'),
    path('testimonios/eliminar/<int:id>/', views.eliminar_testimonio, name='eliminar_testimonio'),
# PIEZAS
path("piezas/", views.piezas_list, name="piezas_list"),
path("piezas/crear/", views.pieza_create, name="pieza_create"),
path("piezas/editar/<int:pieza_id>/", views.pieza_edit, name="pieza_edit"),
path("piezas/eliminar/<int:pieza_id>/", views.pieza_delete, name="pieza_delete"),
path("piezas/movimientos/<int:pieza_id>/", views.movimientos_pieza, name="movimientos_pieza"),
# CONFIGURACIÓN DE PRODUCTO
path("configuracion/", views.configuracion_list, name="configuracion_list"),
path("configuracion/crear/", views.configuracion_create, name="configuracion_create"),
path("configuracion/eliminar/<int:config_id>/", views.configuracion_delete, name="configuracion_delete"),
# CONTROL DE STOCK
path("control-stock/", views.control_stock, name="control_stock"),
path("panel-ordenes/", views.panel_ordenes, name="panel_ordenes"),
path("orden/<int:orden_id>/estado/<str:nuevo_estado>/", views.cambiar_estado_orden, name="cambiar_estado_orden"),
path("panel-quiebres/", views.panel_quiebres, name="panel_quiebres"),
path("quiebre/<int:quiebre_id>/resolver/", views.resolver_quiebre, name="resolver_quiebre"),
path("panel-produccion/", views.panel_produccion, name="panel_produccion"),
path("orden/<int:orden_id>/fabricado/", views.marcar_fabricado, name="marcar_fabricado"),
path("dashboard-stock/", views.dashboard_stock, name="dashboard_stock"),
path("tracking/<str:codigo>/", views.tracking, name="tracking"),
path("tracking/", views.buscar_tracking, name="buscar_tracking"),
path("producto/<int:producto_id>/videos/", administrar_videos_producto, name="administrar_videos_producto"),
path("producto/video/<int:video_id>/eliminar/", eliminar_video_producto, name="eliminar_video_producto"),
path("producto/video/<int:video_id>/editar/", editar_video_producto, name="editar_video_producto"),
# BENEFICIOS POR PRODUCTO
path("producto/<int:producto_id>/beneficios/", administrar_beneficios_producto, name="administrar_beneficios_producto"),
path("producto/beneficio/<int:beneficio_id>/editar/", editar_beneficio_producto, name="editar_beneficio_producto"),
path("producto/beneficio/<int:beneficio_id>/eliminar/", eliminar_beneficio_producto, name="eliminar_beneficio_producto"),
# USO REAL POR PRODUCTO
path("producto/<int:producto_id>/uso-real/", administrar_uso_real_producto, name="administrar_uso_real_producto"),

path("producto/uso-real/<int:uso_id>/editar/", editar_uso_real_producto, name="editar_uso_real_producto"),
path("producto/uso-real/<int:uso_id>/eliminar/", eliminar_uso_real_producto, name="eliminar_uso_real_producto"),

# FAQ POR PRODUCTO
path("producto/<int:producto_id>/faq/", administrar_faq_producto, name="administrar_faq_producto"),
path("producto/faq/<int:faq_id>/editar/", editar_faq_producto, name="editar_faq_producto"),
path("producto/faq/<int:faq_id>/eliminar/", eliminar_faq_producto, name="eliminar_faq_producto"),
# PRODUCTOS RELACIONADOS
path("producto/<int:producto_id>/relacionados/", administrar_productos_relacionados, name="administrar_productos_relacionados"),
path("producto/relacionado/<int:rel_id>/editar/", editar_producto_relacionado, name="editar_producto_relacionado"),
path("producto/relacionado/<int:rel_id>/eliminar/", eliminar_producto_relacionado, name="eliminar_producto_relacionado"),
path('montessori-en-casa/', views.montessori_en_casa, name='montessori_en_casa'),











]











from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)