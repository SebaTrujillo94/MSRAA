from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def tf(context, obj, field):
    """Return translated field: obj.<field>_en when is_en, else obj.<field>."""
    is_en = context.get('is_en', False)
    if is_en:
        en_val = getattr(obj, f'{field}_en', None)
        if en_val:
            return mark_safe(en_val)
    return mark_safe(getattr(obj, field, '') or '')
