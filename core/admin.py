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
        # queryset.update() bypasses pre_save entirely — no Cloudinary trigger
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
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ['title_line1', 'title_line2', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    readonly_fields = ['cloudinary_upload_btn']
    fields = [
        'title_line1', 'title_line1_en',
        'title_line2', 'title_line2_en',
        'video_file', 'video_url', 'cloudinary_upload_btn',
        'order', 'is_active',
    ]
    actions = ['make_active', 'make_inactive']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/upload-cloudinary/',
                 self.admin_site.admin_view(self._upload_cloudinary_view),
                 name='herovideo_upload_cloudinary'),
        ]
        return custom + urls

    def _upload_cloudinary_view(self, request, pk):
        import json
        from django.http import JsonResponse
        from .models import _resolve_media_url
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        try:
            source_url = json.loads(request.body).get('url', '').strip()
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        if not source_url:
            return JsonResponse({'error': 'URL requerida'}, status=400)
        resolved = _resolve_media_url(source_url)
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                resolved,
                resource_type='video',
                folder='msraa/videos',
                public_id=f'herovideo_{pk}',
                overwrite=True,
            )
            cld_url = result['secure_url']
            HeroVideo.objects.filter(pk=pk).update(video_url=cld_url)
            return JsonResponse({'url': cld_url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    @admin.display(description='Subir a Cloudinary')
    def cloudinary_upload_btn(self, obj):
        if not obj.pk:
            return format_html('<span style="color:#999">Guarda el registro primero</span>')
        return format_html(
            '''<div>
              <button type="button" id="cld-btn"
                onclick="cldUpload({})"
                style="padding:8px 18px;background:#e05d20;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;font-weight:600;">
                &#x2601;&#xFE0F; Subir a Cloudinary desde URL
              </button>
              <span id="cld-status" style="margin-left:12px;font-size:13px;"></span>
              <p style="margin:5px 0 0;font-size:11px;color:#888">
                Cloudinary descarga el video desde Dropbox y lo sirve como CDN optimizado.<br>
                Puede tardar 1&#x2013;3 min seg&#xFA;n tama&#xF1;o. El campo URL se actualiza solo.
              </p>
            </div>
            <script>
            function cldUpload(pk) {{
              var btn = document.getElementById('cld-btn');
              var status = document.getElementById('cld-status');
              var urlField = document.getElementById('id_video_url');
              var url = urlField ? urlField.value.trim() : '';
              if (!url) {{
                status.style.color='#c00';
                status.textContent='&#10060; Ingresa una URL de Dropbox en el campo URL primero';
                return;
              }}
              btn.disabled = true;
              btn.textContent = '&#x23F3; Subiendo... puede tardar';
              status.textContent = '';
              var csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
              fetch('/admin/core/herovideo/'+pk+'/upload-cloudinary/', {{
                method: 'POST',
                headers: {{'Content-Type':'application/json','X-CSRFToken':csrf}},
                body: JSON.stringify({{url: url}})
              }})
              .then(r => r.json())
              .then(d => {{
                if (d.url) {{
                  urlField.value = d.url;
                  status.style.color='green';
                  status.textContent='&#x2705; Subido. Guarda el formulario para confirmar.';
                  btn.textContent='&#x2705; Subido';
                }} else {{
                  status.style.color='#c00';
                  status.textContent='&#10060; '+d.error;
                  btn.disabled=false;
                  btn.textContent='&#x2601;&#xFE0F; Subir a Cloudinary desde URL';
                }}
              }})
              .catch(() => {{
                status.style.color='#c00';
                status.textContent='&#10060; Timeout o error de red. Intenta de nuevo.';
                btn.disabled=false;
                btn.textContent='&#x2601;&#xFE0F; Subir a Cloudinary desde URL';
              }});
            }}
            </script>''',
            obj.pk
        )

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
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'year', 'location', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    inlines = [PortfolioProjectImageInline]
    fields = ['title', 'category', 'year', 'location', 'description', 'hero_image', 'hero_image_url', 'video_url', 'order', 'is_active']
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
class CurriculumItemAdmin(admin.ModelAdmin):
    inlines = [CurriculumItemImageInline]
    list_display = ['title', 'category', 'year', 'subtitle', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    ordering = ['category', 'order']
    fields = ['category', 'year', 'title', 'subtitle', 'url', 'url_label', 'video_url', 'order', 'is_active']
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
class MediaItemAdmin(admin.ModelAdmin):
    inlines = [MediaItemSectionInline, MediaItemVideoInline, MediaItemImageInline]
    list_display = ['img_preview', 'title', 'tipo', 'year', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['tipo', 'is_active']
    list_display_links = ['img_preview', 'title']
    ordering = ['-year', 'order']
    readonly_fields = ['img_preview_large']
    fields = ['tipo', 'year', 'title', 'description', 'image', 'image_url', 'img_preview_large', 'url', 'url_label', 'video_url', 'order', 'is_active']
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
