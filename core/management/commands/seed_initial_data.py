from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from decouple import config as env

from core.models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject,
    PortfolioProjectImage
)


class Command(BaseCommand):
    help = 'Seeds initial data: admin users, maintainer group, and default content. Idempotent.'

    def handle(self, *args, **options):
        self._create_superadmins()
        self._create_maintainer_group()
        self._seed_site_config()
        self._seed_menu_items()
        self._seed_hero_videos()
        self._seed_categories()
        self._seed_projects()
        self.stdout.write(self.style.SUCCESS('Seeding complete.'))

    def _create_superadmins(self):
        for i in [1, 2]:
            email = env(f'SUPERADMIN{i}_EMAIL', default=f'admin{i}@msraa.cl')
            password = env(f'SUPERADMIN{i}_PASSWORD', default='changeme123!')
            username = email.split('@')[0]
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(f'  Created superuser: {username} ({email})')
            else:
                self.stdout.write(f'  Superuser already exists: {username}')

    def _create_maintainer_group(self):
        group, created = Group.objects.get_or_create(name='Maintainer')
        if created:
            self.stdout.write('  Created Maintainer group')
        else:
            self.stdout.write('  Maintainer group already exists')

        # Grant view/add/change/delete on all content models — no auth models
        allowed_models = [
            SiteConfiguration, MenuItem, HeroVideo,
            ClientLogo, PortfolioCategory, PortfolioProject, PortfolioProjectImage,
        ]
        group.permissions.clear()
        for model in allowed_models:
            ct = ContentType.objects.get_for_model(model)
            for action in ['view', 'add', 'change', 'delete']:
                codename = f'{action}_{model._meta.model_name}'
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    pass
        self.stdout.write('  Maintainer permissions configured')

    def _seed_site_config(self):
        SiteConfiguration.get_solo()
        self.stdout.write('  SiteConfiguration singleton ready')

    def _seed_menu_items(self):
        if MenuItem.objects.exists():
            self.stdout.write('  Menu items already seeded')
            return

        items = [
            # (label, url, section_group, filter_value, order)
            ('EDUCACIÓN', '#portfolioMain', 'proyectos', 'EDUCACIÓN', 0),
            ('CASAS', '#portfolioMain', 'proyectos', 'CASAS', 1),
            ('INSTITUCIONAL', '#portfolioMain', 'proyectos', 'INSTITUCIONAL', 2),
            ('PUBLICACIONES', '#portfolioMain', 'publicaciones', 'PUBLICACIONES', 0),
            ('VER TODOS', '#portfolioMain', 'publicaciones', '', 1),
            ('CALCULADORA M²', '#calculadoraM2', 'herramientas', '', 0),
            ('CONTACTO', '#contacto', 'contacto', '', 0),
        ]
        for label, url, section, filter_val, order in items:
            MenuItem.objects.create(
                label=label, url=url, section_group=section,
                filter_value=filter_val, order=order, is_active=True
            )
        self.stdout.write(f'  Seeded {len(items)} menu items')

    def _seed_hero_videos(self):
        if HeroVideo.objects.exists():
            self.stdout.write('  Hero videos already seeded')
            return

        videos = [
            ('MSRAA ARQUITECTOS', 'EDIFICIO STARTUP REPUBLICA - UNAB REPUBLICA', '/static/videos/toma 1.mp4', 0),
            ('', '', '/static/videos/toma 2.mp4', 1),
            ('', '', '/static/videos/toma 3.mp4', 2),
        ]
        for t1, t2, url, order in videos:
            HeroVideo.objects.create(
                title_line1=t1, title_line2=t2,
                video_url=url, order=order, is_active=True
            )
        self.stdout.write('  Seeded 3 hero videos (update video_url to Cloudinary URLs for production)')

    def _seed_categories(self):
        if PortfolioCategory.objects.exists():
            self.stdout.write('  Portfolio categories already seeded')
            return

        cats = [
            ('CASAS', 'HOUSES', 'casas'),
            ('EDUCACIÓN', 'EDUCATION', 'educacion'),
            ('INSTITUCIONAL', 'INSTITUTIONAL', 'institucional'),
            ('PUBLICACIONES', 'PUBLICATIONS', 'publicaciones'),
        ]
        for name, name_en, slug in cats:
            PortfolioCategory.objects.create(name=name, name_en=name_en, slug=slug, is_active=True)
        self.stdout.write(f'  Seeded {len(cats)} portfolio categories')

    def _seed_projects(self):
        if PortfolioProject.objects.exists():
            self.stdout.write('  Portfolio projects already seeded')
            return

        projects = [
            {
                'title': 'CASA LA PALOMERA',
                'category': 'casas',
                'year': '2022',
                'location': 'VITACURA, CHILE',
                'description': (
                    'Nuestra filosofía de diseño se basa en la integración de las ideas del lugar '
                    'y el tiempo en que se emplaza la obra. Casa La Palomera busca una relación directa '
                    'entre los espacios interiores y exteriores, maximizando la luz natural y utilizando '
                    'materiales que cualifican los espacios, creando un refugio contemporáneo en el '
                    'sector oriente de Santiago.'
                ),
                'order': 0,
            },
            {
                'title': 'CAMPUS CREATIVO',
                'category': 'educacion',
                'year': '2019',
                'location': 'SANTIAGO, CHILE',
                'description': (
                    'El detallamiento meticuloso y el uso de prototipado 3D nos permite diseñar cada '
                    'parte del edificio bajo el mismo concepto del total. Campus Creativo fomenta la '
                    'interacción interdisciplinaria integrando el diseño urbano contemporáneo con las '
                    'necesidades educativas de vanguardia para Universidad Gabriela Mistral.'
                ),
                'order': 1,
            },
            {
                'title': 'EDIFICIO NUCLEO',
                'category': 'institucional',
                'year': '2021',
                'location': 'LAS CONDES, CHILE',
                'description': (
                    'La geometría pura y la materialidad honesta son los principios rectores de este '
                    'edificio institucional. Los planos se intersecan generando espacios de transición '
                    'que invitan a la exploración y el descubrimiento, mientras que la estructura vista '
                    'celebra la técnica constructiva como elemento expresivo.'
                ),
                'order': 2,
            },
            {
                'title': 'RESIDENCIA SIERRA BELLA',
                'category': 'casas',
                'year': '2023',
                'location': 'LO BARNECHEA, CHILE',
                'description': (
                    'Entendemos la arquitectura como un diálogo entre el habitante y su entorno. '
                    'Sierra Bella se integra al paisaje montañoso con una volumetría escalonada que '
                    'respeta la topografía natural, creando terrazas que capturan las vistas hacia '
                    'la cordillera en cada nivel de la residencia.'
                ),
                'order': 3,
            },
            {
                'title': 'PUBLICACIÓN ANUAL 2023',
                'category': 'publicaciones',
                'year': '2023',
                'location': 'SANTIAGO, CHILE',
                'description': (
                    'Documento de difusión anual que recopila los proyectos más destacados del '
                    'estudio. Esta publicación especializada explora los conceptos y metodologías '
                    'detrás de cada obra, compartiendo el proceso creativo y técnico que '
                    'caracteriza el trabajo de MSRAA.'
                ),
                'order': 4,
            },
            {
                'title': 'COLEGIO NORTE VERDE',
                'category': 'educacion',
                'year': '2020',
                'location': 'ANTOFAGASTA, CHILE',
                'description': (
                    'La sostenibilidad y el confort ambiental son pilares fundamentales en este '
                    'establecimiento educacional. El diseño aprovecha las condiciones climáticas '
                    'del norte chileno para crear espacios naturalmente ventilados e iluminados, '
                    'reduciendo el consumo energético y mejorando la experiencia de aprendizaje.'
                ),
                'order': 5,
            },
            {
                'title': 'CASA TUNQUEN',
                'category': 'casas',
                'year': '2024',
                'location': 'ALGARROBO, CHILE',
                'description': (
                    'Frente al Pacífico, esta residencia de descanso propone una arquitectura '
                    'que abraza el horizonte marino. Los espacios se organizan en torno a una '
                    'terraza central que actúa como corazón de la casa, difuminando los límites '
                    'entre el interior habitable y el paisaje costero.'
                ),
                'order': 6,
            },
            {
                'title': 'CENTRO CÍVICO MAIPÚ',
                'category': 'institucional',
                'year': '2022',
                'location': 'MAIPÚ, CHILE',
                'description': (
                    'Un espacio público que devuelve la plaza a la ciudadanía. El centro cívico '
                    'integra funciones municipales, culturales y de esparcimiento en un complejo '
                    'que celebra la diversidad y promueve el encuentro comunitario, con una '
                    'arquitectura que refleja la identidad y las aspiraciones de la comuna.'
                ),
                'order': 7,
            },
        ]

        category_map = {c.slug: c for c in PortfolioCategory.objects.all()}
        for pd in projects:
            cat = category_map.get(pd['category'])
            PortfolioProject.objects.create(
                title=pd['title'],
                category=cat,
                year=pd['year'],
                location=pd['location'],
                description=pd['description'],
                order=pd['order'],
                is_active=True,
            )
        self.stdout.write(f'  Seeded {len(projects)} portfolio projects (upload images via admin)')
