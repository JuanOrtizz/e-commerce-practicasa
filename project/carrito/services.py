from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404

from .models import CarritoModel, CarritoItemModel
from productos.models import ProductoModel, ColorModel, MedidaModel


def get_o_crear_carrito_service(usuario):
    carrito, _ = CarritoModel.objects.get_or_create(usuario=usuario)
    return carrito


def get_cantidades_en_carrito(usuario, producto_ids=None):
    carrito = CarritoModel.objects.filter(usuario=usuario).first()
    if not carrito:
        return {}
    qs = CarritoItemModel.objects.filter(carrito=carrito)
    if producto_ids:
        qs = qs.filter(producto_id__in=producto_ids)
    return {
        fila['producto_id']: fila['total']
        for fila in qs.values('producto_id').annotate(total=Sum('cantidad'))
    }


def get_stock_disponible_item_service(carrito, item):
    otras_variantes = CarritoItemModel.objects.filter(
        carrito=carrito, producto=item.producto
    ).exclude(id=item.id).aggregate(total=Sum('cantidad'))['total'] or 0
    return item.producto.stock - otras_variantes


def get_stock_restante_producto_service(usuario, producto):
    en_carrito = get_cantidades_en_carrito(usuario, [producto.id]).get(producto.id, 0)
    return producto.stock - en_carrito


def get_stocks_disponibles_producto_service(carrito, producto_id):
    items = CarritoItemModel.objects.filter(carrito=carrito, producto_id=producto_id)
    return {item.id: get_stock_disponible_item_service(carrito, item) for item in items}


@transaction.atomic
def agregar_item_service(carrito, producto_id, cantidad=1, color_id=None, medida_id=None):
    producto = get_object_or_404(ProductoModel, id=producto_id, activo=True)

    if producto.stock < 1:
        raise ValueError('Producto sin stock')

    color_nombre = None
    color_hex = None
    if color_id:
        color = get_object_or_404(ColorModel, id=color_id)
        color_nombre = color.nombre
        color_hex = color.codigo_hex

    medida_nombre = None
    if medida_id:
        medida = get_object_or_404(MedidaModel, id=medida_id)
        medida_nombre = medida.nombre

    total_en_carrito = CarritoItemModel.objects.filter(
        carrito=carrito, producto=producto
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    if total_en_carrito + cantidad > producto.stock:
        raise ValueError('Producto sin stock')

    item, created = CarritoItemModel.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        color_nombre=color_nombre,
        medida_nombre=medida_nombre,
        defaults={
            'color_hex': color_hex,
            'cantidad': cantidad,
        }
    )

    if not created:
        item.cantidad += cantidad
        item.save()

    return item


@transaction.atomic
def actualizar_cantidad_service(carrito, item_id, nueva_cantidad):
    item = get_object_or_404(CarritoItemModel, id=item_id, carrito=carrito)

    if nueva_cantidad <= 0:
        item.delete()
        return None

    if item.producto.stock == 0:
        item.delete()
        return None

    otras_variantes = CarritoItemModel.objects.filter(
        carrito=carrito, producto=item.producto
    ).exclude(id=item.id).aggregate(total=Sum('cantidad'))['total'] or 0

    if otras_variantes + nueva_cantidad > item.producto.stock:
        raise ValueError('Producto sin stock')

    item.cantidad = nueva_cantidad
    item.save()
    return item


@transaction.atomic
def eliminar_item_service(carrito, item_id):
    item = get_object_or_404(CarritoItemModel, id=item_id, carrito=carrito)
    item.delete()


@transaction.atomic
def vaciar_carrito_service(carrito):
    carrito.items.all().delete()


def calcular_precios_item_service(item):
    producto = item.producto
    cantidad = item.cantidad

    precio_unitario = producto.precio_final
    precio_transferencia_unitario = producto.precio_transferencia_final
    precio_original = producto.precio
    precio_transferencia_original = producto.precio_transferencia

    cantidad_paga = cantidad
    ahorro = Decimal('0')

    if producto.promocion == '2x1':
        cantidad_paga = (cantidad // 2) + (cantidad % 2)
        subtotal = precio_unitario * cantidad_paga
        subtotal_transferencia = precio_transferencia_unitario * cantidad_paga
        ahorro = (precio_unitario * cantidad) - subtotal
    elif producto.promocion == '3x2':
        cantidad_paga = ((cantidad // 3) * 2) + (cantidad % 3)
        subtotal = precio_unitario * cantidad_paga
        subtotal_transferencia = precio_transferencia_unitario * cantidad_paga
        ahorro = (precio_unitario * cantidad) - subtotal
    else:
        subtotal = precio_unitario * cantidad
        subtotal_transferencia = precio_transferencia_unitario * cantidad

    return {
        'item': item,
        'producto': producto,
        'cantidad': cantidad,
        'cantidad_paga': cantidad_paga,
        'precio_unitario': precio_unitario,
        'precio_transferencia_unitario': precio_transferencia_unitario,
        'precio_original': precio_original,
        'precio_transferencia_original': precio_transferencia_original,
        'subtotal': subtotal,
        'subtotal_transferencia': subtotal_transferencia,
        'ahorro': ahorro,
        'tiene_promocion_porcentaje': producto.tiene_promocion_porcentaje,
        'promocion': producto.promocion,
        'porcentaje_descuento': producto.porcentaje_descuento if producto.tiene_promocion_porcentaje else None,
    }


def get_carrito_context_service(carrito):
    items_data = []
    total = Decimal('0')
    total_transferencia = Decimal('0')
    total_ahorro = Decimal('0')

    for item in carrito.items.select_related('producto').all():
        if item.producto.stock == 0 or not item.producto.activo:
            item.delete()
            continue
        stock_disponible = get_stock_disponible_item_service(carrito, item)
        if stock_disponible <= 0:
            item.delete()
            continue
        if item.cantidad > stock_disponible:
            item.cantidad = stock_disponible
            item.save()
        data = calcular_precios_item_service(item)
        data['stock_disponible'] = stock_disponible
        items_data.append(data)
        total += data['subtotal']
        total_transferencia += data['subtotal_transferencia']
        total_ahorro += data['ahorro']

    return {
        'carrito': carrito,
        'items': items_data,
        'total': total,
        'total_transferencia': total_transferencia,
        'total_ahorro': total_ahorro,
        'cantidad_items': carrito.items.count(),
    }
