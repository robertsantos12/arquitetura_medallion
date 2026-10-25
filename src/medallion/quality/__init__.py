"""Validação de valores sem dependência de Spark."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def instante(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp sem timezone')
    return dt.astimezone(timezone.utc)


def dinheiro(value, positivo=False):
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('decimal invalido') from exc
    if not n.is_finite() or abs(n) >= Decimal('10000000000000000') or n != n.quantize(Decimal('.01')) or n < 0 or (positivo and n == 0):
        raise ValueError('decimal fora do contrato')
    return n.quantize(Decimal('.01'))
