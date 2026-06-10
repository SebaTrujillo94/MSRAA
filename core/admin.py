from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, PortfolioProjectImage
)


class PortfolioProjectImageInline(admin.TabularInline):
    model = PortfolioProjectImage
    extra = 2
    fields = ['image', 'size', 'order']


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
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
    )


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
