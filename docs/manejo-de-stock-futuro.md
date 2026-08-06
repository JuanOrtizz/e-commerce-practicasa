# Manejo de stock: estado actual y diseño a futuro

Documento de referencia para el manejo de stock del e-commerce PractiCasa.
Describe cómo funciona hoy y qué modelo se debería adoptar cuando se desarrolle
el checkout (app `ventas`).

## Estado actual

### Qué está implementado

- El stock es una cifra **global por producto** (`ProductoModel.stock`) que
  comparten todas las variantes (colores/medidas).
- Al agregar al carrito se valida que la suma de todas las variantes del
  producto en el carrito del usuario **no supere** el stock:
  ```python
  total_en_carrito + cantidad > producto.stock  # -> ValueError
  ```
- Las páginas de lista y detalle muestran `stock_restante = stock - en_carrito`
  del propio usuario. Si es 0, el botón se deshabilita ("Sin stock").
- `get_cantidades_en_carrito(usuario, producto_ids)` en
  `carrito/services.py` devuelve cuántas unidades de cada producto tiene el
  usuario en su carrito (sumando variantes).

### Limitaciones conocidas

- **El carrito no reserva stock.** Agregar un producto al carrito no descuenta
  `ProductoModel.stock`. Dos usuarios podrían tener 4 + 4 = 8 unidades en sus
  carritos con un stock de 4.
- Como todavía no existe el checkout, el stock real solo se controla al
  agregar/actualizar el carrito. No hay sobreventa porque no hay venta.
- Si un usuario llena el carrito con todo el stock y nunca compra, no bloquea
  a otros (el restante es por usuario), pero tampoco hay expiración de
  carritos abandonados.

## Modelo objetivo (estilo MercadoLibre)

Para la app `ventas` se recomienda copiar el modelo que usa MercadoLibre:

### 1. No reservar al agregar al carrito

El carrito es solo una "lista de intención de compra". Agregar/actualizar
items no afecta el stock disponible ni el de otros usuarios.

### 2. Reservar y descontar al confirmar la compra

Al **confirmar la orden** (no antes), dentro de una transacción atómica:

- Bloquear la fila del producto con `select_for_update()`.
- Verificar `stock >= cantidad`.
- Descontar: `stock -= cantidad`.

```python
from django.db import transaction
from django.db.models import F

@transaction.atomic
def confirmar_venta(producto_id, cantidad):
    producto = ProductoModel.objects.select_for_update().get(id=producto_id)
    if producto.stock < cantidad:
        raise ValueError('No hay stock suficiente')
    producto.stock = F('stock') - cantidad
    producto.save(update_fields=['stock'])
    return producto
```

Esto evita la **sobreventa en compras simultáneas**: PostgreSQL serializa los
`UPDATE` y el segundo comprador que llega a la vez verá que el stock ya bajó.

### 3. Unidades disponibles = stock - reservas

Para mostrar "quedan X unidades" se debe descontar no solo el stock vendido
sino las **reservas activas** (órdenes creadas e impagas):

- Modelo `Orden`/`Reserva` con estado: `pendiente`, `pagada`, `cancelada`, `expirada`.
- "Disponible" = `stock - SUM(cantidad de órdenes activas)`.

### 4. Expiración de órdenes impagas

- La reserva dura un tiempo limitado (ej. 2-7 días, configurable).
- Si no se paga, se cancela y las unidades vuelven a estar disponibles.
- Un job (Celery/cron) o lazy-check al consultar la orden libera las vencidas.

### 5. Nota sobre restante por usuario

El `stock_restante` actual de las páginas de producto descuenta solo el
carrito del usuario autenticado. Es un límite blando (evita acaparar en un
carrito), no una reserva global. Cuando exista checkout, el límite duro será
el "disponible" del punto 3.

## Orden de implementación sugerido (cuando se desarrolle `ventas`)

1. Modelos `Orden` y `OrdenItem` con estados.
2. `confirmar_venta` transaccional con `select_for_update()` (punto 2).
3. Cálculo de "disponible" con reservas activas (punto 3).
4. Expiración de órdenes impagas (punto 4).
5. Tests de concurrencia simulando 2 compradores simultáneos.
