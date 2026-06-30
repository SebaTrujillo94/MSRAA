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
    image_url = models.URLField(blank=True, verbose_name='URL de imagen', help_text='Dropbox o Drive (prioridad sobre imagen subida). Recomendado: 800×533px (3:2).')
    url = models.URLField(blank=True, verbose_name='Enlace', help_text='Dropbox, artículo, web, etc.')
    url_label = models.CharField(max_length=60, blank=True, default='Ver más', verbose_name='Texto del enlace')
    url_label_en = models.CharField(max_length=60, blank=True, verbose_name='Texto del enlace (EN)')
    video_url = models.URLField(
        blank=True, verbose_name='URL de video',
        help_text='YouTube, Vimeo, Cloudinary o Dropbox (MP4 directo). Ej: https://youtu.be/xxx o enlace Dropbox .mp4'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-year', 'order']
        verbose_name = 'Ítem de Medios'
        verbose_name_plural = 'Ítems de Medios'

    def __str__(self):
        return f"{self.get_tipo_display()} {self.year}: {self.title}"

    def get_image_src(self):
        if self.image_url:
            return _resolve_media_url(self.image_url)
        return self.image.url if self.image else ''

    def get_video_embed_url(self):
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
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
    image_url = models.URLField(blank=True, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagen referencial'
        verbose_name_plural = 'Imágenes referenciales'

    def get_image_src(self):
        if self.image_url:
            return _resolve_media_url(self.image_url)
        return self.image.url if self.image else ''

    def __str__(self):
        return f"{self.media_item.title} — img {self.order}"


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
    url = models.URLField(blank=True, help_text="Enlace externo (Dropbox, Drive, web). Dejar vacío si no aplica.")
    url_label = models.CharField(max_length=60, blank=True, default='Ver documento', help_text="Texto del enlace")
    url_label_en = models.CharField(max_length=60, blank=True, help_text="Texto del enlace (EN)")
    video_url = models.URLField(blank=True, verbose_name='URL de video', help_text="YouTube o Vimeo. Ej: https://youtu.be/xxxx")
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
    image_url = models.URLField(blank=True, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Pie de foto')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Imagen de Curriculum'
        verbose_name_plural = 'Imágenes de Curriculum'

    def get_image_src(self):
        if self.image_url:
            return _resolve_media_url(self.image_url)
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
        blank=True,
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
        return _resolve_media_url(self.video_url)


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
    description = models.TextField(verbose_name='Descripción')
    description_en = models.TextField(blank=True, verbose_name='Descripción (EN)')
    year = models.CharField(max_length=10, verbose_name='Año')
    location = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    location_en = models.CharField(max_length=200, blank=True, verbose_name='Ubicación (EN)')
    hero_image = models.ImageField(
        upload_to='portfolio/heroes/', blank=True, max_length=500,
        verbose_name='Imagen principal',
        help_text="Imagen portada del proyecto. Recomendado: 1600×1067px (3:2) o 1920×1080px."
    )
    hero_image_url = models.URLField(
        blank=True, verbose_name='URL imagen principal',
        help_text="Dropbox o Drive (prioridad sobre imagen subida). Recomendado: 1600×1067px (3:2)."
    )
    video_url = models.URLField(
        blank=True, verbose_name='URL de video',
        help_text="YouTube, Vimeo o Dropbox MP4. Ej: https://youtu.be/xxxx — se muestra como panel en el overlay."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Proyecto de Portafolio"
        verbose_name_plural = "Proyectos de Portafolio"

    def __str__(self):
        return self.title

    def get_category_name(self):
        return self.category.name if self.category else ""

    def get_hero_image_src(self):
        if self.hero_image_url:
            return _resolve_media_url(self.hero_image_url)
        return self.hero_image.url if self.hero_image else ''

    def get_video_embed_url(self):
        import re
        url = self.video_url
        if not url:
            return ''
        if 'dropbox.com' in url:
            return _resolve_media_url(url)
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
    SIZE_CHOICES = [('large', 'Grande'), ('small', 'Pequeña')]

    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/images/', blank=True, null=True, max_length=500)
    image_url = models.URLField(blank=True, verbose_name='URL de imagen', help_text='URL directa, Dropbox o Drive (alternativa a subir archivo)')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='large')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Imagen de Proyecto"
        verbose_name_plural = "Imágenes de Proyecto"

    def get_image_src(self):
        if self.image_url:
            return _resolve_media_url(self.image_url)
        return self.image.url if self.image else ''

    def __str__(self):
        return f"{self.project.title} — imagen {self.order}"
