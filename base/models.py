from django.db import models
from django.contrib.auth.models import User

# modelo con cada empresa del IPSA
class Accion(models.Model):
    nombre = models.CharField(max_length=100)
    simbolo = models.CharField(max_length=10, unique=True)
    sector = models.CharField(max_length=100, blank=True)
    precio_actual = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.simbolo} - {self.nombre}"

# registro de compras/ventas simuladas o reales
class Operacion(models.Model):
    TIPOS = [('compra', 'Compra'), ('venta', 'Venta')]

    accion = models.ForeignKey(Accion, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.IntegerField()
    precio = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo.upper()} {self.cantidad} {self.accion.simbolo}"

# estado actual por acción, costo promedio y total invertido
class Cartera(models.Model):
    accion = models.ForeignKey(Accion, on_delete=models.CASCADE)
    cantidad_total = models.IntegerField()
    costo_promedio = models.FloatField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def valor_total(self):
        return self.cantidad_total * self.accion.precio_actual

    def __str__(self):
        return f"{self.accion.simbolo}: {self.cantidad_total} acciones"

# decisiones sugeridas por el asistente IA, con motivo y nivel de confianza
class DecisionBot(models.Model):
    accion = models.ForeignKey(Accion, on_delete=models.CASCADE)
    tipo_decision = models.CharField(max_length=10,
                                     choices=[('compra', 'Compra'), ('venta', 'Venta'), ('hold', 'Mantener')])
    motivo = models.TextField()
    score_confianza = models.FloatField()
    precio_objetivo = models.FloatField(null=True, blank=True)
    fecha_decision = models.DateTimeField(auto_now_add=True)
    ejecutada = models.BooleanField(default=False)

    def __str__(self):
        return f"Bot: {self.tipo_decision.upper()} {self.accion.simbolo} ({round(self.score_confianza * 100, 2)}%)"


#////////////////// web ventas montessori //////////

from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    imagen = models.ImageField(upload_to='productos/')
    imagen_1 = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_2 = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_3 = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_4 = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_5 = models.ImageField(upload_to='productos/', blank=True, null=True)
    destacado = models.BooleanField(default=False)
    categoria = models.CharField(max_length=50, choices=[
        ('cunas', 'Cunas'),
        ('estanterias', 'Estanterías'),
        ('mesas', 'Mesas'),
        ('accesorios', 'Accesorios'),
    ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    stock_comercial = models.IntegerField(default=0)

    def stock_disponible(self):
        configuraciones = ConfiguracionProducto.objects.filter(producto=self)

        if not configuraciones.exists():
            return 0  # Sin receta no se puede fabricar

        cantidades = []

        for config in configuraciones:
            stock_pieza = config.pieza.stock
            necesarias = config.cantidad_necesaria

            # Si una pieza no tiene stock → no se puede fabricar ni 1 unidad
            if stock_pieza <= 0:
                return 0

            # Calcular cuántas unidades se pueden fabricar con esta pieza
            unidades = stock_pieza // necesarias
            cantidades.append(unidades)

        # El stock disponible es el mínimo entre todas las piezas
        return min(cantidades) if cantidades else 0

    def __str__(self):
        return self.nombre

    def mensaje_stock(self):
        stock = self.stock_comercial

        if stock >= 3:
            return {
                "tipo": "ok",
                "texto": "✔ Stock disponible para entrega rápida"
            }

        elif 1 <= stock <= 2:
            return {
                "tipo": "bajo",
                "texto": "🔥 Últimas unidades disponibles"
            }

        else:
            return {
                "tipo": "pedido",
                "texto": "⚠️ Disponible bajo pedido (fabricación 7–10 días)"
            }


class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    canal = models.CharField(max_length=50, choices=[
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('mercado_libre', 'Mercado Libre'),
        ('ecommerce_vipalu', 'E-commerce Vipalú'),
        ('otro', 'Otro'),
    ])
    origen = models.CharField(
        max_length=50,
        choices=[
            ('fabricante', 'Fabricante'),
            ('propia', 'Fabricación Propia'),
        ],
        default='propia'  # ← Valor por defecto para registros existentes
    )
    fecha_venta = models.DateField()
    costo_producto = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    costo_despacho = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comision_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True, null=True)


    vendedor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_realizadas'
    )

    @property
    def utilidad(self):
        return self.precio_venta - self.costo_producto - self.costo_despacho - self.comision_venta

    @property
    def margen(self):
        if self.precio_venta > 0:
            return round((self.utilidad / self.precio_venta) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.producto.nombre} - {self.fecha_venta}"


class DatosContacto(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    correo_electronico = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)  # ← Aquí está el cambio

    def __str__(self):
        return self.nombre


################# perfilamiento de usuarios

from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    # Permisos
    puede_ver_ventas = models.BooleanField(default=False)
    puede_crear_ventas = models.BooleanField(default=False)
    puede_editar_ventas = models.BooleanField(default=False)
    puede_eliminar_ventas = models.BooleanField(default=False)
    puede_ver_panel_ventas = models.BooleanField(default=False)

    puede_ver_productos = models.BooleanField(default=False)
    puede_crear_productos = models.BooleanField(default=False)
    puede_editar_productos = models.BooleanField(default=False)
    puede_eliminar_productos = models.BooleanField(default=False)

    puede_importar_excel = models.BooleanField(default=False)
    puede_ejecutar_ia = models.BooleanField(default=False)

    puede_ver_carrito = models.BooleanField(default=False)
    puede_procesar_pagos = models.BooleanField(default=False)
    acceso_panel = models.BooleanField(default=False)



    def __str__(self):
        return self.nombre


class UsuarioPerfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    perfil = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.usuario.username} → {self.perfil.nombre}"


from django.db import models

class Fortaleza(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()

    # Nuevos campos
    imagen = models.ImageField(upload_to='fortalezas_imagenes/', blank=True, null=True)
    video = models.FileField(upload_to='fortalezas_videos/', blank=True, null=True)

    def __str__(self):
        return self.titulo



class Oferta(models.Model):
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='ofertas_imagenes/', blank=True, null=True)
    video = models.FileField(upload_to='ofertas_videos/', blank=True, null=True)

    def __str__(self):
        return self.titulo


class Testimonio(models.Model):
    titulo = models.CharField(max_length=150)
    comentario = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='testimonios/')   # captura del agradecimiento
    imagen2 = models.ImageField(upload_to='testimonios/', blank=True, null=True)  # foto del niño

    def __str__(self):
        return self.titulo


# administrador de stock

class Pieza(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.stock} uds)"


class ConfiguracionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE)
    cantidad_necesaria = models.IntegerField()

    def __str__(self):
        return f"{self.producto.nombre} - {self.pieza.nombre} x {self.cantidad_necesaria}"


class MovimientoStockPieza(models.Model):
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField()  # positivo = entrada, negativo = salida
    motivo = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.pieza.nombre} ({self.cantidad}) - {self.fecha}"


# modelos para crear ordenes y rebajar stock

class Orden(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("produccion", "En producción"),
        ("listo", "Listo para envío"),
        ("enviado", "Enviado"),
        ("entregado", "Entregado"),
    ]

    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    correo_electronico = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    comprobante = models.FileField(upload_to='comprobantes/')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    codigo_seguimiento = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.codigo_seguimiento:
            import uuid
            self.codigo_seguimiento = f"MA-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def tiene_quiebre(self):
        return QuiebreStock.objects.filter(orden=self, resuelto=False).exists()

    def __str__(self):
        return f"Orden #{self.id} - {self.nombre}"


class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} (${self.precio_unitario})"


class QuiebreStock(models.Model):
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE)
    cantidad_faltante = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)

    def __str__(self):
        return f"Quiebre {self.pieza.nombre} - Orden {self.orden.id}"


# sección como se fabrican los productos (administración de los videos)

class ProductoVideo(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    titulo = models.CharField(max_length=200, blank=True)
    video = models.FileField(upload_to='videos_productos/', null=True, blank=True)

    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.producto.nombre} - {self.titulo or 'Video'}"


#seccion beneficios

class BeneficioProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="beneficios"
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=100, blank=True)  # opcional
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.producto.nombre} - {self.titulo}"

# uso real

class UsoRealProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="usos_reales"
    )
    imagen = models.ImageField(upload_to="usos_reales/", null=True, blank=True)
    video = models.FileField(upload_to="usos_reales/", null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Uso real de {self.producto.nombre}"

#preguntas frecuentes

class PreguntaFrecuenteProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="preguntas_frecuentes"
    )
    pregunta = models.CharField(max_length=255)
    respuesta = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"FAQ de {self.producto.nombre}: {self.pregunta}"


#productos relacionados

class ProductoRelacionado(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="productos_relacionados"
    )
    imagen = models.ImageField(upload_to="productos_relacionados/")
    titulo = models.CharField(max_length=255)
    producto_destino = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="relacionado_destino"
    )
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.titulo} relacionado con {self.producto.nombre}"


#panel logístico

class Transportista(models.Model):
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True, null=True)

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    vehiculo = models.CharField(max_length=100, blank=True, null=True)
    patente = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


class RutaEntrega(models.Model):
    transportista = models.ForeignKey(Transportista, on_delete=models.CASCADE, related_name="rutas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    ESTADOS = (
        ("pendiente", "Pendiente"),
        ("en_ruta", "En ruta"),
        ("completada", "Completada"),
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")

    def __str__(self):
        return f"Ruta #{self.id} - {self.transportista.nombre}"


class RutaOrden(models.Model):
    ruta = models.ForeignKey(RutaEntrega, on_delete=models.CASCADE, related_name="ordenes_ruta")
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="ruta_asignada")

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ruta {self.ruta.id} → Orden {self.orden.id}"


class RegistroEntrega(models.Model):
    orden = models.OneToOneField(Orden, on_delete=models.CASCADE, related_name="registro_entrega")

    nombre_receptor = models.CharField(max_length=255)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Entrega Orden {self.orden.id}"


# pixel home

class PixelEvent(models.Model):
    # Identidad del evento
    event = models.CharField(max_length=200)              # Ej: click_btn_agregar, scroll_depth, hover_testimonio
    category = models.CharField(max_length=200, null=True, blank=True)  # Ej: navbar, hero, catalogo, ofertas
    element = models.CharField(max_length=200, null=True, blank=True)   # Ej: btn-agregar, card-producto, oferta-card

    # Identidad del usuario
    visitor_id = models.CharField(max_length=200)         # ID persistente
    session_id = models.CharField(max_length=200)         # ID por sesión

    # Contexto
    page = models.CharField(max_length=100)               # HOME, CARRITO, DETALLE, etc.
    timestamp = models.DateTimeField(auto_now_add=True)   # Fecha exacta del evento

    # Datos estructurados
    value_number = models.FloatField(null=True, blank=True)   # scroll depth, tiempo, precio, etc.
    value_text = models.CharField(max_length=500, null=True, blank=True)  # nombre del producto, botón, sección

    # Datos complejos
    data = models.JSONField(null=True, blank=True)        # cualquier estructura adicional

    def __str__(self):
        return f"{self.timestamp} - {self.event}"
