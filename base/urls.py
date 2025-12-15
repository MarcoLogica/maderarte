from django.urls import path
from . import views

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
]











from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)