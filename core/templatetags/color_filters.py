from django import template

register = template.Library()

def _norm(s):
    try:
        s = (s or '').strip().lower()
        s = s.replace('أ','ا').replace('إ','ا').replace('آ','ا')
        return s
    except Exception:
        return ''

_MAP = {
    'اسود': '#000000',
    'أسود': '#000000',
    'black': '#000000',
    'ابيض': '#ffffff',
    'أبيض': '#ffffff',
    'white': '#ffffff',
    'احمر': '#ff0000',
    'أحمر': '#ff0000',
    'red': '#ff0000',
    'اخضر': '#008000',
    'أخضر': '#008000',
    'green': '#008000',
    'ازرق': '#0000ff',
    'أزرق': '#0000ff',
    'blue': '#0000ff',
    'اصفر': '#ffff00',
    'أصفر': '#ffff00',
    'yellow': '#ffff00',
    'برتقالي': '#ffa500',
    'orange': '#ffa500',
    'بنفسجي': '#800080',
    'purple': '#800080',
    'نيلي': '#4b0082',
    'indigo': '#4b0082',
    'تركوازي': '#40e0d0',
    'فيروزي': '#40e0d0',
    'turquoise': '#40e0d0',
    'كحلي': '#000080',
    'navy': '#000080',
    'رمادي': '#808080',
    'gray': '#808080',
    'زهري': '#ffc0cb',
    'وردي': '#ffc0cb',
    'pink': '#ffc0cb',
    'بني': '#8b4513',
    'بنّي': '#8b4513',
    'brown': '#8b4513',
    'سماوي': '#87ceeb',
    'sky': '#87ceeb',
}

@register.filter(name='color_code')
def color_code(value):
    try:
        code = None
        if hasattr(value, 'code'):
            c = (value.code or '').strip()
            if c:
                code = c
        if not code:
            name = ''
            if hasattr(value, 'name'):
                name = value.name
            else:
                name = str(value)
            name = _norm(name)
            code = _MAP.get(name) or '#ccc'
        return code
    except Exception:
        return '#ccc'
