from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils import timezone
from django.db import models as db_models
from solo.admin import SingletonModelAdmin
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, PortfolioProjectImage,
    CurriculumItem, CurriculumItemImage, MediaItem, MediaItemImage,
    MediaItemSection, MediaItemVideo,
    ContactSubmission,
)


def _safe_save(admin_instance, request, obj, form, change):
    """Save model using queryset.update() to bypass pre_save on FileFields."""
    file_field_names = [
        f.name for f in obj._meta.fields
        if isinstance(f, (db_models.FileField, db_models.ImageField))
    ]
    file_fields_changed = any(f in form.changed_data for f in file_field_names)

    if change and not file_fields_changed and file_field_names:
        update_vals = {
            f.attname: getattr(obj, f.attname)
            for f in obj._meta.fields
            if not isinstance(f, (db_models.FileField, db_models.ImageField))
            and f.name != 'id'
        }
        obj.__class__.objects.filter(pk=obj.pk).update(**update_vals)
    else:
        try:
            obj.save()
        except Exception as e:
            if 'cloudinary' in str(e).lower() or 'forbidden' in str(e).lower():
                if change:
                    update_vals = {
                        f.attname: getattr(obj, f.attname)
                        for f in obj._meta.fields
                        if not isinstance(f, (db_models.FileField, db_models.ImageField))
                        and f.name != 'id'
                    }
                    obj.__class__.objects.filter(pk=obj.pk).update(**update_vals)
                    messages.warning(request, 'Guardado sin imagen — actualiza CLOUDINARY_URL en Vercel env vars.')
                else:
                    raise
            else:
                raise


def _cld_init():
    """Configure Cloudinary SDK from env. Returns error string or None."""
    import os, re
    from django.conf import settings
    import cloudinary
    cld_env = (
        os.environ.get('CLOUDINARY_URL') or
        getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUDINARY_URL', '')
    )
    m = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', cld_env or '')
    if not m:
        return 'CLOUDINARY_URL no configurada en Vercel env vars'
    cloudinary.config(api_key=m.group(1), api_secret=m.group(2), cloud_name=m.group(3))
    return None


_EAGER_VIDEO = [{
    'video_codec': 'h264',
    'audio_codec': 'aac',
    'width': 1920,
    'height': 1080,
    'crop': 'limit',
    'quality': 'auto:good',
    'format': 'mp4',
}]


class CloudinaryUploadMixin:
    """
    Mixin for ModelAdmin classes that adds Cloudinary upload buttons.

    Configure per admin class:
        cld_video_field = 'video_url'       # URLField for video (None to disable)
        cld_image_field = 'image_url'       # URLField for image (None to disable)
        cld_folder      = 'msraa/videos'    # Cloudinary folder prefix (auto if None)
    """
    cld_video_field = 'video_url'
    cld_image_field = None
    cld_folder = None

    def get_urls(self):
        urls = super().get_urls()
        mn = self.model._meta.model_name
        custom = []
        if self.cld_video_field:
            custom.append(path(
                '<int:pk>/upload-cld-video/',
                self.admin_site.admin_view(self._cld_video_view),
                name=f'{mn}_upload_cld_video',
            ))
        if self.cld_image_field:
            custom.append(path(
                '<int:pk>/upload-cld-image/',
                self.admin_site.admin_view(self._cld_image_view),
                name=f'{mn}_upload_cld_image',
            ))
        return custom + urls

    def _cld_upload(self, source_url, resource_type, pk, eager=None):
        """Upload source_url to Cloudinary. Returns (secure_url, error)."""
        from .models import _resolve_media_url
        import cloudinary.uploader
        err = _cld_init()
        if err:
            return None, err
        mn = self.model._meta.model_name
        folder = self.cld_folder or f'msraa/{mn}'
        resolved = _resolve_media_url(source_url)
        try:
            kwargs = dict(
                resource_type=resource_type,
                folder=folder,
                public_id=f'{mn}_{pk}',
                overwrite=True,
            )
            if eager:
                kwargs.update(eager=eager, eager_async=True)
            result = cloudinary.uploader.upload(resolved, **kwargs)
            return result['secure_url'], None
        except Exception as e:
            return None, str(e)

    def _cld_video_view(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            source_url = json.loads(request.body).get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        url, error = self._cld_upload(source_url, 'video', pk, eager=_EAGER_VIDEO)
        if error:
            return JsonResponse({'error': error}, status=500)
        self.model.objects.filter(pk=pk).update(**{self.cld_video_field: url})
        return JsonResponse({'url': url})

    def _cld_image_view(self, request, pk):
        import json
        from django.http import JsonResponse
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            source_url = json.loads(request.body).get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        url, error = self._cld_upload(source_url, 'image', pk)
        if error:
            return JsonResponse({'error': error}, status=500)
        self.model.objects.filter(pk=pk).update(**{self.cld_image_field: url})
        return JsonResponse({'url': url})

    def _cld_btn(self, obj, upload_path_suffix, field_id, icon, label, note):
        if not obj.pk:
            return format_html('<span style="color:#999">Guarda el registro primero</span>')
        slug = field_id.replace('id_', '').replace('-', '_')
        upload_path = f'/admin/core/{self.model._meta.model_name}/{obj.pk}/{upload_path_suffix}'
        return format_html(
            '''<div>
              <button type="button" id="cld-btn-{slug}"
                onclick="cldUp_{slug}()"
                style="padding:8px 18px;background:#e05d20;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;font-weight:600;">
                {icon} {label}
              </button>
              <span id="cld-st-{slug}" style="margin-left:12px;font-size:13px;"></span>
              <p style="margin:5px 0 0;font-size:11px;color:#888">{note}</p>
            </div>
            <script>
            function cldUp_{slug}() {{
              var btn=document.getElementById('cld-btn-{slug}');
              var st=document.getElementById('cld-st-{slug}');
              var f=document.getElementById('{field_id}');
              var url=f?f.value.trim():'';
              if(!url){{st.style.color='#c00';st.textContent='❌ Ingresa una URL primero';return;}}
              btn.disabled=true;btn.textContent='⏳ Subiendo...';st.textContent='';
              var csrf=document.querySelector('[name=csrfmiddlewaretoken]').value;
              fetch('{upload_path}',{{method:'POST',headers:{{'Content-Type':'application/json','X-CSRFToken':csrf}},body:JSON.stringify({{url:url}})}})
              .then(r=>r.json()).then(d=>{{
                if(d.url){{f.value=d.url;st.style.color='green';st.textContent='✅ Subido';btn.textContent='{icon} {label}';btn.disabled=false;}}
                else{{st.style.color='#c00';st.textContent='❌ '+d.error;btn.disabled=false;btn.textContent='{icon} {label}';}}
              }}).catch(()=>{{st.style.color='#c00';st.textContent='❌ Error de red';btn.disabled=false;btn.textContent='{icon} {label}';}});
            }}
            </script>''',
            slug=slug, icon=icon, label=label, note=note,
            field_id=field_id, upload_path=upload_path,
        )

    @admin.display(description='☁️ Subir video a Cloudinary')
    def cloudinary_video_btn(self, obj):
        return self._cld_btn(
            obj, 'upload-cld-video/', f'id_{self.cld_video_field}',
            '☁️', 'Subir video a Cloudinary',
            'Descarga desde Dropbox y sube a Cloudinary CDN con H.264+1080p. Tarda 1–3 min.',
        )

    @admin.display(description='🖼️ Subir imagen a Cloudinary')
    def cloudinary_image_btn(self, obj):
        return self._cld_btn(
            obj, 'upload-cld-image/', f'id_{self.cld_image_field}',
            '🖼️', 'Subir imagen a Cloudinary',
            'Descarga desde Dropbox/Drive y sube a Cloudinary CDN con auto-calidad.',
        )


class PortfolioProjectImageInline(admin.TabularInline):
    model = PortfolioProjectImage
    extra = 2
    fields = ['image', 'image_url', 'size', 'order']


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    readonly_fields = ('cloudinary_status_link',)
    fieldsets = (
        ('General', {
            'fields': ('site_title', 'tagline', 'logo_main', 'font_size_base', 'font_family'),
        }),
        ('Colores', {
            'fields': ('color_gold', 'color_gold_light', 'logo_sidebar_color'),
            'description': 'Colores de acento. logo_sidebar_color = color del logo pequeño izquierdo (por defecto rojo #CC0000).',
        }),
        ('Contacto y Redes', {
            'fields': ('contact_email', 'contact_phone', 'instagram_url', 'linkedin_url'),
        }),
        ('Hero Slides', {
            'fields': ('hero_slide_duration',),
            'description': 'Duración de cada slide en el video hero principal.',
        }),
        ('Sección About', {
            'fields': ('about_label', 'about_p1', 'about_p2'),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': (
                'stat1_number', 'stat1_prefix', 'stat1_label',
                'stat2_number', 'stat2_prefix', 'stat2_label',
                'stat3_number', 'stat3_prefix', 'stat3_label',
            ),
            'classes': ('collapse',),
        }),
        ('Sección Clientes (Trust)', {
            'fields': ('trust_lbl', 'trust_title', 'trust_sub'),
            'classes': ('collapse',),
        }),
        ('Footer', {
            'fields': ('footer_copy',),
        }),
        ('Cloudinary — Almacenamiento', {
            'fields': ('cloudinary_status_link',),
            'description': 'Plan Free: 25 GB storage + 25 GB bandwidth/mes.',
        }),
    )

    @admin.display(description='Estado de uso')
    def cloudinary_status_link(self, obj):
        return format_html(
            '<a href="cloudinary/" class="button" style="padding:8px 16px;background:#0073aa;color:#fff;'
            'border-radius:4px;text-decoration:none;font-size:13px;">📊 Ver uso de Cloudinary</a>'
        )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('cloudinary/', self.admin_site.admin_view(self._cloudinary_usage_view), name='cloudinary_usage'),
        ]
        return custom + urls

    def _cloudinary_usage_view(self, request):
        ctx = dict(self.admin_site.each_context(request), title='Estado Cloudinary')
        try:
            import cloudinary.api
            err = _cld_init()
            if err:
                raise Exception(err)
            usage = cloudinary.api.usage()
            storage_bytes = usage.get('storage', {}).get('usage', 0)
            bandwidth_bytes = usage.get('bandwidth', {}).get('usage', 0)
            GB = 1024 ** 3
            FREE_GB = 25
            ctx.update({
                'storage_gb': storage_bytes / GB,
                'storage_pct': min((storage_bytes / GB / FREE_GB) * 100, 100),
                'bandwidth_gb': bandwidth_bytes / GB,
                'bandwidth_pct': min((bandwidth_bytes / GB / FREE_GB) * 100, 100),
                'transformations': usage.get('transformations', {}).get('usage', 0),
                'requests': usage.get('requests', 0),
                'resources': usage.get('resources', 0),
                'now': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'error': None,
            })
        except Exception as e:
            ctx.update({'error': str(e), 'storage_gb': 0, 'storage_pct': 0,
                        'bandwidth_gb': 0, 'bandwidth_pct': 0,
                        'transformations': 0, 'requests': 0, 'resources': 0, 'now': ''})
        return TemplateResponse(request, 'admin/cloudinary_usage.html', ctx)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['label', 'section_group', 'url', 'filter_value', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['section_group', 'is_active']
    ordering = ['section_group', 'order']


@admin.register(HeroVideo)
class HeroVideoAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_folder = 'msraa/hero'
    list_display = ['title_line1', 'title_line2', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    readonly_fields = ['cloudinary_video_btn']
    fields = [
        'title_line1', 'title_line1_en',
        'title_line2', 'title_line2_en',
        'video_file', 'video_url', 'cloudinary_video_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ClientLogo)
class ClientLogoAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name', 'display_scale', 'order', 'is_active']
    list_editable = ['display_scale', 'order', 'is_active']
    list_display_links = ['logo_preview', 'name']
    readonly_fields = ['logo_preview_large']
    fields = ['name', 'image', 'logo_preview_large', 'display_scale', 'website_url', 'order', 'is_active']

    @admin.display(description='Preview')
    def logo_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;max-width:100px;object-fit:contain;background:#f5f5f5;padding:4px;border-radius:3px">',
                obj.image.url
            )
        return '—'

    @admin.display(description='Vista previa')
    def logo_preview_large(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:200px;object-fit:contain;background:#f0f0f0;padding:8px;border-radius:4px">',
                obj.image.url
            )
        return '—'


@admin.register(PortfolioCategory)
class PortfolioCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_image_field = 'hero_image_url'
    cld_folder = 'msraa/portfolio'
    list_display = ['title', 'category', 'year', 'location', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    inlines = [PortfolioProjectImageInline]
    readonly_fields = ['cloudinary_video_btn', 'cloudinary_image_btn']
    fields = [
        'title', 'title_en', 'category', 'year', 'location', 'location_en',
        'description', 'description_en',
        'hero_image', 'hero_image_url', 'cloudinary_image_btn',
        'video_url', 'cloudinary_video_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


class CurriculumItemImageInline(admin.TabularInline):
    model = CurriculumItemImage
    extra = 2
    fields = ['image', 'image_url', 'caption', 'order']


@admin.register(CurriculumItem)
class CurriculumItemAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_folder = 'msraa/curriculum'
    inlines = [CurriculumItemImageInline]
    list_display = ['title', 'category', 'year', 'subtitle', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    ordering = ['category', 'order']
    readonly_fields = ['cloudinary_video_btn']
    fields = [
        'category', 'year', 'title', 'title_en', 'subtitle', 'subtitle_en',
        'url', 'url_label', 'url_label_en',
        'video_url', 'cloudinary_video_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


class MediaItemImageInline(admin.TabularInline):
    model = MediaItemImage
    extra = 2
    fields = ['image', 'image_url', 'caption', 'order']


class MediaItemSectionInline(admin.TabularInline):
    model = MediaItemSection
    extra = 1
    fields = ['title', 'body', 'order']


class MediaItemVideoInline(admin.TabularInline):
    model = MediaItemVideo
    extra = 1
    fields = ['video_url', 'caption', 'order']


@admin.register(MediaItem)
class MediaItemAdmin(CloudinaryUploadMixin, admin.ModelAdmin):
    cld_video_field = 'video_url'
    cld_image_field = 'image_url'
    cld_folder = 'msraa/medios'
    inlines = [MediaItemSectionInline, MediaItemVideoInline, MediaItemImageInline]
    list_display = ['img_preview', 'title', 'tipo', 'year', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['tipo', 'is_active']
    list_display_links = ['img_preview', 'title']
    ordering = ['-year', 'order']
    readonly_fields = ['img_preview_large', 'cloudinary_video_btn', 'cloudinary_image_btn']
    fields = [
        'tipo', 'year', 'title', 'title_en',
        'description', 'description_en',
        'image', 'image_url', 'img_preview_large', 'cloudinary_image_btn',
        'url', 'url_label', 'url_label_en',
        'video_url', 'cloudinary_video_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def save_model(self, request, obj, form, change):
        _safe_save(self, request, obj, form, change)

    @admin.action(description='✅ Activar seleccionados')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='🚫 Desactivar seleccionados')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.display(description='Imagen')
    def img_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:60px;object-fit:cover;border-radius:3px">', obj.image.url)
        return '—'

    @admin.display(description='Vista previa')
    def img_preview_large(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height:200px;max-width:400px;object-fit:cover;border-radius:4px;margin-top:8px">', obj.image.url)
        return '—'


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'name', 'email', 'phone', 'project_type', 'short_message', 'is_read']
    list_display_links = ['created_at', 'name']
    list_filter = ['is_read', 'created_at']
    list_editable = ['is_read']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['name', 'phone', 'email', 'project_type', 'message', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_read', 'mark_unread']

    @admin.display(description='Mensaje')
    def short_message(self, obj):
        return obj.message[:80] + '…' if len(obj.message) > 80 else obj.message

    @admin.action(description='Marcar como leído')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Marcar como no leído')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
