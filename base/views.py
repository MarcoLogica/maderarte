import pandas as pd
import subprocess
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Accion, DecisionBot, ProductoVideo, BeneficioProducto, UsoRealProducto, PreguntaFrecuenteProducto, \
    ProductoRelacionado, RegistroEntrega


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
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')

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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Producto

@login_required(login_url='/login/')

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

        # Crear un objeto temporal con atributos dinámicos
        item = type('ItemCarrito', (), {})()
        item.id = producto.id
        item.nombre = producto.nombre
        item.imagen = producto.imagen
        item.precio = producto.precio
        item.cantidad = cantidad
        item.subtotal = producto.precio * cantidad

        productos.append(item)
        total += item.subtotal

    return render(request, 'carrito.html', {'productos': productos, 'total': total})



def eliminar_del_carrito(request, id):
    carrito = request.session.get('carrito', {})
    if str(id) in carrito:
        del carrito[str(id)]
    request.session['carrito'] = carrito
    return redirect('ver_carrito')


from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.conf import settings
from .models import Producto, Pieza, ConfiguracionProducto, Orden, OrdenItem
from .forms import DatosContactoForm
from .models import Producto, Pieza, ConfiguracionProducto, Orden, OrdenItem, QuiebreStock



def pago(request):
    carrito = request.session.get('carrito', {})
    productos = []
    total = 0

    # ---------------------------------------------------------
    # 1) Reconstruir productos del carrito
    # ---------------------------------------------------------
    for id, cantidad in carrito.items():
        producto = Producto.objects.get(id=id)
        producto.cantidad = cantidad
        producto.subtotal = producto.precio * cantidad
        productos.append(producto)
        total += producto.subtotal

    # Texto para correos
    detalle_productos = "🛍️ Detalle de productos:\n"
    for p in productos:
        detalle_productos += f"- {p.nombre} (x{p.cantidad}): ${p.precio} → Subtotal: ${p.subtotal}\n"
    detalle_productos += f"\nTOTAL: ${total}\n"

    # ---------------------------------------------------------
    # 2) Si el usuario envía el formulario
    # ---------------------------------------------------------
    if request.method == 'POST':
        contacto_form = DatosContactoForm(request.POST)
        comprobante = request.FILES.get('comprobante')

        if contacto_form.is_valid() and comprobante:
            datos = contacto_form.save()

            # Datos del cliente
            nombre = datos.nombre
            direccion = datos.direccion
            correo = datos.correo_electronico
            telefono = datos.telefono

            # ---------------------------------------------------------
            # 3) Crear la ORDEN
            # ---------------------------------------------------------
            orden = Orden(
                nombre=nombre,
                direccion=direccion,
                correo_electronico=correo,
                telefono=telefono,
                comprobante=comprobante,
                total=total
            )
            orden.save()  # ⭐ AQUÍ SÍ SE EJECUTA TU MÉTODO save() Y SE GENERA EL CÓDIGO

            # ---------------------------------------------------------
            # 4) Crear los ORDENITEMS y rebajar stock de piezas
            # ---------------------------------------------------------
            for p in productos:
                # Crear item
                OrdenItem.objects.create(
                    orden=orden,
                    producto=p,
                    cantidad=p.cantidad,
                    precio_unitario=p.precio
                )

                # Rebajar stock comercial (solo ecommerce)
                p.stock_comercial -= p.cantidad
                p.save()

            # ---------------------------------------------------------
            # 5) Enviar correo interno a Vipalú
            # ---------------------------------------------------------
            cuerpo_admin = (
                f"Se ha recibido un pago por ${total}.\n"
                f"Cliente: {nombre}\n"
                f"Correo: {correo}\n\n"
                f"{detalle_productos}"
            )

            email_admin = EmailMessage(
                subject='Nuevo pago recibido',
                body=cuerpo_admin,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['marco.sepulvedam85@gmail.com'],
            )

            email_admin.attach(comprobante.name, comprobante.read(), comprobante.content_type)
            email_admin.send()

            # ---------------------------------------------------------
            # 6) Enviar correo al cliente
            # ---------------------------------------------------------
            cuerpo_cliente = f"""
            Hola {nombre},

            ¡Gracias por elegir Vipalú!
            Recibimos tu comprobante de pago y ya estamos revisando tu pedido.

            {detalle_productos}

            Envío a:
            {direccion}

            Contacto:
            {correo} / {telefono}

            🔎 Seguimiento de tu pedido:
            Tu código de seguimiento es: {orden.codigo_seguimiento}

            Puedes ver el estado de tu pedido aquí:
            https://maderarte.pythonanywhere.com/tracking/{orden.codigo_seguimiento}/

            Nuestro equipo confirmará tu pago y te avisaremos cuando tu pedido esté listo para despacho.

            Un abrazo,
            Equipo Vipalú 💛
            """

            email_cliente = EmailMessage(
                subject='¡Gracias por tu compra! Estamos procesando tu pago 💛',
                body=cuerpo_cliente,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo],
            )
            email_cliente.send()

            # ---------------------------------------------------------
            # 7) Vaciar carrito
            # ---------------------------------------------------------
            request.session['carrito'] = {}

            return redirect('exito')

    else:
        contacto_form = DatosContactoForm()

    return render(request, 'pago.html', {
        'productos': productos,
        'total': total,
        'form': contacto_form
    })



from django.shortcuts import render, redirect
from .models import Venta, Producto
from .forms import VentaForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Venta, Producto
from .forms import VentaForm


@login_required(login_url='/login/')
  # 👈 ESTA ES LA LÍNEA CLAVE
def administracion_ventas(request):
    user = request.user

    # 1. FILTRAR SEGÚN EL USUARIO
    if user.username == "marco":
        ventas = Venta.objects.all()
    else:
        ventas = Venta.objects.filter(vendedor=user)

    # 2. ORDENAR
    ventas = ventas.order_by('-fecha_venta')

    # 3. FILTROS EXISTENTES
    canal = request.GET.get('canal')
    producto_id = request.GET.get('producto')
    origen = request.GET.get('origen')

    if canal:
        ventas = ventas.filter(canal=canal)
    if producto_id:
        ventas = ventas.filter(producto_id=producto_id)
    if origen:
        ventas = ventas.filter(origen=origen)

    # 4. FORMULARIO PARA CREAR VENTAS
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            nueva_venta = form.save(commit=False)

            # Si NO eres Marco, asigna automáticamente el vendedor
            if user.username != "marco":
                nueva_venta.vendedor = user

            nueva_venta.save()
            return redirect('administracion_ventas')
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

from django.db.models import Sum, Count
from .models import Venta, UsuarioPerfil
import json
from collections import defaultdict

def panel_ventas(request):

    # ============================================================
    # 🔥 FILTRO DE VENTAS SEGÚN PERFIL
    # ============================================================
    usuario_perfil = UsuarioPerfil.objects.get(usuario=request.user)
    perfil = usuario_perfil.perfil

    # Marco (superusuario) ve TODO
    if request.user.is_superuser or perfil.nombre.lower() == "marco":
        ventas = Venta.objects.all()
    else:
        # Cada vendedor ve SOLO sus ventas
        ventas = Venta.objects.filter(vendedor=request.user)

    # ============================================================
    # 🔥 TODO LO DEMÁS QUEDA EXACTAMENTE IGUAL
    # ============================================================

    total_ventas = ventas.count()
    ingresos_totales = ventas.aggregate(Sum('precio_venta'))['precio_venta__sum'] or 0
    utilidad_total = sum([v.utilidad for v in ventas])
    margen_promedio = round(sum([v.margen for v in ventas]) / total_ventas, 2) if total_ventas > 0 else 0

    ventas_ml = ventas.filter(canal='mercado_libre')
    ventas_fb = ventas.filter(canal='facebook')

    margen_ml = round(sum([v.margen for v in ventas_ml]) / ventas_ml.count(), 2) if ventas_ml.exists() else 0
    margen_fb = round(sum([v.margen for v in ventas_fb]) / ventas_fb.count(), 2) if ventas_fb.exists() else 0

    producto_top = ventas.values('producto__nombre').annotate(cantidad=Count('producto')).order_by('-cantidad').first()
    producto_top_nombre = producto_top['producto__nombre'] if producto_top else 'Sin datos'

    canal_top = ventas.values('canal').annotate(cantidad=Count('canal')).order_by('-cantidad').first()
    canal_top_nombre = canal_top['canal'] if canal_top else 'Sin datos'

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

    productos = ventas.values('producto__nombre').annotate(cantidad=Count('producto')).order_by('-cantidad')[:5]
    productos_top_json = json.dumps({
        'labels': [p['producto__nombre'] for p in productos],
        'datasets': [{
            'label': 'Top productos',
            'data': [int(p['cantidad']) for p in productos],
            'backgroundColor': 'rgba(153, 102, 255, 0.6)'
        }]
    })

    canales = ventas.values('canal').annotate(cantidad=Count('canal'))
    canales_json = json.dumps({
        'labels': [c['canal'] for c in canales],
        'datasets': [{
            'label': 'Canales',
            'data': [int(c['cantidad']) for c in canales],
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9575cd']
        }]
    })

    origenes = ventas.values('origen').annotate(cantidad=Count('origen'))
    origenes_json = json.dumps({
        'labels': [o['origen'] for o in origenes],
        'datasets': [{
            'label': 'Origen',
            'data': [int(o['cantidad']) for o in origenes],
            'backgroundColor': ['#81c784', '#aed581']
        }]
    })

    ingresos_por_mes = defaultdict(float)
    utilidad_por_mes = defaultdict(float)

    for v in ventas:
        mes = v.fecha_venta.strftime('%Y-%m')
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
        'ventas': ventas,
    })


####### perfilamiento de usuarios


from django.shortcuts import render, redirect
from .models import Perfil, UsuarioPerfil
from .forms import PerfilForm, UsuarioPerfilForm

def panel_perfiles(request):
    perfiles = Perfil.objects.all()
    usuarios_perfil = UsuarioPerfil.objects.select_related('usuario', 'perfil')

    perfil_form = PerfilForm()
    usuario_perfil_form = UsuarioPerfilForm()

    if request.method == 'POST':
        if 'crear_perfil' in request.POST:
            perfil_form = PerfilForm(request.POST)
            if perfil_form.is_valid():
                perfil_form.save()
                return redirect('panel_perfiles')

        if 'crear_usuario_perfil' in request.POST:
            usuario_perfil_form = UsuarioPerfilForm(request.POST)
            if usuario_perfil_form.is_valid():
                usuario_perfil_form.save()
                return redirect('panel_perfiles')

    return render(request, 'panel_perfiles.html', {
        'perfiles': perfiles,
        'usuarios_perfil': usuarios_perfil,
        'perfil_form': perfil_form,
        'usuario_perfil_form': usuario_perfil_form,
    })

from .forms import CrearUsuarioForm

def panel_perfiles(request):
    perfiles = Perfil.objects.all()
    usuarios_perfil = UsuarioPerfil.objects.select_related('usuario', 'perfil')

    perfil_form = PerfilForm()
    usuario_perfil_form = UsuarioPerfilForm()
    crear_usuario_form = CrearUsuarioForm()

    if request.method == 'POST':

        # Crear perfil
        if 'crear_perfil' in request.POST:
            perfil_form = PerfilForm(request.POST)
            if perfil_form.is_valid():
                perfil_form.save()
                return redirect('panel_perfiles')

        # Asignar perfil
        if 'crear_usuario_perfil' in request.POST:
            usuario_perfil_form = UsuarioPerfilForm(request.POST)
            if usuario_perfil_form.is_valid():
                usuario_perfil_form.save()
                return redirect('panel_perfiles')

        # Crear usuario
        if 'crear_usuario' in request.POST:
            crear_usuario_form = CrearUsuarioForm(request.POST)
            if crear_usuario_form.is_valid():
                user = crear_usuario_form.save(commit=False)
                user.set_password(crear_usuario_form.cleaned_data['password'])
                user.save()
                return redirect('panel_perfiles')

    return render(request, 'panel_perfiles.html', {
        'perfiles': perfiles,
        'usuarios_perfil': usuarios_perfil,
        'perfil_form': perfil_form,
        'usuario_perfil_form': usuario_perfil_form,
        'crear_usuario_form': crear_usuario_form,
    })

def acceso_denegado(request):
    return render(request, 'acceso_denegado.html')

def editar_perfil(request, id):
    perfil = Perfil.objects.get(id=id)

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('panel_perfiles')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'editar_perfil.html', {
        'form': form,
        'perfil': perfil
    })


# carga de videos en fortalezas

from django.shortcuts import render, redirect, get_object_or_404
from .models import Fortaleza

def subir_media_fortaleza(request, id):
    fortaleza = get_object_or_404(Fortaleza, id=id)

    if request.method == 'POST':
        if 'imagen' in request.FILES:
            fortaleza.imagen = request.FILES['imagen']
        if 'video' in request.FILES:
            fortaleza.video = request.FILES['video']
        fortaleza.save()

    return redirect('home')


def lista_fortalezas(request):
    fortalezas = Fortaleza.objects.all()
    return render(request, 'fortalezas_list.html', {'fortalezas': fortalezas})

def crear_fortaleza(request):
    if request.method == 'POST':
        Fortaleza.objects.create(
            titulo=request.POST['titulo'],
            descripcion=request.POST['descripcion'],
            imagen=request.FILES.get('imagen'),
            video=request.FILES.get('video'),
        )
        return redirect('lista_fortalezas')
    return render(request, 'crear_fortaleza.html')

def editar_fortaleza(request, id):
    fortaleza = get_object_or_404(Fortaleza, id=id)
    if request.method == 'POST':
        fortaleza.titulo = request.POST['titulo']
        fortaleza.descripcion = request.POST['descripcion']
        if 'imagen' in request.FILES:
            fortaleza.imagen = request.FILES['imagen']
        if 'video' in request.FILES:
            fortaleza.video = request.FILES['video']
        fortaleza.save()
        return redirect('lista_fortalezas')
    return render(request, 'editar_fortaleza.html', {'fortaleza': fortaleza})

def eliminar_fortaleza(request, id):
    fortaleza = get_object_or_404(Fortaleza, id=id)
    fortaleza.delete()
    return redirect('lista_fortalezas')




def home(request):
    fortalezas = Fortaleza.objects.all()
    productos = Producto.objects.filter(destacado=True)[:6]
    ofertas = Oferta.objects.all()
    testimonios = Testimonio.objects.all()

    return render(request, 'home.html', {
        'fortalezas': fortalezas,
        'productos': productos,
        'ofertas': ofertas,
        'testimonios': testimonios,
    })



from .models import Oferta

def lista_ofertas(request):
    ofertas = Oferta.objects.all()
    return render(request, 'ofertas_list.html', {'ofertas': ofertas})

def crear_oferta(request):
    if request.method == 'POST':
        Oferta.objects.create(
            titulo=request.POST['titulo'],
            descripcion=request.POST['descripcion'],
            imagen=request.FILES.get('imagen'),
            video=request.FILES.get('video'),
        )
        return redirect('lista_ofertas')
    return render(request, 'crear_oferta.html')

def editar_oferta(request, id):
    oferta = get_object_or_404(Oferta, id=id)
    if request.method == 'POST':
        oferta.titulo = request.POST['titulo']
        oferta.descripcion = request.POST['descripcion']
        if 'imagen' in request.FILES:
            oferta.imagen = request.FILES['imagen']
        if 'video' in request.FILES:
            oferta.video = request.FILES['video']
        oferta.save()
        return redirect('lista_ofertas')
    return render(request, 'editar_oferta.html', {'oferta': oferta})

def eliminar_oferta(request, id):
    oferta = get_object_or_404(Oferta, id=id)
    oferta.delete()
    return redirect('lista_ofertas')


from .models import Testimonio

def lista_testimonios(request):
    testimonios = Testimonio.objects.all()
    return render(request, 'testimonios_list.html', {'testimonios': testimonios})

def crear_testimonio(request):
    if request.method == 'POST':
        Testimonio.objects.create(
            titulo=request.POST['titulo'],
            comentario=request.POST['comentario'],
            imagen=request.FILES.get('imagen'),
            imagen2=request.FILES.get('imagen2'),
        )
        return redirect('lista_testimonios')

    return render(request, 'crear_testimonio.html')


def editar_testimonio(request, id):
    testimonio = get_object_or_404(Testimonio, id=id)
    if request.method == 'POST':
        testimonio.titulo = request.POST['titulo']
        testimonio.comentario = request.POST['comentario']
        if 'imagen' in request.FILES:
            testimonio.imagen = request.FILES['imagen']
        testimonio.save()
        return redirect('lista_testimonios')
    return render(request, 'editar_testimonio.html', {'testimonio': testimonio})

def eliminar_testimonio(request, id):
    testimonio = get_object_or_404(Testimonio, id=id)
    testimonio.delete()
    return redirect('lista_testimonios')


# panel control de stock


from django.shortcuts import render, redirect, get_object_or_404
from .models import Pieza, ConfiguracionProducto, MovimientoStockPieza, Producto
from django.contrib import messages
from django.utils import timezone


def piezas_list(request):
    piezas = Pieza.objects.all()
    return render(request, "piezas_list.html", {"piezas": piezas})

def pieza_create(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        descripcion = request.POST.get("descripcion", "")
        stock = int(request.POST.get("stock", 0))

        pieza = Pieza.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            stock=stock
        )

        MovimientoStockPieza.objects.create(
            pieza=pieza,
            cantidad=stock,
            motivo="Carga inicial"
        )

        messages.success(request, "Pieza creada correctamente.")
        return redirect("piezas_list")

    return render(request, "pieza_create.html")


def pieza_edit(request, pieza_id):
    pieza = get_object_or_404(Pieza, id=pieza_id)

    if request.method == "POST":
        pieza.nombre = request.POST["nombre"]
        pieza.descripcion = request.POST.get("descripcion", "")
        pieza.save()

        messages.success(request, "Pieza actualizada.")
        return redirect("piezas_list")

    return render(request, "pieza_edit.html", {"pieza": pieza})


def pieza_delete(request, pieza_id):
    pieza = get_object_or_404(Pieza, id=pieza_id)
    pieza.delete()
    messages.success(request, "Pieza eliminada.")
    return redirect("piezas_list")


def configuracion_list(request):
    productos = Producto.objects.all()
    producto_seleccionado = None
    configuraciones = []

    if request.method == "POST":
        producto_id = request.POST["producto_id"]
        producto_seleccionado = Producto.objects.get(id=producto_id)
        configuraciones = ConfiguracionProducto.objects.filter(producto=producto_seleccionado)

    return render(request, "configuracion_list.html", {
        "productos": productos,
        "producto_seleccionado": producto_seleccionado,
        "configuraciones": configuraciones,
    })


def configuracion_create(request):
    productos = Producto.objects.all()
    piezas = Pieza.objects.all()

    if request.method == "POST":
        producto_id = request.POST["producto"]
        pieza_id = request.POST["pieza"]
        cantidad = int(request.POST["cantidad"])

        ConfiguracionProducto.objects.create(
            producto_id=producto_id,
            pieza_id=pieza_id,
            cantidad_necesaria=cantidad
        )

        messages.success(request, "Configuración agregada.")
        return redirect("configuracion_list")

    return render(request, "configuracion_create.html", {
        "productos": productos,
        "piezas": piezas,
    })


def configuracion_delete(request, config_id):
    config = get_object_or_404(ConfiguracionProducto, id=config_id)
    config.delete()
    messages.success(request, "Configuración eliminada.")
    return redirect("configuracion_list")


def control_stock(request):
    productos = Producto.objects.all()
    producto_seleccionado = None
    configuraciones = []
    stock_total = 0

    # Selección de producto
    if request.method == "POST" and "producto_id" in request.POST:
        producto_seleccionado = Producto.objects.get(id=request.POST["producto_id"])

    # Ajuste de stock
    if request.method == "POST" and "pieza_id" in request.POST:
        pieza = Pieza.objects.get(id=request.POST["pieza_id"])
        ajuste = int(request.POST["ajuste"])
        motivo = request.POST.get("motivo", "Ajuste manual")

        pieza.stock += ajuste
        pieza.save()

        MovimientoStockPieza.objects.create(
            pieza=pieza,
            cantidad=ajuste,
            motivo=motivo
        )

        messages.success(request, "Stock actualizado correctamente.")

        # Mantener producto seleccionado
        producto_seleccionado = Producto.objects.get(id=request.POST["producto_actual"])

    # Si hay producto seleccionado, cargar configuraciones
    if producto_seleccionado:
        configuraciones = ConfiguracionProducto.objects.filter(producto=producto_seleccionado)

        stock_total = producto_seleccionado.stock_disponible()


    return render(request, "control_stock.html", {
        "productos": productos,
        "producto_seleccionado": producto_seleccionado,
        "configuraciones": configuraciones,
        "stock_total": stock_total,
    })

def movimientos_pieza(request, pieza_id):
    pieza = get_object_or_404(Pieza, id=pieza_id)
    movimientos = MovimientoStockPieza.objects.filter(pieza=pieza).order_by("-fecha")

    return render(request, "movimientos_pieza.html", {
        "pieza": pieza,
        "movimientos": movimientos,
    })

def exito(request):
    return render(request, 'exito.html')


# panel de ordenes

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


def panel_ordenes(request):
    estado_filtro = request.GET.get("estado", "")

    if estado_filtro:
        ordenes = Orden.objects.filter(estado=estado_filtro).order_by("-fecha")
    else:
        ordenes = Orden.objects.all().order_by("-fecha")

    # -----------------------------
    # MÉTRICAS OPERATIVAS
    # -----------------------------

    # 0) Órdenes pendientes
    pendientes_count = Orden.objects.filter(estado="pendiente").count()

    # 1) Órdenes en producción
    produccion_count = Orden.objects.filter(estado="produccion").count()

    # 2) Órdenes listas para envío
    listas_envio_count = Orden.objects.filter(estado="listo").count()

    # 3) Órdenes con quiebre
    ordenes_con_quiebre_count = Orden.objects.filter(
        quiebrestock__isnull=False
    ).distinct().count()

    # 4) Ventas mes actual vs mes anterior
    hoy = timezone.now().date()
    primer_dia_mes_actual = hoy.replace(day=1)

    mes_anterior_fin = primer_dia_mes_actual - timedelta(days=1)
    mes_anterior_inicio = mes_anterior_fin.replace(day=1)

    ventas_mes_actual = Orden.objects.filter(
        fecha__date__gte=primer_dia_mes_actual
    ).aggregate(total=Sum("total"))["total"] or 0

    ventas_mes_anterior = Orden.objects.filter(
        fecha__date__gte=mes_anterior_inicio,
        fecha__date__lte=mes_anterior_fin
    ).aggregate(total=Sum("total"))["total"] or 0

    if ventas_mes_anterior > 0:
        variacion_porcentaje = ((ventas_mes_actual - ventas_mes_anterior) / ventas_mes_anterior) * 100
    else:
        variacion_porcentaje = 0

        # 5) Órdenes entregadas
        entregados_count = Orden.objects.filter(estado="entregado").count()

    return render(request, "panel_ordenes.html", {
        "ordenes": ordenes,
        "estado_filtro": estado_filtro,

        # métricas
        "pendientes_count": pendientes_count,
        "produccion_count": produccion_count,
        "listas_envio_count": listas_envio_count,
        "ordenes_con_quiebre_count": ordenes_con_quiebre_count,
        "ventas_mes_actual": ventas_mes_actual,
        "ventas_mes_anterior": ventas_mes_anterior,
        "variacion_porcentaje": variacion_porcentaje,
        "entregados_count": entregados_count,

    })


def cambiar_estado_orden(request, orden_id, nuevo_estado):
    orden = Orden.objects.get(id=orden_id)
    orden.estado = nuevo_estado
    orden.save()

    messages.success(request, f"Orden #{orden.id} actualizada a '{nuevo_estado}'.")
    return redirect("panel_ordenes")


# panel de quiebres de stock

def panel_quiebres(request):
    quiebres = QuiebreStock.objects.filter(resuelto=False).order_by("-fecha")

    return render(request, "panel_quiebres.html", {
        "quiebres": quiebres
    })

def resolver_quiebre(request, quiebre_id):
    quiebre = QuiebreStock.objects.get(id=quiebre_id)
    quiebre.resuelto = True
    quiebre.save()

    messages.success(request, "Quiebre marcado como resuelto.")
    return redirect("panel_quiebres")

#panel de produccion

from django.utils import timezone

from django.utils import timezone
from django.utils import timezone

from django.utils import timezone

def panel_produccion(request):
    ordenes = Orden.objects.filter(estado="produccion").order_by("fecha")

    data_ordenes = []

    # -----------------------------
    # MÉTRICAS DEL PANEL SUPERIOR
    # -----------------------------
    total_produccion = 0
    total_riesgo = 0
    total_retrasadas = 0
    total_tiempo = 0

    for orden in ordenes:
        items = OrdenItem.objects.filter(orden=orden)

        piezas_necesarias = []
        piezas_faltantes = False

        # DÍAS EN PRODUCCIÓN
        dias_en_produccion = (timezone.now() - orden.fecha).days

        # CLASIFICACIÓN
        total_produccion += 1

        if dias_en_produccion > 3:
            total_retrasadas += 1
        elif dias_en_produccion > 1:
            total_riesgo += 1
        else:
            total_tiempo += 1

        # PIEZAS NECESARIAS
        for item in items:
            configuraciones = ConfiguracionProducto.objects.filter(producto=item.producto)

            for config in configuraciones:
                total_necesarias = config.cantidad_necesaria * item.cantidad
                stock_actual = config.pieza.stock
                faltan = max(0, total_necesarias - stock_actual)

                if faltan > 0:
                    piezas_faltantes = True

                piezas_necesarias.append({
                    "pieza": config.pieza.nombre,
                    "necesarias": total_necesarias,
                    "stock": stock_actual,
                    "faltan": faltan,
                })

        data_ordenes.append({
            "orden": orden,
            "piezas": piezas_necesarias,
            "faltantes": piezas_faltantes,
            "dias_en_produccion": dias_en_produccion,
            "direccion": orden.direccion,
        })

    return render(request, "panel_produccion.html", {
        "ordenes": data_ordenes,
        "total_produccion": total_produccion,
        "total_riesgo": total_riesgo,
        "total_retrasadas": total_retrasadas,
        "total_tiempo": total_tiempo,
    })



def marcar_fabricado(request, orden_id):
    orden = Orden.objects.get(id=orden_id)
    orden.estado = "listo"
    orden.save()

    # Obtener items de la orden
    items = OrdenItem.objects.filter(orden=orden)

    for item in items:
        producto = item.producto

        # 1) Rebajar piezas según receta (producción real)
        configuraciones = ConfiguracionProducto.objects.filter(producto=producto)

        for config in configuraciones:
            pieza = config.pieza
            piezas_a_rebajar = config.cantidad_necesaria * item.cantidad

            pieza.stock -= piezas_a_rebajar
            pieza.save()

        # 2) Actualizar stock comercial según stock disponible real
        producto.stock_comercial = producto.stock_disponible()
        producto.save()

    messages.success(request, f"Orden #{orden.id} marcada como fabricada.")
    return redirect("panel_produccion")



# dashboard stock

def dashboard_stock(request):
    piezas = Pieza.objects.all()

    piezas_quiebre = []
    piezas_criticas = []
    piezas_bajo = []
    piezas_ok = []

    # Datos para gráficos de stock
    nombres_piezas = []
    stock_piezas = []

    for p in piezas:
        nombres_piezas.append(p.nombre)
        stock_piezas.append(p.stock)

        if p.stock < 0:
            piezas_quiebre.append(p)
        elif p.stock < 5:
            piezas_criticas.append(p)
        elif p.stock < 15:
            piezas_bajo.append(p)
        else:
            piezas_ok.append(p)

    # ⭐⭐⭐ AQUÍ VA EL CÁLCULO DE CAPACIDAD DE FABRICACIÓN ⭐⭐⭐
    productos = Producto.objects.all()
    capacidad_fabricacion = []

    for prod in productos:
        configuraciones = ConfiguracionProducto.objects.filter(producto=prod)

        if not configuraciones.exists():
            continue

        capacidades = []

        for config in configuraciones:
            if config.cantidad_necesaria > 0:
                capacidad = config.pieza.stock // config.cantidad_necesaria
                capacidades.append(capacidad)

        if capacidades:
            capacidad_fabricacion.append(min(capacidades))

    # ⭐ TOTAL DE UNIDADES QUE PUEDES FABRICAR HOY
    total_capacidad = sum(capacidad_fabricacion)

    return render(request, "dashboard_stock.html", {
        "piezas_quiebre": piezas_quiebre,
        "piezas_criticas": piezas_criticas,
        "piezas_bajo": piezas_bajo,
        "piezas_ok": piezas_ok,
        "nombres_piezas": nombres_piezas,
        "stock_piezas": stock_piezas,
        "total_capacidad": total_capacidad,
    })


# tracking clientes

def tracking(request, codigo):
    try:
        orden = Orden.objects.get(codigo_seguimiento=codigo)
    except Orden.DoesNotExist:
        return render(request, "tracking_no_encontrado.html")

    estados = [
        "pendiente",
        "produccion",
        "listo",
        "enviado",
        "entregado"
    ]

    progreso = {
        "pendiente": 20,
        "produccion": 40,
        "listo": 60,
        "enviado": 80,
        "entregado": 100,
    }

    # ⭐ Traer los productos asociados a la orden
    items = OrdenItem.objects.filter(orden=orden)

    return render(request, "tracking.html", {
        "orden": orden,
        "items": items,  # ⭐ Enviamos los items al template
        "estados": estados,
        "progreso": progreso[orden.estado],
    })

def buscar_tracking(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")
        return redirect("tracking", codigo=codigo)

    return render(request, "buscar_tracking.html")



#### administración videos de fabricación en detalle producto

def administrar_videos_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    videos = ProductoVideo.objects.filter(producto=producto).order_by('orden')

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        video = request.FILES.get("video")

        if video:
            ProductoVideo.objects.create(
                producto=producto,
                titulo=titulo,
                video=video
            )

        return redirect("administrar_videos_producto", producto_id=producto.id)

    return render(request, "admin_videos_producto.html", {
        "producto": producto,
        "videos": videos
    })

def eliminar_video_producto(request, video_id):
    video = get_object_or_404(ProductoVideo, id=video_id)
    producto_id = video.producto.id
    video.delete()
    return redirect("administrar_videos_producto", producto_id=producto_id)


def editar_video_producto(request, video_id):
    video = get_object_or_404(ProductoVideo, id=video_id)

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        archivo = request.FILES.get("video")

        video.titulo = titulo

        if archivo:
            video.video = archivo  # reemplaza el archivo si se sube uno nuevo

        video.save()

        return redirect("administrar_videos_producto", producto_id=video.producto.id)

    return render(request, "editar_video_producto.html", {
        "video": video
    })


#beneficios productos

def administrar_beneficios_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    beneficios = producto.beneficios.all().order_by("orden")

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        icono = request.POST.get("icono")

        BeneficioProducto.objects.create(
            producto=producto,
            titulo=titulo,
            descripcion=descripcion,
            icono=icono
        )

        return redirect("administrar_beneficios_producto", producto_id=producto.id)

    return render(request, "admin_beneficios_producto.html", {
        "producto": producto,
        "beneficios": beneficios
    })

def editar_beneficio_producto(request, beneficio_id):
    beneficio = get_object_or_404(BeneficioProducto, id=beneficio_id)

    if request.method == "POST":
        beneficio.titulo = request.POST.get("titulo")
        beneficio.descripcion = request.POST.get("descripcion")
        beneficio.icono = request.POST.get("icono")
        beneficio.save()

        return redirect("administrar_beneficios_producto", producto_id=beneficio.producto.id)

    return render(request, "editar_beneficio_producto.html", {
        "beneficio": beneficio
    })


def eliminar_beneficio_producto(request, beneficio_id):
    beneficio = get_object_or_404(BeneficioProducto, id=beneficio_id)
    producto_id = beneficio.producto.id
    beneficio.delete()
    return redirect("administrar_beneficios_producto", producto_id=producto_id)

#uso real

def administrar_uso_real_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    usos = producto.usos_reales.all().order_by("orden")

    if request.method == "POST":
        imagen = request.FILES.get("imagen")
        video = request.FILES.get("video")

        UsoRealProducto.objects.create(
            producto=producto,
            imagen=imagen,
            video=video
        )

        return redirect("administrar_uso_real_producto", producto_id=producto.id)

    return render(request, "admin_uso_real_producto.html", {
        "producto": producto,
        "usos": usos
    })

def editar_uso_real_producto(request, uso_id):
    uso = get_object_or_404(UsoRealProducto, id=uso_id)

    if request.method == "POST":
        if request.FILES.get("imagen"):
            uso.imagen = request.FILES.get("imagen")

        if request.FILES.get("video"):
            uso.video = request.FILES.get("video")

        uso.save()
        return redirect("administrar_uso_real_producto", producto_id=uso.producto.id)

    return render(request, "editar_uso_real_producto.html", {
        "uso": uso
    })

def eliminar_uso_real_producto(request, uso_id):
    uso = get_object_or_404(UsoRealProducto, id=uso_id)
    producto_id = uso.producto.id
    uso.delete()
    return redirect("administrar_uso_real_producto", producto_id=producto_id)


#preguntas frecuentes

def administrar_faq_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    faqs = producto.preguntas_frecuentes.all().order_by("orden")

    if request.method == "POST":
        pregunta = request.POST.get("pregunta")
        respuesta = request.POST.get("respuesta")

        PreguntaFrecuenteProducto.objects.create(
            producto=producto,
            pregunta=pregunta,
            respuesta=respuesta
        )

        return redirect("administrar_faq_producto", producto_id=producto.id)

    return render(request, "admin_faq_producto.html", {
        "producto": producto,
        "faqs": faqs
    })

def editar_faq_producto(request, faq_id):
    faq = get_object_or_404(PreguntaFrecuenteProducto, id=faq_id)

    if request.method == "POST":
        faq.pregunta = request.POST.get("pregunta")
        faq.respuesta = request.POST.get("respuesta")
        faq.save()

        return redirect("administrar_faq_producto", producto_id=faq.producto.id)

    return render(request, "editar_faq_producto.html", {"faq": faq})


def eliminar_faq_producto(request, faq_id):
    faq = get_object_or_404(PreguntaFrecuenteProducto, id=faq_id)
    producto_id = faq.producto.id
    faq.delete()
    return redirect("administrar_faq_producto", producto_id=producto_id)


#productos relacionados

def administrar_productos_relacionados(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    relacionados = producto.productos_relacionados.all().order_by("orden")

    if request.method == "POST":
        imagen = request.FILES.get("imagen")
        titulo = request.POST.get("titulo")
        producto_destino_id = request.POST.get("producto_destino")

        ProductoRelacionado.objects.create(
            producto=producto,
            imagen=imagen,
            titulo=titulo,
            producto_destino_id=producto_destino_id
        )

        return redirect("administrar_productos_relacionados", producto_id=producto.id)

    productos = Producto.objects.exclude(id=producto.id)

    return render(request, "admin_productos_relacionados.html", {
        "producto": producto,
        "relacionados": relacionados,
        "productos": productos
    })

def editar_producto_relacionado(request, rel_id):
    rel = get_object_or_404(ProductoRelacionado, id=rel_id)

    if request.method == "POST":
        if request.FILES.get("imagen"):
            rel.imagen = request.FILES.get("imagen")

        rel.titulo = request.POST.get("titulo")
        rel.producto_destino_id = request.POST.get("producto_destino")
        rel.save()

        return redirect("administrar_productos_relacionados", producto_id=rel.producto.id)

    productos = Producto.objects.exclude(id=rel.producto.id)

    return render(request, "editar_producto_relacionado.html", {
        "rel": rel,
        "productos": productos
    })

def eliminar_producto_relacionado(request, rel_id):
    rel = get_object_or_404(ProductoRelacionado, id=rel_id)
    producto_id = rel.producto.id
    rel.delete()
    return redirect("administrar_productos_relacionados", producto_id=producto_id)

#montessori en casa

def montessori_en_casa(request):
    return render(request, 'montessori-en-casa.html')


# carrito de compra

def sumar_cantidad(request, item_id):
    carrito = request.session.get('carrito', {})
    item_id = str(item_id)

    if item_id in carrito:
        carrito[item_id] += 1

    request.session['carrito'] = carrito
    return redirect('ver_carrito')


def restar_cantidad(request, item_id):
    carrito = request.session.get('carrito', {})
    item_id = str(item_id)

    if item_id in carrito and carrito[item_id] > 1:
        carrito[item_id] -= 1

    request.session['carrito'] = carrito
    return redirect('ver_carrito')


# panel de logistica

from .models import Orden, RutaEntrega, RutaOrden, Transportista



def panel_administrativo_rutas(request):
    ordenes_listas = Orden.objects.filter(estado="listo").order_by("fecha")
    transportistas = Transportista.objects.filter(activo=True).order_by("nombre")
    rutas = RutaEntrega.objects.all().order_by("-fecha_creacion")

    return render(request, "panel_administrativo_rutas.html", {
        "ordenes_listas": ordenes_listas,
        "transportistas": transportistas,
        "rutas": rutas,
    })


def generar_ruta(request):
    ordenes_ids = request.POST.getlist("ordenes")
    transportista_id = request.POST.get("transportista")

    # Validaciones
    if not ordenes_ids or not transportista_id:
        # manejar error
        pass

    transportista = Transportista.objects.get(id=transportista_id)

    # Crear ruta
    ruta = RutaEntrega.objects.create(
        transportista=transportista,
        estado="pendiente"
    )

    # Asignar órdenes
    for oid in ordenes_ids:
        orden = Orden.objects.get(id=oid)
        RutaOrden.objects.create(ruta=ruta, orden=orden)
        orden.estado = "enviado"
        orden.save()

    return redirect("panel_administrativo_rutas")



def detalle_ruta(request, ruta_id):
    ruta = RutaEntrega.objects.get(id=ruta_id)

    # Cargar ordenes con la orden real
    ordenes = RutaOrden.objects.filter(ruta=ruta).select_related("orden")

    # Refrescar cada orden desde la base de datos
    for item in ordenes:
        item.orden.refresh_from_db()

    return render(request, "detalle_ruta.html", {
        "ruta": ruta,
        "ordenes": ordenes
    })







def cambiar_estado_ruta(request, ruta_id, nuevo_estado):
    ruta = RutaEntrega.objects.get(id=ruta_id)
    ruta.estado = nuevo_estado
    ruta.save()

    return redirect("detalle_ruta", ruta_id=ruta_id)


def lista_transportistas(request):
    transportistas = Transportista.objects.all().order_by("nombre")

    return render(request, "transportistas_lista.html", {
        "transportistas": transportistas,
    })

def crear_transportista(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        telefono = request.POST.get("telefono")
        correo = request.POST.get("correo")
        vehiculo = request.POST.get("vehiculo")
        patente = request.POST.get("patente")

        Transportista.objects.create(
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            vehiculo=vehiculo,
            patente=patente,
            activo=True
        )

        return redirect("lista_transportistas")

    return render(request, "transportistas_crear.html")


def editar_transportista(request, transportista_id):
    transportista = Transportista.objects.get(id=transportista_id)

    if request.method == "POST":
        transportista.nombre = request.POST.get("nombre")
        transportista.telefono = request.POST.get("telefono")
        transportista.correo = request.POST.get("correo")
        transportista.vehiculo = request.POST.get("vehiculo")
        transportista.patente = request.POST.get("patente")

        transportista.save()

        return redirect("lista_transportistas")

    return render(request, "transportistas_editar.html", {
        "transportista": transportista
    })

def toggle_transportista(request, transportista_id):
    transportista = Transportista.objects.get(id=transportista_id)

    # Cambiar estado
    transportista.activo = not transportista.activo
    transportista.save()

    return redirect("lista_transportistas")


def panel_transportista(request, transportista_id):
    transportista = Transportista.objects.get(id=transportista_id)

    rutas = RutaEntrega.objects.filter(transportista=transportista).order_by("-fecha_creacion")

    return render(request, "panel_transportista.html", {
        "transportista": transportista,
        "rutas": rutas,
    })

from django.utils import timezone

from .models import RutaOrden

def marcar_entregada(request, orden_id):
    orden = Orden.objects.get(id=orden_id)

    if request.method == "POST":
        nombre_receptor = request.POST.get("receptor")
        observaciones = request.POST.get("observaciones")

        # Obtener o crear el registro de entrega
        registro, creado = RegistroEntrega.objects.get_or_create(
            orden=orden,
            defaults={
                "nombre_receptor": nombre_receptor,
                "observaciones": observaciones,
                "fecha_entrega": timezone.now()
            }
        )

        # Si ya existía, lo actualizamos
        if not creado:
            registro.nombre_receptor = nombre_receptor
            registro.observaciones = observaciones
            registro.fecha_entrega = timezone.now()
            registro.save()

        # Cambiar estado de la orden
        orden.estado = "entregado"
        orden.save()

        # Obtener la ruta desde el modelo intermedio
        relacion = RutaOrden.objects.get(orden=orden)
        ruta = relacion.ruta

        # Redirigir al panel del transportista
        return redirect("panel_transportista", transportista_id=ruta.transportista.id)

    return render(request, "marcar_entregada.html", {
        "orden": orden
    })

def panel_principal(request):
    return render(request, "panel_principal.html")


# mercado pago en cuetas

# views.py
from django.shortcuts import render

def mercado_pago(request):
    return render(request, "mercado_pago.html")

from django.core.mail import send_mail
from django.shortcuts import render, redirect

def contactanos(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        telefono = request.POST.get("telefono")
        mensaje = request.POST.get("mensaje")

        cuerpo = (
            f"Nuevo mensaje desde la página de contacto Vipalú:\n\n"
            f"Nombre: {nombre}\n"
            f"Correo: {correo}\n"
            f"Teléfono: {telefono}\n"
            f"Mensaje:\n{mensaje}\n"
        )

        send_mail(
            subject="Nuevo mensaje desde Contactanos - Vipalú",
            message=cuerpo,
            from_email="no-reply@vipalu.cl",  # puede ser cualquiera
            recipient_list=["marco.sepulvedam85@gmail.com"],
            fail_silently=False,
        )

        return redirect("contacto_enviado")

    return render(request, "contactanos.html")


def contacto_enviado(request):
    return render(request, "contacto_enviado.html")

