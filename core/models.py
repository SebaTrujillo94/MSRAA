from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    site_title = models.CharField(max_length=200, default="MSRAA — Estudio de Arquitectura")
    tagline = models.CharField(max_length=200, default="MSRAA")

    # Accent/gold color — overrides --gold CSS variable
    color_gold = models.CharField(
        max_length=20, default="#e8b84b",
        help_text="Color dorado en tema oscuro (CSS --gold). Ej: #e8b84b"
    )
    color_gold_light = models.CharField(
        max_length=20, default="#b8841a",
        help_text="Color dorado en tema claro. Ej: #b8841a"
    )
    logo_sidebar_color = models.CharField(
        max_length=20, default="#CC0000",
        verbose_name="Color logo sidebar",
        help_text="Color del logo izquierdo pequeño (ej: #CC0000 = rojo oficial)"
    )

    font_size_base = models.PositiveIntegerField(
        default=16,
        validators=[MinValueValidator(12), MaxValueValidator(24)],
        help_text="Tamaño base de fuente en px (12–24)"
    )
    font_family = models.CharField(max_length=100, default="Calibri, sans-serif")

    # Contact
    contact_email = models.EmailField(default="contacto@msraa.cl")
    contact_phone = models.CharField(max_length=30, blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Logo — if blank, template falls back to static PNG
    logo_main = models.ImageField(
        upload_to='logos/', blank=True,
        help_text="Logo principal MSRAA (PNG con transparencia). Dejar en blanco para usar el logo estático por defecto."
    )

    # About section
    about_label = models.CharField(max_length=100, default="SOBRE EL PROYECTO")
    about_p1 = models.TextField(
        default="Cuatro volúmenes dibujan su órbita en torno a un vacío central "
                "que actúa como corazón del proyecto. La luz natural penetra desde "
                "múltiples ángulos, creando una danza de sombras que transforma el "
                "espacio a lo largo del día."
    )
    about_p2 = models.TextField(
        default="Las fachadas están marcadas por una rigurosa modulación que refleja "
                "la precisión técnica del proceso constructivo. Cada detalle ha sido "
                "pensado para que la obra dialogue con su entorno y perdure en el tiempo."
    )

    # Stats bar
    stat1_number = models.PositiveIntegerField(default=50)
    stat1_prefix = models.CharField(max_length=50, default="Proyectos")
    stat1_label = models.CharField(max_length=100, default="Instalaciones completadas")
    stat2_number = models.PositiveIntegerField(default=10)
    stat2_prefix = models.CharField(max_length=50, default="Difusión")
    stat2_label = models.CharField(max_length=100, default="Publicaciones especializadas")
    stat3_number = models.PositiveIntegerField(default=300)
    stat3_prefix = models.CharField(max_length=50, default="Superficie construida")
    stat3_label = models.CharField(max_length=100, default="M² construidos en todo Chile")

    # Trust/clients section
    trust_lbl = models.CharField(max_length=200, default="QUIENES NOS HAN CONFIADO SU VISIÓN")
    trust_title = models.CharField(max_length=200, default="ORGULLOSOS DE CADA COLABORACIÓN")
    trust_sub = models.TextField(
        default="Agradecemos profundamente la confianza de nuestros clientes, "
                "cuya visión y colaboración han sido fundamentales para crear "
                "proyectos que transforman espacios y comunidades."
    )

    # Footer
    footer_copy = models.CharField(max_length=200, default="© 2026 MSRAA ESTUDIO DE ARQUITECTURA")

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


class HeroVideo(models.Model):
    title_line1 = models.CharField(
        max_length=200, blank=True,
        help_text="Primera línea del título sobre el video (dejar en blanco para ocultar)"
    )
    title_line2 = models.CharField(max_length=200, blank=True, help_text="Segunda línea del título")
    video_file = models.FileField(
        upload_to='videos/', blank=True,
        help_text="Subir MP4 aquí (Cloudinary en producción). Tiene prioridad sobre la URL."
    )
    video_url = models.URLField(
        blank=True,
        help_text="URL externa de CDN para el video. Usar si no se sube el archivo directamente."
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
        return self.video_url


class ClientLogo(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='client_logos/')
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
    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.SET_NULL, null=True, related_name='projects'
    )
    description = models.TextField()
    year = models.CharField(max_length=10)
    location = models.CharField(max_length=200, blank=True)
    hero_image = models.ImageField(
        upload_to='portfolio/heroes/', blank=True,
        help_text="Imagen principal del proyecto (se muestra en la grilla)"
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


class PortfolioProjectImage(models.Model):
    SIZE_CHOICES = [('large', 'Grande'), ('small', 'Pequeña')]

    project = models.ForeignKey(PortfolioProject, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/images/')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='large')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Imagen de Proyecto"
        verbose_name_plural = "Imágenes de Proyecto"

    def __str__(self):
        return f"{self.project.title} — imagen {self.order}"
