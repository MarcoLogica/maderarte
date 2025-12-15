from django.db import models

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
    precio = models.DecimalField(max_digits=10, decimal_places=2)
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

    def __str__(self):
        return self.nombre


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
    VENDEDORES = [
        ('Marco', 'Marco'),
        ('Catalina', 'Catalina'),
    ]

    vendedor = models.CharField(
        max_length=100,
        choices=VENDEDORES,
        null=True,
        blank=True
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