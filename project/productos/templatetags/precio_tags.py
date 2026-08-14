from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def format_price(value):
    if value is None or value == '':
        return ''
    try:
        numero = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value
    entero, decimales = format(numero, ',.2f').split('.')
    entero = entero.replace(',', '.')
    return f'{entero},{decimales}'
