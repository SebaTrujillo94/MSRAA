"""
Import portfolio projects from a local folder structure.

Expected structure:
    root_folder/
    ├── Proyecto A/
    │   ├── portada.jpg        ← hero image (or first image found)
    │   ├── foto1.jpg
    │   ├── foto2.jpg
    │   └── info.txt           ← optional metadata (Clave: Valor)
    └── Proyecto B/
        ├── hero.jpg
        ├── imagen_01.jpg
        └── descripcion.txt

info.txt accepted keys (case-insensitive, Spanish or English):
    Titulo / Title        → title
    Año / Year            → year
    Ubicacion / Location  → location
    Descripcion           → description
    Categoria / Category  → category name or slug

Usage:
    python manage.py import_portfolio /ruta/a/carpetas
    python manage.py import_portfolio /ruta/a/carpetas --category arquitectura
    python manage.py import_portfolio /ruta/a/carpetas --dry-run
    python manage.py import_portfolio /ruta/a/carpetas --start-order 10
"""

import os
import sys

import cloudinary
import cloudinary.uploader
from django.core.management.base import BaseCommand, CommandError

from core.models import PortfolioCategory, PortfolioProject, PortfolioProjectImage

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff', '.tif'}

HERO_KEYWORDS = {'hero', 'portada', 'cover', 'principal', 'main', 'front'}

# Mapping of text file keys → PortfolioProject field names
_KEY_MAP = {
    'titulo': 'title',
    'title': 'title',
    'año': 'year',
    'anio': 'year',
    'year': 'year',
    'ubicacion': 'location',
    'ubicación': 'location',
    'location': 'location',
    'descripcion': 'description',
    'descripción': 'description',
    'description': 'description',
    'categoria': '_category',
    'categoría': '_category',
    'category': '_category',
}


def _parse_info(filepath):
    """Parse a Clave: Valor text file. Returns dict with raw keys lowercased."""
    info = {}
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except OSError:
        return info

    # Try key:value format first
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            raw_key, _, val = line.partition(':')
            key = raw_key.strip().lower()
            mapped = _KEY_MAP.get(key, key)
            if mapped not in info:
                info[mapped] = val.strip()

    # If no key:value found, treat whole file as description
    if not info:
        text = ''.join(lines).strip()
        if text:
            info['description'] = text

    return info


def _find_images(folder):
    """Return sorted list of image filenames in folder."""
    files = []
    for name in os.listdir(folder):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTS:
            files.append(name)
    return sorted(files)


def _split_hero(image_files):
    """Return (hero_filename, gallery_filenames).
    Hero = file with hero keyword in name, or first image alphabetically."""
    for fname in image_files:
        stem = os.path.splitext(fname)[0].lower()
        if any(kw in stem for kw in HERO_KEYWORDS):
            gallery = [f for f in image_files if f != fname]
            return fname, gallery
    if image_files:
        return image_files[0], image_files[1:]
    return None, []


def _resolve_category(name_or_slug):
    """Lookup PortfolioCategory by slug or name (case-insensitive)."""
    if not name_or_slug:
        return None
    cat = PortfolioCategory.objects.filter(slug__iexact=name_or_slug).first()
    if not cat:
        cat = PortfolioCategory.objects.filter(name__icontains=name_or_slug).first()
    return cat


def _upload(path, dry_run):
    """Upload image to Cloudinary. Returns secure_url string."""
    if dry_run:
        return f'[DRY_RUN:{os.path.basename(path)}]'
    result = cloudinary.uploader.upload(
        path,
        folder='msraa/portfolio',
        resource_type='image',
        overwrite=False,
        unique_filename=True,
    )
    return result['secure_url']


class Command(BaseCommand):
    help = 'Import portfolio projects from a local folder (one subfolder per project)'

    def add_arguments(self, parser):
        parser.add_argument(
            'folder',
            type=str,
            help='Path to root folder containing one subfolder per project',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='',
            metavar='SLUG_OR_NAME',
            help='Default category for all imported projects (slug or name)',
        )
        parser.add_argument(
            '--start-order',
            type=int,
            default=None,
            metavar='N',
            help='Starting order value (default: after last existing project)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview actions without uploading or creating DB records',
        )

    def handle(self, *args, **options):
        root = options['folder']
        dry_run = options['dry_run']
        default_cat_arg = options['category']
        start_order = options['start_order']

        if not os.path.isdir(root):
            raise CommandError(f'No existe la carpeta: {root}')

        default_category = _resolve_category(default_cat_arg)
        if default_cat_arg and not default_category:
            self.stderr.write(
                self.style.WARNING(
                    f'⚠️  Categoría "{default_cat_arg}" no encontrada — se creará sin categoría'
                )
            )

        if start_order is None:
            last = PortfolioProject.objects.order_by('-order').values_list('order', flat=True).first()
            start_order = (last or 0) + 1

        if dry_run:
            self.stdout.write(self.style.WARNING('--- MODO DRY-RUN: no se creará nada ---\n'))

        # List project subfolders
        subfolders = sorted([
            d for d in os.listdir(root)
            if os.path.isdir(os.path.join(root, d)) and not d.startswith('.')
        ])

        if not subfolders:
            raise CommandError(f'No se encontraron subcarpetas en: {root}')

        self.stdout.write(f'Encontradas {len(subfolders)} carpetas de proyectos.\n')

        created = 0
        errors = 0

        for i, folder_name in enumerate(subfolders):
            project_path = os.path.join(root, folder_name)
            order = start_order + i

            try:
                self._process_project(
                    project_path=project_path,
                    folder_name=folder_name,
                    order=order,
                    default_category=default_category,
                    dry_run=dry_run,
                )
                created += 1
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f'❌  {folder_name}: {exc}')
                )
                errors += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY-RUN completo. {created} proyectos serían importados, {errors} errores.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅  Importación completa: {created} proyectos creados, {errors} errores.'))

    def _process_project(self, project_path, folder_name, order, default_category, dry_run):
        # 1. Parse text file (if any)
        info = {}
        txt_files = [
            f for f in os.listdir(project_path)
            if f.lower().endswith('.txt') and not f.startswith('.')
        ]
        if txt_files:
            info = _parse_info(os.path.join(project_path, txt_files[0]))

        title = info.get('title') or folder_name
        year = info.get('year') or '2024'
        location = info.get('location') or ''
        description = info.get('description') or ''

        # Category: text file overrides default
        category = default_category
        if info.get('_category'):
            cat = _resolve_category(info['_category'])
            if cat:
                category = cat
            else:
                self.stderr.write(
                    self.style.WARNING(f'  ⚠️  Categoría "{info["_category"]}" no encontrada, usando default')
                )

        # 2. Find images
        image_files = _find_images(project_path)
        hero_file, gallery_files = _split_hero(image_files)

        if not hero_file:
            self.stderr.write(self.style.WARNING(f'  ⚠️  {folder_name}: sin imágenes'))

        # 3. Upload hero
        hero_url = ''
        if hero_file:
            self.stdout.write(f'  📤 Hero: {hero_file}')
            hero_url = _upload(os.path.join(project_path, hero_file), dry_run)

        # 4. Print summary
        self.stdout.write(
            f'\n📁 {folder_name}\n'
            f'   Título:      {title}\n'
            f'   Año:         {year}\n'
            f'   Ubicación:   {location or "—"}\n'
            f'   Categoría:   {category.name if category else "— (sin categoría)"}\n'
            f'   Hero:        {hero_file or "—"}\n'
            f'   Galería:     {len(gallery_files)} imágenes\n'
            f'   Orden:       {order}'
        )

        if dry_run:
            return

        # 5. Create PortfolioProject
        project = PortfolioProject.objects.create(
            title=title,
            title_en='',
            category=category,
            description=description,
            description_en='',
            year=year,
            location=location,
            location_en='',
            hero_image_url=hero_url,
            order=order,
            is_active=False,  # start inactive — review before publishing
        )

        # 6. Upload + create gallery images
        for j, fname in enumerate(gallery_files):
            self.stdout.write(f'  📤 [{j+1}/{len(gallery_files)}] {fname}')
            img_url = _upload(os.path.join(project_path, fname), dry_run)
            PortfolioProjectImage.objects.create(
                project=project,
                image_url=img_url,
                order=j + 1,
            )

        self.stdout.write(self.style.SUCCESS(f'  ✅ Proyecto creado (id={project.pk}, is_active=False)'))
