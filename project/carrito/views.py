from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST

from .services import (
    get_o_crear_carrito_service, agregar_item_service, actualizar_cantidad_service,
    eliminar_item_service, vaciar_carrito_service, get_carrito_context_service,
    calcular_precios_item_service
)


@login_required
def ver_carrito(request):
    carrito = get_o_crear_carrito_service(request.user)
    context = get_carrito_context_service(carrito)
    return render(request, 'carrito/carrito.html', context)


@require_POST
def agregar_al_carrito(request):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    try:
        carrito = get_o_crear_carrito_service(request.user)
        producto_id = request.POST.get('producto_id')
        color_id = request.POST.get('color')
        medida_id = request.POST.get('medida')

        if not producto_id:
            return JsonResponse({'errors': 'Producto no especificado'}, status=400)

        item = agregar_item_service(carrito, producto_id, color_id=color_id, medida_id=medida_id)

        return JsonResponse({
            'success': {
                'message': f'{item.producto.nombre} agregado al carrito',
            }
        })
    except ValueError as e:
        return JsonResponse({'errors': str(e)}, status=400)
    except Http404:
        return JsonResponse({'errors': 'Producto no encontrado'}, status=404)
    except Exception:
        return JsonResponse({'errors': 'Error al agregar el producto'}, status=500)


@require_POST
def actualizar_cantidad(request):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    try:
        carrito = get_o_crear_carrito_service(request.user)
        item_id = request.POST.get('item_id')
        try:
            nueva_cantidad = int(request.POST.get('cantidad', 0))
        except (TypeError, ValueError):
            return JsonResponse({'errors': 'Cantidad inválida'}, status=400)

        item = actualizar_cantidad_service(carrito, item_id, nueva_cantidad)

        context = get_carrito_context_service(carrito)
        data = {
            'success': {
                'message': 'Carrito actualizado',
                'item_eliminado': item is None,
                'carrito': {
                    'total': str(context['total']),
                    'total_transferencia': str(context['total_transferencia']),
                    'total_ahorro': str(context['total_ahorro']),
                }
            }
        }
        if item is not None:
            item_data = calcular_precios_item_service(item)
            data['success']['item'] = {
                'id': item.id,
                'cantidad': item.cantidad,
                'subtotal': str(item_data['subtotal']),
                'subtotal_transferencia': str(item_data['subtotal_transferencia']),
                'ahorro': str(item_data['ahorro']),
                'cantidad_paga': item_data['cantidad_paga'],
                'stock': item.producto.stock,
            }
        return JsonResponse(data)
    except ValueError as e:
        return JsonResponse({'errors': str(e)}, status=400)
    except Http404:
        return JsonResponse({'errors': 'Item no encontrado'}, status=404)
    except Exception:
        return JsonResponse({'errors': 'Error al actualizar cantidad'}, status=500)


@require_POST
def eliminar_item(request):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    try:
        carrito = get_o_crear_carrito_service(request.user)
        item_id = request.POST.get('item_id')
        eliminar_item_service(carrito, item_id)

        context = get_carrito_context_service(carrito)
        return JsonResponse({
            'success': {
                'message': 'Producto eliminado del carrito',
                'carrito': {
                    'total': str(context['total']),
                    'total_transferencia': str(context['total_transferencia']),
                    'total_ahorro': str(context['total_ahorro']),
                }
            }
        })
    except Http404:
        return JsonResponse({'errors': 'Item no encontrado'}, status=404)
    except Exception:
        return JsonResponse({'errors': 'Error al eliminar el producto'}, status=500)


@require_POST
def vaciar_carrito(request):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    try:
        carrito = get_o_crear_carrito_service(request.user)
        vaciar_carrito_service(carrito)

        return JsonResponse({
            'success': {
                'message': 'Carrito vaciado',
            }
        })
    except Exception:
        return JsonResponse({'errors': 'Error al vaciar el carrito'}, status=500)
