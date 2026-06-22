"""
Populate DB with example data for all models.
Safe to run multiple times — skips if data already exists.
"""
from django.core.management.base import BaseCommand
from core.models import (
    SiteConfiguration, MenuItem, PortfolioCategory, PortfolioProject,
    CurriculumItem, MediaItem, HeroVideo, ClientLogo,
)


class Command(BaseCommand):
    help = 'Seed DB with example data'

    def handle(self, *args, **options):
        self._site_config()
        self._hero_videos()
        self._menu_items()
        self._portfolio()
        self._curriculum()
        self._media()
        self.stdout.write(self.style.SUCCESS('Seed complete.'))

    def _site_config(self):
        cfg = SiteConfiguration.get_solo()
        if cfg.contact_email == 'contacto@msraa.cl' and not cfg.about_p1:
            cfg.contact_email = 'contacto@msraa.cl'
            cfg.contact_phone = '+56 9 1234 5678'
            cfg.about_label = 'SOBRE EL PROYECTO'
            cfg.about_p1 = (
                'Cuatro volúmenes dibujan su órbita en torno a un vacío central '
                'que actúa como corazón del proyecto. La luz natural penetra desde '
                'múltiples ángulos, creando una danza de sombras que transforma el '
                'espacio a lo largo del día.'
            )
            cfg.about_p2 = (
                'Las fachadas están marcadas por una rigurosa modulación que refleja '
                'la precisión técnica del proceso constructivo. Cada detalle ha sido '
                'pensado para que la obra dialogue con su entorno y perdure en el tiempo.'
            )
            cfg.stat1_number = 50
            cfg.stat1_prefix = 'Proyectos'
            cfg.stat1_label = 'Instalaciones completadas'
            cfg.stat2_number = 10
            cfg.stat2_prefix = 'Difusión'
            cfg.stat2_label = 'Publicaciones especializadas'
            cfg.stat3_number = 300
            cfg.stat3_prefix = 'Superficie construida'
            cfg.stat3_label = 'M² construidos en todo Chile'
            cfg.trust_lbl = 'QUIENES NOS HAN CONFIADO SU VISIÓN'
            cfg.trust_title = 'ORGULLOSOS DE CADA COLABORACIÓN'
            cfg.trust_sub = (
                'Agradecemos profundamente la confianza de nuestros clientes, '
                'cuya visión y colaboración han sido fundamentales para crear '
                'proyectos que transforman espacios y comunidades.'
            )
            cfg.footer_copy = '© 2026 MSRAA ESTUDIO DE ARQUITECTURA'
            cfg.save()
            self.stdout.write('  SiteConfiguration updated')

    def _hero_videos(self):
        if HeroVideo.objects.exists():
            self.stdout.write('  HeroVideos already exist — skip')
            return
        videos = [
            {'title_line1': 'MSRAA ARQUITECTOS', 'title_line2': 'EDIFICIO STARTUP REPUBLICA', 'order': 0},
            {'title_line1': 'DISEÑO', 'title_line2': 'Y CONSTRUCCIÓN', 'order': 1},
            {'title_line1': 'ARQUITECTURA', 'title_line2': 'DE EXCELENCIA', 'order': 2},
        ]
        for v in videos:
            HeroVideo.objects.create(**v, is_active=True)
        self.stdout.write(f'  Created {len(videos)} HeroVideos')

    def _menu_items(self):
        if MenuItem.objects.exists():
            self.stdout.write('  MenuItems already exist — skip')
            return
        items = [
            ('Casas', 'proyectos', '#proyectos', 'CASAS', 1),
            ('Edificios', 'proyectos', '#proyectos', 'EDIFICIOS', 2),
            ('Educación', 'proyectos', '#proyectos', 'EDUCACIÓN', 3),
            ('Artículos', 'publicaciones', '#publicaciones', '', 1),
            ('Premios', 'publicaciones', '#publicaciones', '', 2),
            ('Formación', 'curriculum', '#curriculum', '', 1),
            ('Experiencia', 'curriculum', '#curriculum', '', 2),
            ('Calculadora M²', 'herramientas', '#herramientas', '', 1),
            ('Contacto', 'contacto', '#contacto', '', 1),
        ]
        for label, section, url, fv, order in items:
            MenuItem.objects.create(
                label=label, section_group=section,
                url=url, filter_value=fv, order=order, is_active=True
            )
        self.stdout.write(f'  Created {len(items)} MenuItems')

    def _portfolio(self):
        if PortfolioCategory.objects.exists():
            self.stdout.write('  Portfolio already exists — skip')
            return
        cats = [
            ('CASAS', 'casas'),
            ('EDIFICIOS', 'edificios'),
            ('EDUCACIÓN', 'educacion'),
        ]
        cat_objs = {}
        for name, slug in cats:
            cat_objs[slug] = PortfolioCategory.objects.create(name=name, slug=slug, is_active=True)

        projects = [
            {
                'title': 'Casa Particular Las Condes',
                'category': cat_objs['casas'],
                'description': 'Residencia unifamiliar de 320 m² en Las Condes. Diseño contemporáneo con énfasis en la integración de espacios interiores y exteriores, luz natural y materialidad local.',
                'year': '2023',
                'location': 'Las Condes, Santiago',
                'hero_image_url': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800',
                'order': 1,
            },
            {
                'title': 'Edificio Residencial Ñuñoa',
                'category': cat_objs['edificios'],
                'description': 'Edificio de 8 pisos con 32 departamentos. Proyecto de arquitectura sustentable con certificación EDGE, paneles solares y sistema de reutilización de aguas grises.',
                'year': '2022',
                'location': 'Ñuñoa, Santiago',
                'hero_image_url': 'https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800',
                'order': 2,
            },
            {
                'title': 'Colegio Nuevo Horizonte',
                'category': cat_objs['educacion'],
                'description': 'Establecimiento educacional para 800 alumnos. Diseño pedagógico innovador con aulas flexibles, patio cubierto multipropósito y biblioteca central.',
                'year': '2021',
                'location': 'Maipú, Santiago',
                'hero_image_url': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800',
                'order': 3,
            },
            {
                'title': 'Casa de Playa Maitencillo',
                'category': cat_objs['casas'],
                'description': 'Vivienda de veraneo en primera línea de playa. Estructura de madera y vidrio diseñada para resistir el ambiente marino y maximizar las vistas al Pacífico.',
                'year': '2024',
                'location': 'Maitencillo, Valparaíso',
                'hero_image_url': 'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=800',
                'order': 4,
            },
        ]
        for p in projects:
            PortfolioProject.objects.create(**p, is_active=True)
        self.stdout.write(f'  Created {len(cats)} categories, {len(projects)} projects')

    def _curriculum(self):
        if CurriculumItem.objects.exists():
            self.stdout.write('  CurriculumItems already exist — skip')
            return
        items = [
            {
                'category': 'formacion',
                'year': '2005 — 2011',
                'title': 'Arquitecto',
                'subtitle': 'Pontificia Universidad Católica de Chile',
                'order': 1,
            },
            {
                'category': 'formacion',
                'year': '2012 — 2013',
                'title': 'Magíster en Arquitectura',
                'subtitle': 'Universidad de Chile',
                'order': 2,
            },
            {
                'category': 'experiencia',
                'year': '2014 —',
                'title': 'Director — MSRAA Estudio de Arquitectura',
                'subtitle': 'Santiago, Chile',
                'order': 1,
            },
            {
                'category': 'experiencia',
                'year': '2011 — 2014',
                'title': 'Arquitecto Asociado',
                'subtitle': 'Estudio Undurraga Devés Arquitectos',
                'order': 2,
            },
            {
                'category': 'reconocimientos',
                'year': '2022',
                'title': 'Premio Mejor Obra de Arquitectura Sustentable',
                'subtitle': 'Colegio de Arquitectos de Chile',
                'order': 1,
            },
            {
                'category': 'reconocimientos',
                'year': '2019',
                'title': 'Finalista Premio Nacional de Arquitectura',
                'subtitle': 'Ministerio de Vivienda y Urbanismo',
                'order': 2,
            },
            {
                'category': 'publicaciones',
                'year': '2023',
                'title': 'Arquitectura Contemporánea en Chile',
                'subtitle': 'Revista ARQ, Edición 112',
                'order': 1,
            },
        ]
        for item in items:
            CurriculumItem.objects.create(**item, is_active=True)
        self.stdout.write(f'  Created {len(items)} CurriculumItems')

    def _media(self):
        if MediaItem.objects.exists():
            self.stdout.write('  MediaItems already exist — skip')
            return
        items = [
            {
                'tipo': 'premio',
                'year': '2022',
                'title': 'Premio Mejor Obra Sustentable 2022',
                'description': 'MSRAA Estudio recibe reconocimiento del Colegio de Arquitectos de Chile por el diseño del Edificio Residencial Ñuñoa, destacando su eficiencia energética y uso de materiales locales.',
                'image_url': 'https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=600',
                'url_label': 'Ver más',
                'order': 1,
            },
            {
                'tipo': 'publicacion',
                'year': '2023',
                'title': 'Arquitectura Contemporánea en Chile',
                'description': 'Artículo publicado en Revista ARQ sobre las tendencias actuales en arquitectura residencial chilena, con especial énfasis en la integración paisajística y la sostenibilidad.',
                'image_url': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600',
                'url_label': 'Leer artículo',
                'order': 2,
            },
            {
                'tipo': 'charla',
                'year': '2023',
                'title': 'Conferencia: Diseño Sustentable en el Siglo XXI',
                'description': 'Presentación en el Congreso Latinoamericano de Arquitectura sobre estrategias de diseño pasivo y el rol del arquitecto frente al cambio climático.',
                'image_url': 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600',
                'url_label': 'Ver presentación',
                'order': 3,
            },
        ]
        for item in items:
            MediaItem.objects.create(**item, is_active=True)
        self.stdout.write(f'  Created {len(items)} MediaItems')
