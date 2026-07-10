from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from solo.models import SingletonModel


def _resolve_media_url(url):
    """Convert cloud sharing URLs to direct/embeddable URLs."""
    if not url:
        return url
    import re
    # Dropbox: convert sharing URL to raw/direct URL
    if 'dropbox.com' in url and 'dropboxusercontent.com' not in url:
        url = re.sub(r'[?&]dl=\d', '', url).rstrip('?&')
        url = url + ('&' if '?' in url else '?') + 'raw=1'
    # Google Drive: convert /view to /uc?export=view
    gd = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if gd:
        return f'https://drive.google.com/uc?export=view&id={gd.group(1)}'
    return url


def _cloudinary_h264(url):
    """Add H.264 + 1080p transformation to a Cloudinary video URL for mobile compatibility."""
    if not url or 'res.cloudinary.com' not in url or '/upload/' not in url:
        return url
    if 'vc_h264' in url:
        return url
    return url.replace('/upload/', '/upload/vc_h264,ac_aac,q_auto:good/', 1)


_GRAVITY_CHOICES = [
    ('auto', 'Automático (IA)'),
    ('face', 'Cara'),
    ('faces', 'Caras múltiples'),
    ('center', 'Centro'),
    ('north', 'Arriba'),
    ('south', 'Abajo'),
    ('east', 'Derecha'),
    ('west', 'Izquierda'),
    ('northeast', 'Arriba-Derecha'),
    ('northwest', 'Arriba-Izquierda'),
    ('southeast', 'Abajo-Derecha'),
    ('southwest', 'Abajo-Izquierda'),
]

_RATIO_CHOICES = [
    ('', 'Original'),
    ('16:9', '16:9 — Panorámico'),
    ('4:3', '4:3 — Clásico'),
    ('3:2', '3:2 — Foto'),
    ('1:1', '1:1 — Cuadrado'),
    ('2:3', '2:3 — Retrato'),
]

_VID_RATIO_CHOICES = [
    ('', 'Original'),
    ('16:9', '16:9 — Panorámico'),
    ('4:3', '4:3 — Clásico'),
    ('1:1', '1:1 — Cuadrado'),
    ('9:16', '9:16 — Vertical'),
]

_CROP_MODE_CHOICES = [
    ('fill',  'Rellenar (c_fill) — recorta para llenar'),
    ('fit',   'Ajustar (c_fit) — escala sin recortar'),
    ('pad',   'Añadir fondo (c_pad) — letterbox/pillarbox'),
    ('scale', 'Estirar (c_scale) — deforma proporciones'),
]


def _cloudinary_img(url, gravity='auto', ratio='', zoom=None, x=0, y=0, crop='fill', bg=''):
    """Add crop/quality/format transformation to a Cloudinary image URL."""
    if not url or 'res.cloudinary.com' not in url or '/upload/' not in url:
        return url
    if 'f_auto' in url or 'q_auto' in url:
        return url
    crop_mode = crop or 'fill'
    parts = ['f_auto', 'q_auto:good', f'c_{crop_mode}']
    if crop_mode in ('fill', 'pad'):
        parts.append(f'g_{gravity or "auto"}')
    if crop_mode in ('fill', 'pad'):
        if zoom:
            try:
                z = float(zoom)
                if abs(z - 1.0) > 0.001:
                    parts.append(f'z_{z:.2f}'.rstrip('0').rstrip('.'))
            except (TypeError, ValueError):
                pass
        if x:
            parts.append(f'x_{int(x)}')
        if y:
            parts.append(f'y_{int(y)}')
    elif crop_mode in ('fit', 'scale'):
        if zoom:
            try:
                z = float(zoom)
                w_val = max(100, round(1200 * z))
                parts.append(f'w_{w_val}')
            except (TypeError, ValueError):
                pass
    if crop_mode == 'pad' and bg:
        bg_val = bg.strip()
        if bg_val.startswith('#'):
            hex_part = bg_val.lstrip('#')
            if len(hex_part) == 3:
                hex_part = ''.join(c * 2 for c in hex_part)
            bg_val = 'rgb:' + hex_part
        parts.append(f'b_{bg_val}')
    if ratio:
        parts.append(f'ar_{ratio}')
    return url.replace('/upload/', f'/upload/{",".join(parts)}/', 1)


def _cloudinary_crop(url, x, y, w, h):
    if not url or 'res.cloudinary.com' not in url or '/upload/' not in url:
        return url
    if 'f_auto' in url or 'q_auto' in url:
        return url
    parts = f'c_crop,f_auto,q_auto:good,x_{x},y_{y},w_{w},h_{h}'
    return url.replace('/upload/', f'/upload/{parts}/', 1)


class SiteConfiguration(SingletonModel):
    site_title = models.CharField(max_length=200, default="MSRAA — Estudio de Arquitectura", verbose_name="Título del sitio")
    tagline = models.CharField(max_length=200, default="MSRAA", verbose_name="Eslogan")

    # Accent/gold color — overrides --gold CSS variable
    color_gold = models.CharField(
        max_length=20, default="#e8b84b",
        verbose_name="Color dorado",
        help_text="Color dorado en tema oscuro (CSS --gold). Ej: #e8b84b"
    )
    color_gold_light = models.CharField(
        max_length=20, default="#b8841a",
        verbose_name="Color dorado claro",
        help_text="Color dorado en tema claro. Ej: #b8841a"
    )
    logo_sidebar_color = models.CharField(
        max_length=20, default="#CC0000",
        verbose_name="Color logo sidebar",
        help_text="Color del logo izquierdo pequeño (ej: #CC0000 = rojo oficial)"
    )

    font_size_base = models.PositiveIntegerField(
        default=16,
        verbose_name="Tamaño de fuente base",
        validators=[MinValueValidator(12), MaxValueValidator(24)],
        help_text="Tamaño base de fuente en px (12–24)"
    )
    font_family = models.CharField(max_length=100, default="Calibri, sans-serif", verbose_name="Familia tipográfica")

    # Contact
    contact_email = models.EmailField(default="contacto@msraa.cl", verbose_name="Correo de contacto")
    contact_phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    instagram_url = models.URLField(blank=True, verbose_name="URL Instagram")
    linkedin_url = models.URLField(blank=True, verbose_name="URL LinkedIn")

    # Logo — if blank, template falls back to static PNG
    logo_main = models.ImageField(
        upload_to='logos/', blank=True, max_length=500,
        verbose_name="Logo principal",
        help_text="Logo principal MSRAA (PNG con transparencia). Dejar en blanco para usar el logo estático por defecto."
    )

    # About section
    about_label = models.CharField(max_length=100, default="SOBRE EL PROYECTO", verbose_name="Etiqueta sección Sobre")
    about_label_en = models.CharField(max_length=100, blank=True, verbose_name="Etiqueta sección Sobre (EN)")
    about_p1 = models.TextField(
        verbose_name="Párrafo 1 (Sobre)",
        default="Cuatro volúmenes dibujan su órbita en torno a un vacío central "
                "que actúa como corazón del proyecto. La luz natural penetra desde "
                "múltiples ángulos, creando una danza de sombras que transforma el "
                "espacio a lo largo del día."
    )
    about_p1_en = models.TextField(blank=True, verbose_name="Párrafo 1 (Sobre) (EN)")
    about_p2 = models.TextField(
        verbose_name="Párrafo 2 (Sobre)",
        default="Las fachadas están marcadas por una rigurosa modulación que refleja "
                "la precisión técnica del proceso constructivo. Cada detalle ha sido "
                "pensado para que la obra dialogue con su entorno y perdure en el tiempo."
    )
    about_p2_en = models.TextField(blank=True, verbose_name="Párrafo 2 (Sobre) (EN)")

    # Stats bar
    stat1_number = models.PositiveIntegerField(default=50, verbose_name="Estadística 1 — número")
    stat1_prefix = models.CharField(max_length=50, default="Proyectos", verbose_name="Estadística 1 — prefijo")
    stat1_prefix_en = models.CharField(max_length=50, blank=True, verbose_name="Estadística 1 — prefijo (EN)")
    stat1_label = models.CharField(max_length=100, default="Instalaciones completadas", verbose_name="Estadística 1 — etiqueta")
    stat1_label_en = models.CharField(max_length=100, blank=True, verbose_name="Estadística 1 — etiqueta (EN)")
    stat2_number = models.PositiveIntegerField(default=10, verbose_name="Estadística 2 — número")
    stat2_prefix = models.CharField(max_length=50, default="Difusión", verbose_name="Estadística 2 — prefijo")
    stat2_prefix_en = models.CharField(max_length=50, blank=True, verbose_name="Estadística 2 — prefijo (EN)")
    stat2_label = models.CharField(max_length=100, default="Publicaciones especializadas", verbose_name="Estadística 2 — etiqueta")
    stat2_label_en = models.CharField(max_length=100, blank=True, verbose_name="Estadística 2 — etiqueta (EN)")
    stat3_number = models.PositiveIntegerField(default=300, verbose_name="Estadística 3 — número")
    stat3_prefix = models.CharField(max_length=50, default="Superficie construida", verbose_name="Estadística 3 — prefijo")
    stat3_prefix_en = models.CharField(max_length=50, blank=True, verbose_name="Estadística 3 — prefijo (EN)")
    stat3_label = models.CharField(max_length=100, default="M² construidos en todo Chile", verbose_name="Estadística 3 — etiqueta")
    stat3_label_en = models.CharField(max_length=100, blank=True, verbose_name="Estadística 3 — etiqueta (EN)")

    # Trust/clients section
    trust_lbl = models.CharField(max_length=200, default="QUIENES NOS HAN CONFIADO SU VISIÓN", verbose_name="Colaboradores — etiqueta")
    trust_lbl_en = models.CharField(max_length=200, blank=True, verbose_name="Colaboradores — etiqueta (EN)")
    trust_title = models.CharField(max_length=200, default="ORGULLOSOS DE CADA COLABORACIÓN", verbose_name="Colaboradores — título")
    trust_title_en = models.CharField(max_length=200, blank=True, verbose_name="Colaboradores — título (EN)")
    trust_sub = models.TextField(
        verbose_name="Colaboradores — subtítulo",
        default="Agradecemos profundamente la confianza de nuestros clientes, "
                "cuya visión y colaboración han sido fundamentales para crear "
                "proyectos que transforman espacios y comunidades."
    )
    trust_sub_en = models.TextField(blank=True, verbose_name="Colaboradores — subtítulo (EN)")

    # Hero slides
    hero_slide_duration = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        verbose_name="Duración slide hero (seg)",
        help_text="Segundos que se muestra cada slide del hero antes de pasar al siguiente (5–60s)."
    )

    # Footer
    footer_copy = models.CharField(max_length=200, default="© 2026 MSRAA ESTUDIO DE ARQUITECTURA", verbose_name="Texto pie de página")
    footer_copy_en = models.CharField(max_length=200, blank=True, verbose_name="Texto pie de página (EN)")

    class Meta:
        verbose_name = "Configuración del Sitio"

    def __str__(self):
        return "Configuración del Sitio"

    def get_logo_url(self):
        if self.logo_main:
            return self.logo_main.url
        return None


class MenuItem(models.Model):
    SECTION_CHOICES = [
        ('proyectos', 'PROYECTOS'),
        ('publicaciones', 'PUBLICACIONES'),
        ('curriculum', 'CURRICULUM'),
        ('herramientas', 'HERRAMIENTAS'),
        ('contacto', 'CONTACTO'),
    ]

    label = models.CharField(max_length=100)
    label_en = models.CharField(max_length=100, blank=True, help_text="Etiqueta en inglés (opcional)")
    url = models.CharField(max_length=200, help_text="Usar #seccionId para anclas internas")
    section_group = models.CharField(max_length=30, choices=SECTION_CHOICES, default='proyectos')
    filter_value = models.CharField(
        max_length=100, blank=True,
        help_text="Valor de data-filter para filtrado de portafolio (ej: CASAS, EDUCACIÓN). Dejar vacío si no filtra."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['section_group', 'order']
        verbose_name = "Ítem de Menú"
        verbose_name_plural = "Ítems de Menú"

    def __str__(self):
        return f"{self.get_section_group_display()}: {self.label}"


class MediaItem(models.Model):
    TYPE_CHOICES = [
        ('noticia', 'NOTICIA'),
        ('charla', 'CHARLA'),
        ('premio', 'PREMIO'),
        ('publicacion', 'PUBLICACIÓN'),
        ('entrevista', 'ENTREVISTA'),
        ('otro', 'OTRO'),
    ]

    tipo = models.CharField(max_length=20, choices=TYPE_CHOICES, default='noticia', verbose_name='Tipo')
    year = models.CharField(max_length=10, blank=True, verbose_name='Año', help_text='Ej: 2024')
    title = models.CharField(max_length=200, verbose_name='Título')
    title_en = models.CharField(max_length=200, blank=True, verbose_name='Título (EN)')
    description = models.TextField(blank=True, verbose_name='Descripción')
    description_en = models.TextField(blank=True, verbose_name='Descripción (EN)')
    image = models.ImageField(upload_to='medios/', blank=True, null=True, max_length=500, verbose_name='Imagen', help_text='Foto portada. Resolución recomendada: 800×533px (3:2).')
    image_url = models.URLField(blank=True, max_length=500, verbose_name='URL de imagen', help_text='Dropbox o Drive (prioridad sobre imagen subida). Recomendado: 800×533px (3:2).')
    url = models.URLField(blank=True, max_length=500, verbose_name='Enlace', help_text='Dropbox, artículo, web, etc.')
    url_label = models.CharField(max_length=60, blank=True, default='Ver más', verbose_name='Texto del enlace')
    url_label_en = models.CharField(max_length=60, blank=True, verbose_name='Texto del enlace (EN)')
    video_url = models.URLField(
        blank=True, max_length=500, verbose_name='URL de video',
        help_text='YouTube, Vimeo, Cloudinary o Dropbox (MP4 directo). Ej: https://youtu.be/xxx o enlace Dropbox .mp4'
    )
    img_gravity = models.CharField(
        max_length=20, choices=_GRAVITY_CHOICES, default='auto', blank=True,
        verbose_name='Punto de enfoque (imagen)',
        help_text='Dónde enfocar al recortar la imagen de portada.',
    )
    img_ratio = models.CharField(
        max_length=10, choices=_RATIO_CHOICES, default='', blank=True,
        verbose_name='Proporción de imagen',
        help_text='Recortar imagen a esta proporción. Vacío = original.',
    )
    img_zoom = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, blank=True,
        verbose_name='Zoom',
        help_text='1.0 = normal · 0.5 = más contexto · 2.0 = acercar',
    )
    img_x = models.IntegerField(
        default=0, blank=True,
        verbose_name='Offset X (px)',
        help_text='+ = derecha, − = izquierda (desde punto de enfoque)',
    )
    img_y = models.IntegerField(
        default=0, blank=True,
        verbose_name='Offset Y (px)',
        help_text='+ = abajo, − = arriba (desde punto de enfoque)',
    )
    img_crop = models.CharField(
        max_length=10, choices=_CROP_MODE_CHOICES, default='fill', blank=True,
        verbose_name='Modo de recorte',
        help_text='fill=recorta · fit=ajusta · pad=añade fondo · scale=estira',
    )
    img_bg = models.CharField(
        max_length=30, default='', blank=True,
        verbose_name='Color de fondo',
        help_text='Solo para pad. Ej: white, black, auto:border, rgb:FF0000',
    )
    img_crop_w = models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)')
    img_crop_h = models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-year', 'order']
        verbose_name = 'Ítem de Medios'
        verbose_name_plural = 'Ítems de Medios'
        permissions = [('edit_media_crop', 'Puede usar el editor de medios')]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.year}: {self.title}"

    def get_image_src(self):
        if self.image_url:
            url = _resolve_media_url(self.image_url)
            if self.img_crop_w and self.img_crop_h:
                return _cloudinary_crop(url, self.img_x or 0, self.img_y or 0, self.img_crop_w, self.img_crop_h)
            return _cloudinary_img(url, gravity=self.img_gravity or 'auto', ratio=self.img_ratio or '',
                                   zoom=self.img_zoom, x=self.img_x or 0, y=self.img_y or 0,
                                   crop=self.img_crop or 'fill', bg=self.img_bg or '')
        return self.image.url if self.image else ''

    def get_video_embed_url(self):
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
        if 'res.cloudinary.com' in url:
            return _cloudinary_h264(url)
        if 'player.cloudinary.com/embed' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            params.setdefault('quality_auto', ['best'])
            new_query = urlencode({k: v[0] for k, v in params.items()})
            return urlunparse(parsed._replace(query=new_query))
        yt = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}'
        vimeo = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo:
            return f'https://player.vimeo.com/video/{vimeo.group(1)}'
        return url


class MediaItemImage(models.Model):
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='medios/gallery/', blank=True, null=True, max_length=500)
    image_url = models.URLField(blank=True, max_length=500, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagen referencial'
        verbose_name_plural = 'Imágenes referenciales'

    def get_image_src(self):
        if self.image_url:
            return _cloudinary_img(_resolve_media_url(self.image_url))
        return self.image.url if self.image else ''

    def __str__(self):
        return f"{self.media_item.title} — img {self.order}"


class MediaItemSection(models.Model):
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200, blank=True, verbose_name='Título de sección')
    body = models.TextField(blank=True, verbose_name='Contenido')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Sección adicional'
        verbose_name_plural = 'Secciones adicionales'

    def __str__(self):
        return f"{self.media_item.title} — sección {self.order}"


class MediaItemVideo(models.Model):
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, related_name='videos')
    video_url = models.URLField(
        max_length=500, verbose_name='URL de video',
        help_text='YouTube, Vimeo, Dropbox (.mp4 con ?raw=1), etc.'
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name='Pie de video')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'

    def get_video_url(self):
        import re
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
        if 'res.cloudinary.com' in url:
            return _cloudinary_h264(url)
        yt = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}'
        vimeo = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo:
            return f'https://player.vimeo.com/video/{vimeo.group(1)}'
        return url

    def __str__(self):
        return f"{self.media_item.title} — video {self.order}"


class CurriculumItem(models.Model):
    CATEGORY_CHOICES = [
        ('formacion', 'FORMACIÓN'),
        ('experiencia', 'EXPERIENCIA'),
        ('reconocimientos', 'RECONOCIMIENTOS'),
        ('publicaciones', 'PUBLICACIONES'),
        ('otros', 'OTROS'),
    ]

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='experiencia', verbose_name='Categoría')
    year = models.CharField(max_length=20, blank=True, help_text="Ej: 2020, 2015 — 2020, 2010 —")
    title = models.CharField(max_length=200, verbose_name='Título')
    title_en = models.CharField(max_length=200, blank=True, verbose_name='Título (EN)')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='Subtítulo / Institución')
    subtitle_en = models.CharField(max_length=300, blank=True, verbose_name='Subtítulo / Institución (EN)')
    url = models.URLField(blank=True, max_length=500, help_text="Enlace externo (Dropbox, Drive, web). Dejar vacío si no aplica.")
    url_label = models.CharField(max_length=60, blank=True, default='Ver documento', help_text="Texto del enlace")
    url_label_en = models.CharField(max_length=60, blank=True, help_text="Texto del enlace (EN)")
    video_url = models.URLField(blank=True, max_length=500, verbose_name='URL de video', help_text="YouTube o Vimeo. Ej: https://youtu.be/xxxx")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = 'Ítem de Curriculum'
        verbose_name_plural = 'Ítems de Curriculum'

    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"

    def get_video_embed_url(self):
        import re
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
        if 'res.cloudinary.com' in url:
            return _cloudinary_h264(url)
        if 'player.cloudinary.com/embed' in url:
            return url
        yt = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}'
        vimeo = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo:
            return f'https://player.vimeo.com/video/{vimeo.group(1)}'
        return url


class CurriculumItemImage(models.Model):
    curriculum_item = models.ForeignKey(CurriculumItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='curriculum/', blank=True, null=True, max_length=500, verbose_name='Imagen')
    image_url = models.URLField(blank=True, max_length=500, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Pie de foto')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagen de Curriculum'
        verbose_name_plural = 'Imágenes de Curriculum'

    def get_image_src(self):
        if self.image_url:
            return _cloudinary_img(_resolve_media_url(self.image_url))
        return self.image.url if self.image else ''

    def __str__(self):
        return f"{self.curriculum_item.title} — img {self.order}"


class HeroVideo(models.Model):
    title_line1 = models.CharField(
        max_length=200, blank=True,
        help_text="Primera línea del título sobre el video (dejar en blanco para ocultar)"
    )
    title_line1_en = models.CharField(max_length=200, blank=True, help_text="Primera línea del título (EN)")
    title_line2 = models.CharField(max_length=200, blank=True, help_text="Segunda línea del título")
    title_line2_en = models.CharField(max_length=200, blank=True, help_text="Segunda línea del título (EN)")
    video_file = models.FileField(
        upload_to='videos/', blank=True,
        help_text="Subir MP4 (Cloudinary en producción). Prioridad sobre URL. Recomendado: 1920×1080px, H.264, máx 100MB."
    )
    video_url = models.URLField(
        blank=True, max_length=500,
        help_text="URL Dropbox, Cloudinary CDN o enlace directo MP4. Recomendado: 1920×1080px. Dropbox: copiar enlace compartido del archivo .mp4."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Video Hero"
        verbose_name_plural = "Videos Hero"

    def __str__(self):
        return f"Video {self.order}: {self.title_line1 or '(sin título)'}"

    def get_video_url(self):
        if self.video_file:
            return self.video_file.url
        return _cloudinary_h264(_resolve_media_url(self.video_url))


class ClientLogo(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='client_logos/', max_length=500)
    website_url = models.URLField(blank=True)
    display_scale = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        verbose_name="Escala %",
        help_text="Tamaño visual del logo (50–200%). Default 100. Subir si logo aparece pequeño."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Logo de Cliente"
        verbose_name_plural = "Logos de Clientes"

    def __str__(self):
        return self.name

    @property
    def logo_height_px(self):
        return int(44 * self.display_scale / 100)


class PortfolioCategory(models.Model):
    name = models.CharField(max_length=100, help_text="Nombre en filtros (ej: CASAS, EDUCACIÓN)")
    name_en = models.CharField(max_length=100, blank=True, help_text="Nombre en inglés")
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría de Portafolio"
        verbose_name_plural = "Categorías de Portafolio"
        ordering = ['name']

    def __str__(self):
        return self.name


class PortfolioProject(models.Model):
    title = models.CharField(max_length=200, verbose_name='Título')
    title_en = models.CharField(max_length=200, blank=True, verbose_name='Título (EN)')
    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.SET_NULL, null=True, related_name='projects',
        verbose_name='Categoría'
    )
    summary = models.TextField(
        blank=True, verbose_name='Resumen (tarjeta)',
        help_text='Texto corto que aparece en la tarjeta del portafolio. Si se deja vacío se usan los primeros 280 caracteres de la descripción.',
    )
    summary_en = models.TextField(blank=True, verbose_name='Resumen (tarjeta EN)')
    description = models.TextField(verbose_name='Descripción completa')
    description_en = models.TextField(blank=True, verbose_name='Descripción completa (EN)')
    year = models.CharField(max_length=10, verbose_name='Año')
    location = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    location_en = models.CharField(max_length=200, blank=True, verbose_name='Ubicación (EN)')
    hero_image = models.ImageField(
        upload_to='portfolio/heroes/', blank=True, max_length=500,
        verbose_name='Imagen principal',
        help_text="Imagen portada del proyecto. Recomendado: 1600×1067px (3:2) o 1920×1080px."
    )
    hero_image_url = models.URLField(
        blank=True, max_length=500, verbose_name='URL imagen principal',
        help_text="Dropbox o Drive (prioridad sobre imagen subida). Recomendado: 1600×1067px (3:2)."
    )
    video_url = models.URLField(
        blank=True, max_length=500, verbose_name='URL de video',
        help_text="YouTube, Vimeo o Dropbox MP4. Ej: https://youtu.be/xxxx — se muestra como panel en el overlay."
    )
    img_gravity = models.CharField(
        max_length=20, choices=_GRAVITY_CHOICES, default='auto', blank=True,
        verbose_name='Punto de enfoque (imagen)',
        help_text='Dónde enfocar al recortar la imagen principal.',
    )
    img_ratio = models.CharField(
        max_length=10, choices=_RATIO_CHOICES, default='', blank=True,
        verbose_name='Proporción de imagen',
        help_text='Recortar imagen a esta proporción. Vacío = original.',
    )
    img_zoom = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, blank=True,
        verbose_name='Zoom',
        help_text='1.0 = normal · 0.5 = más contexto · 2.0 = acercar',
    )
    img_x = models.IntegerField(
        default=0, blank=True,
        verbose_name='Offset X (px)',
        help_text='+ = derecha, − = izquierda (desde punto de enfoque)',
    )
    img_y = models.IntegerField(
        default=0, blank=True,
        verbose_name='Offset Y (px)',
        help_text='+ = abajo, − = arriba (desde punto de enfoque)',
    )
    img_crop = models.CharField(
        max_length=10, choices=_CROP_MODE_CHOICES, default='fill', blank=True,
        verbose_name='Modo de recorte',
        help_text='fill=recorta · fit=ajusta · pad=añade fondo · scale=estira',
    )
    img_bg = models.CharField(
        max_length=30, default='', blank=True,
        verbose_name='Color de fondo',
        help_text='Solo para pad. Ej: white, black, auto:border, rgb:FF0000',
    )
    img_crop_w = models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)')
    img_crop_h = models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Proyecto de Portafolio"
        verbose_name_plural = "Proyectos de Portafolio"
        permissions = [('edit_media_crop', 'Puede usar el editor de medios')]

    def __str__(self):
        return self.title

    def get_category_name(self):
        return self.category.name if self.category else ""

    def get_summary(self):
        if self.summary:
            return self.summary
        desc = self.description or ''
        if len(desc) <= 280:
            return desc
        cut = desc[:280].rfind(' ')
        return desc[:cut] + '…' if cut > 0 else desc[:280] + '…'

    def get_hero_image_src(self):
        if self.hero_image_url:
            url = _resolve_media_url(self.hero_image_url)
            if self.img_crop_w and self.img_crop_h:
                return _cloudinary_crop(url, self.img_x or 0, self.img_y or 0, self.img_crop_w, self.img_crop_h)
            return _cloudinary_img(url, gravity=self.img_gravity or 'auto', ratio=self.img_ratio or '',
                                   zoom=self.img_zoom, x=self.img_x or 0, y=self.img_y or 0,
                                   crop=self.img_crop or 'fill', bg=self.img_bg or '')
        return self.hero_image.url if self.hero_image else ''

    def get_video_embed_url(self):
        import re
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
        if 'res.cloudinary.com' in url:
            return _cloudinary_h264(url)
        if 'player.cloudinary.com/embed' in url:
            return url
        yt = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}'
        vimeo = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo:
            return f'https://player.vimeo.com/video/{vimeo.group(1)}'
        return url


class ContactSubmission(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nombre')
    phone = models.CharField(max_length=50, blank=True, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Correo')
    project_type = models.CharField(max_length=200, blank=True, verbose_name='Tipo de proyecto')
    message = models.TextField(verbose_name='Mensaje')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de envío')
    is_read = models.BooleanField(default=False, verbose_name='Leído')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consulta de Contacto'
        verbose_name_plural = 'Consultas de Contacto'

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class PortfolioProjectImage(models.Model):
    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/images/', blank=True, null=True, max_length=500)
    image_url = models.URLField(blank=True, max_length=500, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    order = models.PositiveIntegerField(default=0)
    img_gravity = models.CharField(max_length=20, choices=_GRAVITY_CHOICES, default='auto', blank=True, verbose_name='Punto de enfoque')
    img_ratio = models.CharField(max_length=10, choices=_RATIO_CHOICES, default='', blank=True, verbose_name='Proporción')
    img_zoom = models.DecimalField(max_digits=4, decimal_places=2, default=1.0, verbose_name='Zoom')
    img_x = models.IntegerField(default=0, verbose_name='Ajuste X')
    img_y = models.IntegerField(default=0, verbose_name='Ajuste Y')
    img_crop = models.CharField(max_length=10, choices=_CROP_MODE_CHOICES, default='fill', blank=True, verbose_name='Modo de recorte')
    img_bg = models.CharField(max_length=30, default='', blank=True, verbose_name='Color de fondo')
    img_crop_w = models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)')
    img_crop_h = models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)')

    class Meta:
        ordering = ['order']
        verbose_name = "Imagen de Proyecto"
        verbose_name_plural = "Imágenes de Proyecto"

    def get_image_src(self):
        if self.image_url:
            url = _resolve_media_url(self.image_url)
            if self.img_crop_w and self.img_crop_h:
                return _cloudinary_crop(url, self.img_x or 0, self.img_y or 0, self.img_crop_w, self.img_crop_h)
            return _cloudinary_img(url, gravity=self.img_gravity or 'auto', ratio=self.img_ratio or '',
                                   zoom=self.img_zoom, x=self.img_x or 0, y=self.img_y or 0,
                                   crop=self.img_crop or 'fill', bg=self.img_bg or '')
        return self.image.url if self.image else ''

    def __str__(self):
        return f"{self.project.title} — imagen {self.order}"


# ─── Mantenedor / Monitoring ─────────────────────────────────────────────────

class SiteVisit(models.Model):
    """Daily aggregated page visit counter."""
    date = models.DateField(db_index=True)
    path = models.CharField(max_length=300, db_index=True)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [('date', 'path')]
        ordering = ['-date', '-count']
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'

    def __str__(self):
        return f"{self.date} {self.path} ({self.count})"


class MonitorAlert(models.Model):
    METRIC_CHOICES = [
        ('storage_pct',   'Almacenamiento Cloudinary (%)'),
        ('bandwidth_pct', 'Ancho de banda Cloudinary (%)'),
        ('response_ms',   'Tiempo de respuesta sitio (ms)'),
    ]
    CONDITION_CHOICES = [
        ('gt', '>  Mayor que'),
        ('lt', '<  Menor que'),
    ]
    STATUS_CHOICES = [
        ('ok',      'OK'),
        ('warn',    'Advertencia'),
        ('crit',    'Critico'),
        ('unknown', 'Sin datos'),
    ]

    name        = models.CharField(max_length=100, verbose_name='Nombre')
    metric      = models.CharField(max_length=30, choices=METRIC_CHOICES, verbose_name='Metrica')
    condition   = models.CharField(max_length=5, choices=CONDITION_CHOICES, default='gt', verbose_name='Condicion')
    threshold   = models.FloatField(verbose_name='Umbral')
    is_active   = models.BooleanField(default=True, verbose_name='Activa')
    last_checked = models.DateTimeField(null=True, blank=True, verbose_name='Ultimo chequeo')
    last_status  = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unknown', verbose_name='Estado')
    email_notify = models.EmailField(blank=True, verbose_name='Email notificacion')

    class Meta:
        ordering = ['name']
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'

    def __str__(self):
        return f"{self.name} ({self.get_metric_display()} {self.condition} {self.threshold})"


# ─── Equipo / Team ────────────────────────────────────────────────────────────

class TeamMember(models.Model):
    name       = models.CharField(max_length=200, verbose_name='Nombre')
    role       = models.CharField(max_length=200, blank=True, verbose_name='Cargo')
    role_en    = models.CharField(max_length=200, blank=True, verbose_name='Cargo (EN)')
    bio        = models.TextField(blank=True, verbose_name='Descripción breve')
    bio_en     = models.TextField(blank=True, verbose_name='Descripción breve (EN)')
    image_url  = models.URLField(blank=True, max_length=500, verbose_name='Foto (URL Cloudinary)')
    img_gravity = models.CharField(max_length=20, choices=_GRAVITY_CHOICES, default='face', blank=True, verbose_name='Punto de enfoque')
    img_ratio   = models.CharField(max_length=10, choices=_RATIO_CHOICES, default='1:1', blank=True, verbose_name='Proporción')
    img_x       = models.IntegerField(default=0, blank=True, verbose_name='Ajuste X')
    img_y       = models.IntegerField(default=0, blank=True, verbose_name='Ajuste Y')
    img_crop_w  = models.PositiveIntegerField(default=0, blank=True, verbose_name='Recorte ancho px')
    img_crop_h  = models.PositiveIntegerField(default=0, blank=True, verbose_name='Recorte alto px')
    img_crop    = models.CharField(max_length=10, choices=_CROP_MODE_CHOICES, default='fill', blank=True, verbose_name='Modo de recorte')
    img_bg      = models.CharField(max_length=30, default='', blank=True, verbose_name='Color de fondo')
    order      = models.PositiveIntegerField(default=0, verbose_name='Orden')
    is_active  = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'

    def __str__(self):
        return self.name

    def get_image_src(self):
        if not self.image_url:
            return ''
        return _cloudinary_img(
            _resolve_media_url(self.image_url),
            gravity=self.img_gravity or 'face',
            ratio=self.img_ratio or '1:1',
            x=self.img_x or 0,
            y=self.img_y or 0,
            crop=self.img_crop or 'fill',
            bg=self.img_bg or '',
        )
