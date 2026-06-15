import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, CurriculumItem, MediaItem
)


def index(request):
    config = SiteConfiguration.get_solo()
    hero_videos = list(HeroVideo.objects.filter(is_active=True).order_by('order'))
    client_logos = list(ClientLogo.objects.filter(is_active=True).order_by('order'))
    categories = list(PortfolioCategory.objects.filter(is_active=True))
    projects = list(
        PortfolioProject.objects
        .filter(is_active=True)
        .select_related('category')
        .prefetch_related('images')
        .order_by('order')
    )
    menu_items = MenuItem.objects.filter(is_active=True)
    media_items = list(MediaItem.objects.filter(is_active=True).prefetch_related('images'))
    media_data_json = json.dumps([{
        'tipo': m.get_tipo_display(),
        'year': m.year,
        'title': m.title,
        'description': m.description,
        'image': m.get_image_src(),
        'images': [i.get_image_src() for i in m.images.all() if i.get_image_src()],
        'url': m.url,
        'url_label': m.url_label or 'Ver más',
        'videoUrl': m.get_video_embed_url(),
    } for m in media_items], ensure_ascii=False)
    CURRICULUM_CATEGORY_ORDER = ['formacion', 'experiencia', 'reconocimientos', 'publicaciones', 'otros']
    CURRICULUM_CATEGORY_LABELS = dict(CurriculumItem.CATEGORY_CHOICES)
    curriculum_items = CurriculumItem.objects.filter(is_active=True).prefetch_related('images')
    _cv_groups = {}
    for item in curriculum_items:
        _cv_groups.setdefault(item.category, []).append(item)
    curriculum_groups = [
        (CURRICULUM_CATEGORY_LABELS[cat], _cv_groups[cat])
        for cat in CURRICULUM_CATEGORY_ORDER
        if cat in _cv_groups
    ]

    # Build projectData JSON matching the shape the existing JS expects
    project_data = []
    for p in projects:
        project_data.append({
            'title': p.title,
            'category': p.get_category_name(),
            'year': p.year,
            'location': p.location,
            'heroImg': p.get_hero_image_src(),
            'desc': p.description,
            'videoUrl': p.get_video_embed_url(),
            'images': [
                {'url': img.get_image_src(), 'size': img.size}
                for img in p.images.all() if img.get_image_src()
            ],
        })
    project_data_json = json.dumps(project_data, ensure_ascii=False)

    # Build slides array matching the shape the existing JS expects
    slides_data = []
    for v in hero_videos:
        slides_data.append({
            'vid': v.get_video_url(),
            't1': v.title_line1,
            't2': v.title_line2,
        })
    slides_json = json.dumps(slides_data, ensure_ascii=False)

    context = {
        'config': config,
        'hero_videos': hero_videos,
        'client_logos': client_logos,
        'categories': categories,
        'projects': projects,
        'project_data_json': project_data_json,
        'slides_json': slides_json,
        'menu_items_by_section': _group_menu_items(menu_items),
        'curriculum_groups': curriculum_groups,
        'media_items': media_items,
        'media_data_json': media_data_json,
        'nav_section_labels': {
            'proyectos': 'PROYECTOS —',
            'publicaciones': 'PUBLICACIONES —',
            'curriculum': 'CURRICULUM —',
            'herramientas': 'HERRAMIENTAS —',
            'contacto': 'CONTACTO —',
        },
    }
    return render(request, 'index.html', context)


def _group_menu_items(menu_items):
    groups = {}
    for item in menu_items:
        groups.setdefault(item.section_group, []).append(item)
    return groups


@csrf_exempt
@require_POST
def contact_submit(request):
    try:
        data = json.loads(request.body)
        config = SiteConfiguration.get_solo()
        send_mail(
            subject=f"Contacto MSRAA: {data.get('name', '')}",
            message=(
                f"Nombre: {data.get('name', '')}\n"
                f"Teléfono: {data.get('phone', '')}\n"
                f"Email: {data.get('email', '')}\n"
                f"Tipo de proyecto: {data.get('project_type', '')}\n\n"
                f"{data.get('message', '')}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[config.contact_email],
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)
