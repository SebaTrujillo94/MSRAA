"""
Management command to auto-translate all empty _en fields using Groq API.
Reads Spanish source fields, translates to English, saves _en counterparts.

Usage:
    python manage.py auto_translate --api-key=gsk_xxx
    python manage.py auto_translate --api-key=gsk_xxx --dry-run   # preview only
    python manage.py auto_translate --api-key=gsk_xxx --force     # overwrite existing

    Or set env var GROQ_API_KEY and omit --api-key.
"""
import os
from groq import Groq
from django.core.management.base import BaseCommand
from core.models import (
    SiteConfiguration, MenuItem, PortfolioCategory,
    PortfolioProject, MediaItem, CurriculumItem, HeroVideo,
)


TRANSLATE_PROMPT = (
    "You are a professional translator for an architecture firm's website. "
    "Translate the following Spanish text to English. "
    "Preserve ALL-CAPS formatting, punctuation, line breaks, and tone exactly. "
    "Reply with ONLY the translated text, nothing else."
)


def _translate(client, text):
    if not text or not text.strip():
        return ''
    resp = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        max_tokens=1024,
        messages=[
            {'role': 'system', 'content': TRANSLATE_PROMPT},
            {'role': 'user', 'content': text},
        ],
    )
    return resp.choices[0].message.content.strip()


class Command(BaseCommand):
    help = 'Auto-translate Spanish DB fields to English using Claude API'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--force', action='store_true', help='Overwrite existing _en values')
        parser.add_argument('--api-key', default='', help='Groq API key (or set GROQ_API_KEY env var)')

    def handle(self, *args, **options):
        dry = options['dry_run']
        force = options['force']
        api_key = options['api_key'] or os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            self.stderr.write('ERROR: provide --api-key=gsk_xxx or set GROQ_API_KEY env var')
            return
        client = Groq(api_key=api_key)
        total = 0

        def tr(es_text, en_field_name):
            nonlocal total
            if not es_text:
                return None
            self.stdout.write(f'  [{en_field_name}] "{es_text[:60]}..."')
            if dry:
                return '(dry-run)'
            result = _translate(client, es_text)
            total += 1
            return result

        def maybe_set(obj, field_en, es_text):
            current = getattr(obj, field_en, '')
            if current and not force:
                self.stdout.write(self.style.WARNING(f'  skip {field_en} (already set)'))
                return False
            translated = tr(es_text, field_en)
            if translated is None:
                return False
            if not dry:
                setattr(obj, field_en, translated)
            return True

        # SiteConfiguration
        self.stdout.write(self.style.SUCCESS('=== SiteConfiguration ==='))
        cfg = SiteConfiguration.get_solo()
        fields = [
            ('about_label_en', cfg.about_label),
            ('about_p1_en', cfg.about_p1),
            ('about_p2_en', cfg.about_p2),
            ('stat1_prefix_en', cfg.stat1_prefix),
            ('stat1_label_en', cfg.stat1_label),
            ('stat2_prefix_en', cfg.stat2_prefix),
            ('stat2_label_en', cfg.stat2_label),
            ('stat3_prefix_en', cfg.stat3_prefix),
            ('stat3_label_en', cfg.stat3_label),
            ('trust_lbl_en', cfg.trust_lbl),
            ('trust_title_en', cfg.trust_title),
            ('trust_sub_en', cfg.trust_sub),
            ('footer_copy_en', cfg.footer_copy),
        ]
        changed = any(maybe_set(cfg, f, v) for f, v in fields)
        if changed and not dry:
            cfg.save()

        # MenuItem
        self.stdout.write(self.style.SUCCESS('=== MenuItems ==='))
        for item in MenuItem.objects.all():
            changed = maybe_set(item, 'label_en', item.label)
            if changed and not dry:
                item.save()

        # PortfolioCategory
        self.stdout.write(self.style.SUCCESS('=== PortfolioCategories ==='))
        for cat in PortfolioCategory.objects.all():
            changed = maybe_set(cat, 'name_en', cat.name)
            if changed and not dry:
                cat.save()

        # PortfolioProject
        self.stdout.write(self.style.SUCCESS('=== PortfolioProjects ==='))
        for p in PortfolioProject.objects.all():
            f1 = maybe_set(p, 'title_en', p.title)
            f2 = maybe_set(p, 'description_en', p.description)
            f3 = maybe_set(p, 'location_en', p.location)
            if (f1 or f2 or f3) and not dry:
                p.save()

        # MediaItem
        self.stdout.write(self.style.SUCCESS('=== MediaItems ==='))
        for m in MediaItem.objects.all():
            f1 = maybe_set(m, 'title_en', m.title)
            f2 = maybe_set(m, 'description_en', m.description)
            f3 = maybe_set(m, 'url_label_en', m.url_label)
            if (f1 or f2 or f3) and not dry:
                m.save()

        # CurriculumItem
        self.stdout.write(self.style.SUCCESS('=== CurriculumItems ==='))
        for c in CurriculumItem.objects.all():
            f1 = maybe_set(c, 'title_en', c.title)
            f2 = maybe_set(c, 'subtitle_en', c.subtitle)
            f3 = maybe_set(c, 'url_label_en', c.url_label)
            if (f1 or f2 or f3) and not dry:
                c.save()

        # HeroVideo
        self.stdout.write(self.style.SUCCESS('=== HeroVideos ==='))
        for v in HeroVideo.objects.all():
            f1 = maybe_set(v, 'title_line1_en', v.title_line1)
            f2 = maybe_set(v, 'title_line2_en', v.title_line2)
            if (f1 or f2) and not dry:
                v.save()

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {total} translations applied{"" if not dry else " (dry-run, nothing saved)"}.'
        ))
