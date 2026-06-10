import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject
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

    # Build projectData JSON matching the shape the existing JS expects
    project_data = []
    for p in projects:
        project_data.append({
            'title': p.title,
            'category': p.get_category_name(),
            'year': p.year,
            'location': p.location,
            'heroImg': p.hero_image.url if p.hero_image else '',
            'desc': p.description,
            'images': [
                {'url': img.image.url, 'size': img.size}
                for img in p.images.all()
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
        'nav_section_labels': {
            'proyectos': 'PROYECTOS —',
            'publicaciones': 'PUBLICACIONES —',
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
