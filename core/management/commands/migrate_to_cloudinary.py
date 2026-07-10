"""
Migrate local media files to Cloudinary.

Finds all DB records that still reference local files (not yet on Cloudinary)
and uploads each file, then updates the record to use the Cloudinary URL.

Usage:
    python manage.py migrate_to_cloudinary
    python manage.py migrate_to_cloudinary --dry-run
    python manage.py migrate_to_cloudinary --model MediaItem
    python manage.py migrate_to_cloudinary --folder msraa/media

Models handled:
    MediaItem           ->uploads image, sets image_url
    MediaItemImage      ->uploads image, sets image_url
    CurriculumItemImage ->uploads image, sets image_url
    ClientLogo          ->uploads image, updates image.name with Cloudinary public_id
"""

import os

import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.management.base import BaseCommand

MEDIA_ROOT = str(settings.MEDIA_ROOT)


def _is_cloudinary(url_or_name: str) -> bool:
    return 'cloudinary.com' in url_or_name or url_or_name.startswith('msraa/')


def _local_path(field_name: str) -> str | None:
    """Return absolute path if file exists locally, else None."""
    if not field_name:
        return None
    if _is_cloudinary(field_name):
        return None
    path = os.path.join(MEDIA_ROOT, field_name)
    return path if os.path.isfile(path) else None


def _upload(path: str, folder: str, dry_run: bool) -> dict | None:
    if dry_run:
        return {'secure_url': f'[DRY_RUN:{os.path.basename(path)}]',
                'public_id': f'dry_run/{os.path.basename(path)}'}
    with open(path, 'rb') as f:
        data = f.read()
    result = cloudinary.uploader.upload(
        data,
        folder=folder,
        resource_type='image',
        overwrite=False,
        unique_filename=True,
    )
    return result


class Command(BaseCommand):
    help = 'Upload local media files to Cloudinary and update DB records'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Preview without uploading or writing to DB')
        parser.add_argument('--model', type=str, default='',
                            help='Only process this model (MediaItem, MediaItemImage, CurriculumItemImage, ClientLogo)')
        parser.add_argument('--folder', type=str, default='msraa/media',
                            help='Cloudinary folder prefix (default: msraa/media)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_model = options['model'].lower()
        folder = options['folder'].rstrip('/')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n--- MODO DRY-RUN ---\n'))

        total_ok = total_skip = total_err = 0

        tasks = [
            ('MediaItem',           self._migrate_media_items),
            ('MediaItemImage',      self._migrate_media_item_images),
            ('CurriculumItemImage', self._migrate_curriculum_images),
            ('ClientLogo',          self._migrate_client_logos),
        ]

        for name, fn in tasks:
            if only_model and only_model != name.lower():
                continue
            ok, skip, err = fn(folder, dry_run)
            total_ok += ok; total_skip += skip; total_err += err

        self.stdout.write('')
        style = self.style.SUCCESS if not total_err else self.style.WARNING
        self.stdout.write(style(
            f'Resultado: {total_ok} migrados, {total_skip} ya en Cloudinary, {total_err} errores'
        ))

    # ------------------------------------------------------------------ #

    def _migrate_media_items(self, folder, dry_run):
        from core.models import MediaItem
        ok = skip = err = 0
        self.stdout.write('\n[MediaItem — portadas]')
        for obj in MediaItem.objects.all():
            # Already has a Cloudinary URL ->skip
            if obj.image_url and _is_cloudinary(obj.image_url):
                self.stdout.write(f'  SKIP  id={obj.id} {obj.title[:40]}')
                skip += 1
                continue
            # Has local file?
            path = _local_path(str(obj.image) if obj.image else '')
            if not path:
                self.stdout.write(f'  EMPTY id={obj.id} {obj.title[:40]} (sin imagen local)')
                skip += 1
                continue
            try:
                result = _upload(path, f'{folder}/medios', dry_run)
                if not dry_run:
                    obj.image_url = result['secure_url']
                    obj.save(update_fields=['image_url'])
                self.stdout.write(self.style.SUCCESS(
                    f'  OK    id={obj.id} {obj.title[:40]} ->{result["secure_url"][:60]}'
                ))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERR   id={obj.id} {obj.title[:40]}: {e}'))
                err += 1
        return ok, skip, err

    def _migrate_media_item_images(self, folder, dry_run):
        from core.models import MediaItemImage
        ok = skip = err = 0
        self.stdout.write('\n[MediaItemImage — galería]')
        for obj in MediaItemImage.objects.select_related('media_item').all():
            if obj.image_url and _is_cloudinary(obj.image_url):
                skip += 1; continue
            path = _local_path(str(obj.image) if obj.image else '')
            if not path:
                skip += 1; continue
            label = f'id={obj.id} [{obj.media_item.title[:30]}] img#{obj.order}'
            try:
                result = _upload(path, f'{folder}/medios/gallery', dry_run)
                if not dry_run:
                    obj.image_url = result['secure_url']
                    obj.save(update_fields=['image_url'])
                self.stdout.write(self.style.SUCCESS(f'  OK    {label}'))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERR   {label}: {e}'))
                err += 1
        return ok, skip, err

    def _migrate_curriculum_images(self, folder, dry_run):
        from core.models import CurriculumItemImage
        ok = skip = err = 0
        self.stdout.write('\n[CurriculumItemImage]')
        for obj in CurriculumItemImage.objects.select_related('curriculum_item').all():
            if obj.image_url and _is_cloudinary(obj.image_url):
                skip += 1; continue
            path = _local_path(str(obj.image) if obj.image else '')
            if not path:
                skip += 1; continue
            label = f'id={obj.id} [{obj.curriculum_item.title[:30]}] img#{obj.order}'
            try:
                result = _upload(path, f'{folder}/curriculum', dry_run)
                if not dry_run:
                    obj.image_url = result['secure_url']
                    obj.save(update_fields=['image_url'])
                self.stdout.write(self.style.SUCCESS(f'  OK    {label}'))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERR   {label}: {e}'))
                err += 1
        return ok, skip, err

    def _migrate_client_logos(self, folder, dry_run):
        from core.models import ClientLogo
        ok = skip = err = 0
        self.stdout.write('\n[ClientLogo]')
        for obj in ClientLogo.objects.all():
            field_name = str(obj.image) if obj.image else ''
            if _is_cloudinary(field_name):
                self.stdout.write(f'  SKIP  id={obj.id} {obj.name[:40]}')
                skip += 1
                continue
            path = _local_path(field_name)
            if not path:
                self.stdout.write(f'  EMPTY id={obj.id} {obj.name[:40]} (sin imagen local)')
                skip += 1
                continue
            try:
                result = _upload(path, f'{folder}/logos', dry_run)
                if not dry_run:
                    # MediaCloudinaryStorage uses public_id as the stored field value
                    obj.image.name = result['public_id']
                    obj.save(update_fields=['image'])
                self.stdout.write(self.style.SUCCESS(
                    f'  OK    id={obj.id} {obj.name[:40]} ->{result["public_id"]}'
                ))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERR   id={obj.id} {obj.name}: {e}'))
                err += 1
        return ok, skip, err
