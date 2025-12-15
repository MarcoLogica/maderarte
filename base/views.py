import pandas as pd
import subprocess
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Accion, DecisionBot

@csrf_exempt
def importar_excel(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]
        df = pd.read_excel(archivo)

        for _, row in df.iterrows():
            Accion.objects.update_or_create(
                simbolo=row["simbolo"],
                defaults={
                    "nombre": row["nombre"],
                    "precio_actual": row["precio_actual"],
                    "sector": row.get("sector", "")
                }
            )
        messages.success(request, "✅ Acciones importadas correctamente.")
        return redirect("dashboard")
    messages.error(request, "❌ Archivo inválido o faltante.")
    return redirect("dashboard")

def dashboard(request):
    acciones = Accion.objects.all()
    decisiones = DecisionBot.objects.all().order_by('-fecha_decision')[:30]
    return render(request, "dashboard.html", {
        "acciones": acciones,
        "decisiones": decisiones
    })

def run_predictor(request):
    try:
        result = subprocess.run(
            ["python", "ia/predictor.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )

        salida = result.stdout.strip()
        error = result.stderr.strip()

        if salida:
            messages.success(request, "🧠 IA ejecutada: " + salida)
        elif error:
            messages.error(request, "❌ Error al ejecutar IA: " + error)
        else:
            messages.warning(request, "⚠️ IA ejecutada, pero sin salida visible.")
    except Exception as e:
        messages.error(request, f"❌ Excepción al ejecutar IA: {str(e)}")

    return redirect("dashboard")



#///////////////////WEB ventas montessori ////////////////


from django.shortcuts import render
from .models import Producto

def home(request):
    productos = Producto.objects.filter(destacado=True)[:6]
    return render(request, 'home.html', {'productos': productos})

from django.shortcuts import render, get_object_or_404
from .models import Producto

def detalle_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    imagenes_adicionales = [
        producto.imagen_1,
        producto.imagen_2,
        producto.imagen_3,
        producto.imagen_4,
        producto.imagen_5,
    ]
    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'imagenes_adicionales': imagenes_adicionales
    })

from django.shortcuts import render, redirect
from .forms import ProductoForm

def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductoForm()
    return render(request, 'crear_producto.html', {'form': form})

def panel(request):
    return render(request, 'panel.html')

from django.shortcuts import render
from .models import Producto

def lista_productos(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'lista_productos.html', {'productos': productos})

from django.shortcuts import render, get_object_or_404, redirect
from .models import Producto
from .forms import ProductoForm

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'editar_producto.html', {'form': form, 'producto': producto})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Producto

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        producto.delete()
        return redirect('lista_productos')
    return render(request, 'eliminar_producto.html', {'producto': producto})


def agregar_al_carrito(request, id):
    carrito = request.session.get('carrito', {})
    carrito[str(id)] = carrito.get(str(id), 0) + 1
    request.session['carrito'] = carrito
    return redirect('ver_carrito')

from .models import Producto

def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    productos = []
    total = 0

    for id, cantidad in carrito.items():
        producto = Producto.objects.get(id=id)
        producto.cantidad = cantidad
        producto.subtotal = producto.precio * cantidad
        productos.append(producto)
        total += producto.subtotal

    return render(request, 'carrito.html', {'productos': productos, 'total': total})

def eliminar_del_carrito(request, id):
    carrito = request.session.get('carrito', {})
    if str(id) in carrito:
        del carrito[str(id)]
    request.session['carrito'] = carrito
    return redirect('ver_carrito')


from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from .models import Producto
from django.conf import settings
from .forms import DatosContactoForm

def pago(request):
    carrito = request.session.get('carrito', {})
    productos = []
    total = 0

    for id, cantidad in carrito.items():
        producto = Producto.objects.get(id=id)
        producto.cantidad = cantidad
        producto.subtotal = producto.precio * cantidad
        productos.append(producto)
        total += producto.subtotal

    contacto_form = DatosContactoForm(request.POST)

    if contacto_form.is_valid():
        contacto_form.save()

    if request.method == 'POST':
        imagen = request.FILES.get('comprobante')
        if imagen:
            email = EmailMessage(
                subject='Nuevo pago recibido',
                body=f'Se ha recibido un pago por ${total}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['marco.sepulvedam85@gmail.com'],
            )
            email.attach(imagen.name, imagen.read(), imagen.content_type)
            email.send()
            request.session['carrito'] = {}  # Vaciar carrito
            return redirect('exito')

    return render(request, 'pago.html', {'productos': productos, 'total': total})

def exito(request):
    return render(request, 'exito.html')


from django.shortcuts import render
from .models import Venta, Producto
from .forms import VentaForm

def administracion_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha_venta')

    canal = request.GET.get('canal')
    producto_id = request.GET.get('producto')
    origen = request.GET.get('origen')

    if canal:
        ventas = ventas.filter(canal=canal)
    if producto_id:
        ventas = ventas.filter(producto_id=producto_id)
    if origen:
        ventas = ventas.filter(origen=origen)

    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('administracion_ventas')  # Recarga la vista para mostrar la nueva venta
    else:
        form = VentaForm()

    productos = Producto.objects.all()

    return render(request, 'administracion.html', {
        'form': form,
        'ventas': ventas,
        'productos': productos,
        'canal': canal,
        'producto_id': producto_id,
        'origen': origen,
    })


from django.shortcuts import render, get_object_or_404, redirect
from .models import Venta
from .forms import VentaForm

def editar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            return redirect('administracion_ventas')
    else:
        form = VentaForm(instance=venta)
    return render(request, 'editar_venta.html', {'form': form, 'venta': venta})

def eliminar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    if request.method == 'POST':
        venta.delete()
        return redirect('administracion_ventas')
    return render(request, 'eliminar_venta.html', {'venta': venta})


from .forms import DatosContactoForm

def confirmar_pago(request):
    productos = obtener_productos_del_carrito(request)
    total = calcular_total(productos)

    if request.method == 'POST':
        contacto_form = DatosContactoForm(request.POST)
        comprobante = request.FILES.get('comprobante')

        if contacto_form.is_valid() and comprobante:
            contacto_form.save()
            guardar_comprobante(comprobante)
            return redirect('pago_exitoso')

    else:
        contacto_form = DatosContactoForm()

    return render(request, 'confirmar_pago.html', {
        'productos': productos,
        'total': total,
        'contacto_form': contacto_form
    })

from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Venta
import json
from collections import defaultdict

def panel_ventas(request):
    ventas = Venta.objects.all()

    total_ventas = ventas.count()
    ingresos_totales = ventas.aggregate(Sum('precio_venta'))['precio_venta__sum'] or 0
    utilidad_total = sum([v.utilidad for v in ventas])  # ✅ KPI utilidad total
    margen_promedio = round(sum([v.margen for v in ventas]) / total_ventas, 2) if total_ventas > 0 else 0  # ✅ KPI margen promedio

    # ✅ Margen por canal específico (usando valores correctos)
    ventas_ml = ventas.filter(canal='mercado_libre')
    ventas_fb = ventas.filter(canal='facebook')

    margen_ml = round(sum([v.margen for v in ventas_ml]) / ventas_ml.count(), 2) if ventas_ml.exists() else 0
    margen_fb = round(sum([v.margen for v in ventas_fb]) / ventas_fb.count(), 2) if ventas_fb.exists() else 0

    producto_top = ventas.values('producto__nombre').annotate(cantidad=Count('producto')).order_by('-cantidad').first()
    producto_top_nombre = producto_top['producto__nombre'] if producto_top else 'Sin datos'

    canal_top = ventas.values('canal').annotate(cantidad=Count('canal')).order_by('-cantidad').first()
    canal_top_nombre = canal_top['canal'] if canal_top else 'Sin datos'

    # ✅ Ventas por día
    ventas_por_dia = ventas.values('fecha_venta').annotate(total=Sum('precio_venta')).order_by('fecha_venta')
    fechas = [str(v['fecha_venta']) for v in ventas_por_dia]
    montos = [float(v['total']) for v in ventas_por_dia]
    ventas_por_dia_json = json.dumps({
        'labels': fechas,
        'datasets': [{
            'label': 'Ventas por día',
            'data': montos,
            'borderColor': 'rgba(75, 192, 192, 1)',
            'fill': False
        }]
    })

    # ✅ Productos más vendidos
    productos = ventas.values('producto__nombre').annotate(cantidad=Count('producto')).order_by('-cantidad')[:5]
    productos_top_json = json.dumps({
        'labels': [p['producto__nombre'] for p in productos],
        'datasets': [{
            'label': 'Top productos',
            'data': [int(p['cantidad']) for p in productos],
            'backgroundColor': 'rgba(153, 102, 255, 0.6)'
        }]
    })

    # ✅ Distribución por canal
    canales = ventas.values('canal').annotate(cantidad=Count('canal'))
    canales_json = json.dumps({
        'labels': [c['canal'] for c in canales],
        'datasets': [{
            'label': 'Canales',
            'data': [int(c['cantidad']) for c in canales],
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9575cd']
        }]
    })

    # ✅ Distribución por origen
    origenes = ventas.values('origen').annotate(cantidad=Count('origen'))
    origenes_json = json.dumps({
        'labels': [o['origen'] for o in origenes],
        'datasets': [{
            'label': 'Origen',
            'data': [int(o['cantidad']) for o in origenes],
            'backgroundColor': ['#81c784', '#aed581']
        }]
    })

    # ✅ Ingresos y utilidad por mes
    ingresos_por_mes = defaultdict(float)
    utilidad_por_mes = defaultdict(float)

    for v in ventas:
        mes = v.fecha_venta.strftime('%Y-%m')  # formato YYYY-MM
        ingresos_por_mes[mes] += float(v.precio_venta)
        utilidad_por_mes[mes] += float(v.utilidad)

    meses_ordenados = sorted(ingresos_por_mes.keys())

    ingresos_mes_json = json.dumps({
        'labels': meses_ordenados,
        'datasets': [{
            'label': 'Ingresos por mes',
            'data': [round(ingresos_por_mes[mes], 2) for mes in meses_ordenados],
            'backgroundColor': 'rgba(100, 181, 246, 0.6)'
        }]
    })

    utilidad_mes_json = json.dumps({
        'labels': meses_ordenados,
        'datasets': [{
            'label': 'Utilidad por mes',
            'data': [round(utilidad_por_mes[mes], 2) for mes in meses_ordenados],
            'backgroundColor': 'rgba(255, 138, 101, 0.6)'
        }]
    })

    return render(request, 'panel_ventas.html', {
        'total_ventas': total_ventas,
        'ingresos_totales': f"{int(ingresos_totales):,}".replace(",", "."),
        'utilidad_total': f"{int(utilidad_total):,}".replace(",", "."),
        'margen_promedio': margen_promedio,
        'margen_ml': margen_ml,
        'margen_fb': margen_fb,
        'producto_top': producto_top_nombre,
        'canal_top': canal_top_nombre,
        'ventas_por_dia_json': ventas_por_dia_json,
        'productos_top_json': productos_top_json,
        'canales_json': canales_json,
        'origenes_json': origenes_json,
        'ingresos_mes_json': ingresos_mes_json,
        'utilidad_mes_json': utilidad_mes_json,
        'ventas': ventas,  # ✅ agregado para tabla y formulario
    })