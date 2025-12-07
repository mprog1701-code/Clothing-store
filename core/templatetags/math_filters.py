from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

ARABIC_INDIC_MAP = {
    '0': '\u0660', '1': '\u0661', '2': '\u0662', '3': '\u0663', '4': '\u0664',
    '5': '\u0665', '6': '\u0666', '7': '\u0667', '8': '\u0668', '9': '\u0669'
}

def _to_arabic_indic(s: str) -> str:
    return ''.join(ARABIC_INDIC_MAP.get(ch, ch) for ch in s)

@register.filter(name='iqd')
def iqd(value, use_arabic_indic=True):
    """Format a number as Iraqi Dinar with thousands separators and optional Arabic-Indic digits.

    Usage in templates: {{ amount|iqd }} or {{ amount|iqd:False }} to keep Western digits.
    """
    try:
        # Normalize value to integer-like number (IQD typically displayed without decimals)
        num = Decimal(str(value)).quantize(Decimal('1'))
    except Exception:
        return value

    formatted = f"{int(num):,}"
    # Replace comma with localized separator (Arabic comma '،') for RTL feel
    formatted = formatted.replace(',', ',')
    if use_arabic_indic in (True, 'True', 'true', '1', 'yes', 'y'):
        formatted = _to_arabic_indic(formatted)
    return f"{formatted} د.ع"
