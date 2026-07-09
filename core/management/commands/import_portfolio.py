"""
Import portfolio projects directly from a Dropbox shared folder URL or a local folder.

Usage (Dropbox URL):
    python manage.py import_portfolio "https://www.dropbox.com/scl/fo/..."
    python manage.py import_portfolio "https://www.dropbox.com/scl/fo/..." --category arquitectura
    python manage.py import_portfolio "https://www.dropbox.com/scl/fo/..." --dry-run

Usage (local folder):
    python manage.py import_portfolio /ruta/a/carpetas --dry-run

Expected folder structure:
    root/
    ├── Proyecto A/
    │   ├── portada.jpg        ← hero (or first image found)
    │   ├── foto1.jpg
    │   ├── foto2.jpg
    │   └── info.txt           ← optional: Clave: Valor
    └── Proyecto B/
        └── ...

info.txt accepted keys (case-insensitive):
    Titulo / Title, Año / Year, Ubicacion / Location, Descripcion / Description, Categoria
"""

import io
import os
import urllib.request
import zipfile

import cloudinary
import cloudinary.uploader
from django.core.management.base import BaseCommand, CommandError

from core.models import PortfolioCategory, PortfolioProject, PortfolioProjectImage

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.tif', '.tiff'}
HERO_KEYWORDS = {'hero', 'portada', 'cover', 'principal', 'main', 'front'}

_KEY_MAP = {
    'titulo': 'title', 'title': 'title',
    'año': 'year', 'anio': 'year', 'year': 'year',
    'ubicacion': 'location', 'ubicación': 'location', 'location': 'location',
    'descripcion': 'description', 'descripción': 'description', 'description': 'description',
    'categoria': '_category', 'categoría': '_category', 'category': '_category',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_info_bytes(data: bytes) -> dict:
    info = {}
    try:
        text = data.decode('utf-8', errors='replace')
    except Exception:
        return info
    lines = text.splitlines()
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
    if not info and text.strip():
        info['description'] = text.strip()
    return info


def _split_hero(image_names):
    for name in image_names:
        stem = os.path.splitext(name)[0].lower()
        if any(kw in stem for kw in HERO_KEYWORDS):
            return name, [n for n in image_names if n != name]
    if image_names:
        return image_names[0], image_names[1:]
    return None, []


def _resolve_category(name_or_slug):
    if not name_or_slug:
        return None
    cat = PortfolioCategory.objects.filter(slug__iexact=name_or_slug).first()
    if not cat:
        cat = PortfolioCategory.objects.filter(name__icontains=name_or_slug).first()
    return cat


def _upload_bytes(data: bytes, filename: str, dry_run: bool) -> str:
    if dry_run:
        return f'[DRY_RUN:{filename}]'
    result = cloudinary.uploader.upload(
        data,
        folder='msraa/portfolio',
        resource_type='image',
        overwrite=False,
        unique_filename=True,
    )
    return result['secure_url']


# ---------------------------------------------------------------------------
# ZIP-based processing (Dropbox download)
# ---------------------------------------------------------------------------

def _dropbox_zip_url(url: str) -> str:
    """Convert a Dropbox shared folder URL to a direct ZIP download URL."""
    url = url.strip()
    # Remove dl=0 or dl=1, then add dl=1
    import re
    url = re.sub(r'[&?]dl=\d', '', url)
    sep = '&' if '?' in url else '?'
    return url + sep + 'dl=1'


def _download_zip(url: str, stdout) -> io.BytesIO:
    stdout.write(f'⬇️  Descargando ZIP desde Dropbox...')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    stdout.write(f'   Descargado: {len(data) / 1024 / 1024:.1f} MB')
    return io.BytesIO(data)


def _extract_projects_from_zip(zip_buffer: io.BytesIO):
    """
    Parse ZIP structure. Returns dict: {project_folder_name: {images: [...], info_bytes: bytes|None}}
    Each entry: images = list of (name, bytes), sorted; info_bytes = content of first .txt or None.
    """
    with zipfile.ZipFile(zip_buffer) as zf:
        names = zf.namelist()

    # Find depth-1 folders (project folders)
    # ZIP paths look like: "Root Folder/Project A/foto.jpg"
    # We need to find the common root prefix first.
    with zipfile.ZipFile(zip_buffer) as zf:
        all_names = [n for n in zf.namelist() if not n.endswith('/')]

    # Determine common prefix (the Dropbox folder name wrapper)
    parts_list = [n.replace('\\', '/').split('/') for n in all_names]
    root_prefix = parts_list[0][0] if parts_list else ''
    # Verify all share this prefix
    for parts in parts_list:
        if parts[0] != root_prefix:
            root_prefix = ''
            break

    depth_offset = 1 if root_prefix else 0  # skip the wrapper folder

    projects = {}

    with zipfile.ZipFile(zip_buffer) as zf:
        for member in zf.infolist():
            path = member.filename.replace('\\', '/').rstrip('/')
            parts = path.split('/')
            # Skip root wrapper and entries that are too shallow
            rel_parts = parts[depth_offset:]
            if len(rel_parts) < 2:
                continue  # skip root-level files
            project_name = rel_parts[0]
            file_name = rel_parts[-1]
            if not file_name:
                continue  # it's a directory entry

            if project_name not in projects:
                projects[project_name] = {'images': [], 'info_bytes': None}

            ext = os.path.splitext(file_name)[1].lower()
            if ext in IMAGE_EXTS:
                data = zf.read(member.filename)
                projects[project_name]['images'].append((file_name, data))
            elif ext == '.txt' and projects[project_name]['info_bytes'] is None:
                projects[project_name]['info_bytes'] = zf.read(member.filename)

    # Sort images in each project
    for proj in projects.values():
        proj['images'].sort(key=lambda x: x[0].lower())

    return projects


# ---------------------------------------------------------------------------
# Local folder processing
# ---------------------------------------------------------------------------

def _extract_projects_from_folder(root: str):
    projects = {}
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isdir(path) or name.startswith('.'):
            continue
        images = []
        info_bytes = None
        for fname in sorted(os.listdir(path)):
            ext = os.path.splitext(fname)[1].lower()
            fpath = os.path.join(path, fname)
            if ext in IMAGE_EXTS:
                with open(fpath, 'rb') as f:
                    images.append((fname, f.read()))
            elif ext == '.txt' and info_bytes is None:
                with open(fpath, 'rb') as f:
                    info_bytes = f.read()
        projects[name] = {'images': images, 'info_bytes': info_bytes}
    return projects


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Import portfolio projects from a Dropbox URL or local folder'

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            type=str,
            help='Dropbox shared folder URL or local folder path',
        )
        parser.add_argument(
            '--category', type=str, default='', metavar='SLUG_OR_NAME',
            help='Default category for all projects',
        )
        parser.add_argument(
            '--start-order', type=int, default=None, metavar='N',
            help='Starting order value (default: after last existing project)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview without uploading or writing to DB',
        )

    def handle(self, *args, **options):
        source = options['source']
        dry_run = options['dry_run']
        cat_arg = options['category']
        start_order = options['start_order']

        default_category = _resolve_category(cat_arg)
        if cat_arg and not default_category:
            self.stderr.write(self.style.WARNING(
                f'⚠️  Categoría "{cat_arg}" no encontrada — proyectos quedarán sin categoría'
            ))

        if start_order is None:
            last = PortfolioProject.objects.order_by('-order').values_list('order', flat=True).first()
            start_order = (last or 0) + 1

        if dry_run:
            self.stdout.write(self.style.WARNING('\n--- MODO DRY-RUN: nada será creado ---\n'))

        # Load project data
        if source.startswith('http'):
            zip_url = _dropbox_zip_url(source)
            zip_buf = _download_zip(zip_url, self.stdout)
            projects = _extract_projects_from_zip(zip_buf)
        else:
            if not os.path.isdir(source):
                raise CommandError(f'No existe la carpeta: {source}')
            projects = _extract_projects_from_folder(source)

        if not projects:
            raise CommandError('No se encontraron carpetas de proyectos.')

        self.stdout.write(f'\nEncontrados {len(projects)} proyectos.\n')

        created = errors = 0

        for i, (folder_name, data) in enumerate(projects.items()):
            try:
                self._process(
                    folder_name=folder_name,
                    images=data['images'],
                    info_bytes=data['info_bytes'],
                    order=start_order + i,
                    default_category=default_category,
                    dry_run=dry_run,
                )
                created += 1
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'❌  {folder_name}: {exc}'))
                errors += 1

        self.stdout.write('')
        msg = f'{created} proyectos {"serían importados" if dry_run else "creados"}, {errors} errores.'
        self.stdout.write(self.style.SUCCESS(f'✅  {msg}') if not errors else self.style.WARNING(f'⚠️  {msg}'))

    def _process(self, folder_name, images, info_bytes, order, default_category, dry_run):
        # Parse metadata
        info = _parse_info_bytes(info_bytes) if info_bytes else {}
        title = info.get('title') or folder_name
        year = info.get('year') or '2024'
        location = info.get('location') or ''
        description = info.get('description') or ''

        category = default_category
        if info.get('_category'):
            cat = _resolve_category(info['_category'])
            if cat:
                category = cat

        # Split hero vs gallery
        image_names = [n for n, _ in images]
        hero_name, gallery_names = _split_hero(image_names)
        images_by_name = {n: d for n, d in images}

        self.stdout.write(
            f'\n📁 {folder_name}\n'
            f'   Título:    {title}\n'
            f'   Año:       {year}\n'
            f'   Ubicación: {location or "—"}\n'
            f'   Categoría: {category.name if category else "— (sin categoría)"}\n'
            f'   Hero:      {hero_name or "—"}\n'
            f'   Galería:   {len(gallery_names)} imágenes\n'
            f'   Orden:     {order}'
        )

        if dry_run:
            return

        # Upload hero
        hero_url = ''
        if hero_name:
            self.stdout.write(f'   📤 Hero: {hero_name}')
            hero_url = _upload_bytes(images_by_name[hero_name], hero_name, dry_run)

        # Create project (is_active=False → review before publishing)
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
            is_active=False,
        )

        # Upload gallery
        for j, gname in enumerate(gallery_names, 1):
            self.stdout.write(f'   📤 [{j}/{len(gallery_names)}] {gname}')
            img_url = _upload_bytes(images_by_name[gname], gname, dry_run)
            PortfolioProjectImage.objects.create(
                project=project,
                image_url=img_url,
                order=j,
            )

        self.stdout.write(self.style.SUCCESS(f'   ✅ Creado (id={project.pk})'))
