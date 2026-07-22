import bleach
from bleach.css_sanitizer import CSSSanitizer
from django.db import models
from tinymce.widgets import TinyMCE

_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'span', 'ul', 'ol', 'li', 'div', 'dl', 'dt', 'dd',
    'h1', 'h2', 'h3',
]
_ALLOWED_ATTRIBUTES = {
    'span': ['style'], 'p': ['style'], 'div': ['style', 'class'], 'dl': ['class'],
    'h1': ['style'], 'h2': ['style'], 'h3': ['style'],
}
_CSS_SANITIZER = CSSSanitizer(allowed_css_properties=[
    'color', 'background-color', 'font-size', 'font-family', 'text-align',
    'margin-left', 'margin-right', 'text-decoration',
])


def sanitize_rich_text(html):
    if not html:
        return html
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        css_sanitizer=_CSS_SANITIZER,
        strip=True,
    )


class RichTextField(models.TextField):
    """TextField edited via TinyMCE; sanitized with bleach before save."""

    def formfield(self, **kwargs):
        # Admin injects AdminTextareaWidget for every TextField subclass via
        # FORMFIELD_FOR_DBFIELD_DEFAULTS before this runs, so it must be
        # forced here rather than set as a default.
        kwargs['widget'] = TinyMCE()
        return super().formfield(**kwargs)

    def pre_save(self, model_instance, add):
        value = sanitize_rich_text(getattr(model_instance, self.attname))
        setattr(model_instance, self.attname, value)
        return value
