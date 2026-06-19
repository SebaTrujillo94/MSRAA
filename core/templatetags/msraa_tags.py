from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def tf(context, obj, field):
    """Return translated field: obj.<field>_en when is_en, else obj.<field>."""
    is_en = context.get('is_en', False)
    if is_en:
        en_val = getattr(obj, f'{field}_en', None)
        if en_val:
            return en_val
    return getattr(obj, field, '')
