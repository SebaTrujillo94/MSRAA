import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, CurriculumItem, MediaItem,
    ContactSubmission, TeamMember,
)


def _tf(obj, field, is_en):
    """Return English field value when is_en=True, fallback to default field."""
    if is_en:
        en_val = getattr(obj, f'{field}_en', None)
        if en_val:
            return en_val
    return getattr(obj, field, '')


_NAV_LABELS = {
    'es': {
        'proyectos': 'PROYECTOS —',
        'publicaciones': 'PUBLICACIONES —',
        'curriculum': 'CURRICULUM —',
        'herramientas': 'HERRAMIENTAS —',
        'contacto': 'CONTACTO —',
    },
    'en': {
        'proyectos': 'PROJECTS —',
        'publicaciones': 'PUBLICATIONS —',
        'curriculum': 'CURRICULUM —',
        'herramientas': 'TOOLS —',
        'contacto': 'CONTACT —',
    },
}

_CV_LABELS = {
    'es': dict(CurriculumItem.CATEGORY_CHOICES),
    'en': {
        'formacion': 'EDUCATION',
        'experiencia': 'EXPERIENCE',
        'reconocimientos': 'AWARDS',
        'publicaciones': 'PUBLICATIONS',
        'otros': 'OTHER',
    },
}

_UI = {
    'es': {
        'portfolio_heading': 'PORTAFOLIO',
        'media_heading': 'PUBLICACIONES Y MEDIOS',
        'curriculum_heading': 'CURRICULUM',
        'tools_heading': 'HERRAMIENTAS',
        'contact_heading': 'CONTACTO',
        'contact_name': 'Nombre',
        'contact_phone': 'Teléfono',
        'contact_email': 'Correo',
        'contact_project_type': 'Tipo de proyecto',
        'contact_message': 'Mensaje',
        'contact_submit': 'Enviar mensaje',
        'contact_success': '¡Mensaje enviado! Te contactaremos pronto.',
        'contact_error': 'Error al enviar. Intenta de nuevo.',
        'filter_all': 'TODOS',
        'see_more': 'Ver más',
        'see_doc': 'Ver documento',
        'close': 'Cerrar',
        'calculadora_heading': 'CALCULADORA M²',
    },
    'en': {
        'portfolio_heading': 'PORTFOLIO',
        'media_heading': 'PUBLICATIONS & MEDIA',
        'curriculum_heading': 'CURRICULUM',
        'tools_heading': 'TOOLS',
        'contact_heading': 'CONTACT',
        'contact_name': 'Name',
        'contact_phone': 'Phone',
        'contact_email': 'Email',
        'contact_project_type': 'Project type',
        'contact_message': 'Message',
        'contact_submit': 'Send message',
        'contact_success': 'Message sent! We will contact you soon.',
        'contact_error': 'Failed to send. Please try again.',
        'filter_all': 'ALL',
        'see_more': 'See more',
        'see_doc': 'View document',
        'close': 'Close',
        'calculadora_heading': 'M² CALCULATOR',
    },
}


def index(request):
    lang = request.LANGUAGE_CODE or 'es'
    is_en = lang.startswith('en')
    lang_key = 'en' if is_en else 'es'

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
    media_items = list(MediaItem.objects.filter(is_active=True).prefetch_related('images', 'sections', 'videos'))
    media_data_json = json.dumps([{
        'tipo': m.get_tipo_display(),
        'year': m.year,
        'title': _tf(m, 'title', is_en),
        'description': _tf(m, 'description', is_en),
        'image': m.get_image_src(),
        'images': [i.get_image_src() for i in m.images.all() if i.get_image_src()],
        'url': m.url,
        'url_label': _tf(m, 'url_label', is_en) or _UI[lang_key]['see_more'],
        'videoUrl': m.get_video_embed_url(),
        'sections': [
            {'title': s.title, 'body': s.body}
            for s in m.sections.all()
        ],
        'videos': [
            {'url': v.get_video_url(), 'caption': v.caption}
            for v in m.videos.all()
        ],
    } for m in media_items], ensure_ascii=False)

    CURRICULUM_CATEGORY_ORDER = ['formacion', 'experiencia', 'reconocimientos', 'publicaciones']
    cv_labels = _CV_LABELS[lang_key]
    curriculum_items = CurriculumItem.objects.filter(is_active=True).prefetch_related('images')
    _cv_groups = {}
    for item in curriculum_items:
        _cv_groups.setdefault(item.category, []).append(item)
    curriculum_groups = [
        (cv_labels[cat], _cv_groups[cat])
        for cat in CURRICULUM_CATEGORY_ORDER
        if cat in _cv_groups
    ]
    curriculum_cv_item = _cv_groups.get('otros', [None])[0]

    team_members = list(TeamMember.objects.filter(is_active=True))

    nxt_projects = list(config.featured_next_projects.filter(is_active=True).order_by('order'))
    if not nxt_projects and projects:
        nxt_projects = [projects[-1]]
    project_index_by_id = {p.pk: i for i, p in enumerate(projects)}
    nxt_projects_data = [{
        'title': _tf(p, 'title', is_en),
        'heroImg': p.get_hero_image_src(),
        'videoUrl': p.get_video_embed_url(),
        'index': project_index_by_id.get(p.pk, -1),
    } for p in nxt_projects]
    nxt_projects_json = json.dumps(nxt_projects_data, ensure_ascii=False)

    project_data = []
    for p in projects:
        cat = p.category
        cat_name = (_tf(cat, 'name', is_en) if cat else '') or p.get_category_name()
        project_data.append({
            'title': _tf(p, 'title', is_en),
            'category': cat_name,
            'year': p.year,
            'location': _tf(p, 'location', is_en),
            'heroImg': p.get_hero_image_src(),
            'summary': _tf(p, 'summary', is_en) or p.get_summary(),
            'desc': _tf(p, 'description', is_en),
            'videoUrl': p.get_video_embed_url(),
            'images': [
                {'url': img.get_image_src()}
                for img in p.images.all() if img.get_image_src()
            ],
        })
    project_data_json = json.dumps(project_data, ensure_ascii=False)

    slides_data = []
    for v in hero_videos:
        slides_data.append({
            'vid': v.get_video_url(),
            'vidHd': v.get_video_url_hd(),
            't1': _tf(v, 'title_line1', is_en),
            't2': _tf(v, 'title_line2', is_en),
        })
    slides_json = json.dumps(slides_data, ensure_ascii=False)

    config_t = {
        'site_title': _tf(config, 'site_title', is_en),
        'about_label': _tf(config, 'about_label', is_en),
        'about_p1': _tf(config, 'about_p1', is_en),
        'about_p2': _tf(config, 'about_p2', is_en),
        'stat1_prefix': _tf(config, 'stat1_prefix', is_en),
        'stat1_label': _tf(config, 'stat1_label', is_en),
        'stat2_prefix': _tf(config, 'stat2_prefix', is_en),
        'stat2_label': _tf(config, 'stat2_label', is_en),
        'stat3_prefix': _tf(config, 'stat3_prefix', is_en),
        'stat3_label': _tf(config, 'stat3_label', is_en),
        'trust_lbl': _tf(config, 'trust_lbl', is_en),
        'trust_title': _tf(config, 'trust_title', is_en),
        'trust_sub': _tf(config, 'trust_sub', is_en),
        'footer_copy': _tf(config, 'footer_copy', is_en),
    }

    context = {
        'config': config,
        'config_t': config_t,
        'is_en': is_en,
        'lang': lang_key,
        'ui': _UI[lang_key],
        'hero_videos': hero_videos,
        'client_logos': client_logos,
        'categories': categories,
        'projects': projects,
        'project_data_json': project_data_json,
        'slides_json': slides_json,
        'hero_slide_duration': config.hero_slide_duration,
        'menu_items_by_section': _group_menu_items(menu_items),
        'curriculum_groups': curriculum_groups,
        'curriculum_cv_item': curriculum_cv_item,
        'nxt_projects_json': nxt_projects_json,
        'team_members': team_members,
        'media_items': media_items,
        'media_data_json': media_data_json,
        'nav_section_labels': _NAV_LABELS[lang_key],
        'is_en': is_en,
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
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        project_type = data.get('project_type', '').strip()
        message = data.get('message', '').strip()

        submission = ContactSubmission.objects.create(
            name=name,
            phone=phone,
            email=email,
            project_type=project_type,
            message=message,
        )

        config = SiteConfiguration.get_solo()
        try:
            send_mail(
                subject=f"Contacto MSRAA: {name}",
                message=(
                    f"Nombre: {name}\n"
                    f"Teléfono: {phone}\n"
                    f"Email: {email}\n"
                    f"Tipo de proyecto: {project_type}\n\n"
                    f"{message}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[config.contact_email],
            )
        except Exception:
            pass

        return JsonResponse({'status': 'ok', 'id': submission.pk})
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)
