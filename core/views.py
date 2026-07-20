import json
import requests
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    SiteConfiguration, MenuItem, HeroVideo,
    ClientLogo, PortfolioCategory, PortfolioProject, CurriculumItem, MediaItem,
    ContactSubmission, TeamMember, PortfolioDocument,
)

# Cap every proxied chunk well under Vercel's serverless response size limit (~4.5MB).
_PDF_PROXY_CHUNK = 3 * 1024 * 1024


def pdf_proxy(request, pk):
    """Stream a PortfolioDocument's PDF from its source URL via Range requests.

    Browsers can't fetch these Dropbox URLs directly (CORS fails on the
    redirect chain), so this proxies byte ranges through our own origin.

    A request with no Range header must get a real 200 with the true
    Content-Length (pdf.js reads it to detect Accept-Ranges support, then
    aborts the stream early) — responding 206 to an unranged request breaks
    that negotiation and pdf.js falls back to a full linear scan. Only
    actual Range requests are bounded to keep individual responses under
    Vercel's per-response size limit.
    """
    doc = get_object_or_404(PortfolioDocument, pk=pk, is_active=True)
    upstream_url = doc.get_pdf_src()

    range_header = request.META.get('HTTP_RANGE', '')
    upstream_headers = {}
    if range_header.startswith('bytes='):
        try:
            spec = range_header.split('=', 1)[1]
            raw_start, _, raw_end = spec.partition('-')
            if raw_start == '':
                # Suffix range "bytes=-N" — last N bytes. Clamp N, keep suffix form
                # so upstream computes the correct offset from the real file size.
                n = min(int(raw_end), _PDF_PROXY_CHUNK)
                upstream_headers['Range'] = f'bytes=-{n}'
            else:
                start = int(raw_start)
                end = int(raw_end) if raw_end else start + _PDF_PROXY_CHUNK - 1
                end = min(end, start + _PDF_PROXY_CHUNK - 1)
                upstream_headers['Range'] = f'bytes={start}-{end}'
        except (ValueError, IndexError):
            pass

    try:
        upstream = requests.get(upstream_url, headers=upstream_headers, stream=True, timeout=25)
    except requests.RequestException:
        return HttpResponse('No se pudo obtener el PDF.', status=502)

    if upstream.status_code not in (200, 206):
        return HttpResponse('No se pudo obtener el PDF.', status=502)

    is_ranged = 'Range' in upstream_headers
    response = StreamingHttpResponse(
        upstream.iter_content(chunk_size=65536),
        status=upstream.status_code,
        content_type='application/pdf',
    )
    content_range = upstream.headers.get('Content-Range')
    if content_range:
        response['Content-Range'] = content_range
    if 'Content-Length' in upstream.headers:
        response['Content-Length'] = upstream.headers['Content-Length']
    response['Accept-Ranges'] = 'bytes'
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'public, max-age=86400' if is_ranged else 'no-store'
    return response


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
        'portafolio': 'PORTAFOLIO —',
        'curriculum': 'CURRICULUM —',
        'herramientas': 'HERRAMIENTAS —',
        'contacto': 'CONTACTO —',
    },
    'en': {
        'proyectos': 'PROJECTS —',
        'publicaciones': 'PUBLICATIONS —',
        'portafolio': 'PORTFOLIO —',
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
        'nav_menu_btn': 'MENÚ',
        'nav_contact_btn': 'CONTACTO',

        'calc_eyebrow': 'MSRAA — Calculadora de superficies',
        'calc_title_html': '¿Cuántos m² necesita<br>tu <em>casa ideal?</em>',
        'calc_subtitle': '5 preguntas. Resultado preciso y personalizado.',

        'calc_q0': '¿Cuántas personas vivirán en la casa?',
        'calc_hint0': 'Define el número de dormitorios y baños necesarios.',
        'calc_opt_solo': 'Solo yo',
        'calc_opt_pareja': 'Pareja',
        'calc_opt_fam_peq': 'Familia pequeña',
        'calc_opt_fam_grande': 'Familia grande',

        'calc_q1': '¿Qué estilo de vida prefieres?',
        'calc_hint1': 'Influye en el tamaño de áreas comunes (living, comedor, cocina).',
        'calc_opt_minimalista': 'Minimalista',
        'calc_opt_equilibrado': 'Equilibrado',
        'calc_opt_espacioso': 'Espacioso',

        'calc_q2': '¿Necesitas espacios adicionales?',
        'calc_hint2': 'Puedes seleccionar más de uno.',
        'calc_opt_office': 'Oficina / estudio',
        'calc_opt_laundry': 'Lavandería',
        'calc_opt_gym': 'Gimnasio / sala de juegos',
        'calc_opt_none': 'Solo los básicos',

        'calc_q3': '¿Qué tipo de exteriores imaginas?',
        'calc_hint3': 'Se suma un porcentaje aproximado para obras exteriores.',
        'calc_opt_ext0': 'Sin exteriores',
        'calc_opt_ext1': 'Terraza o jardín',
        'calc_opt_ext2': 'Jardín + quincho',
        'calc_opt_ext3': 'Piscina + jardín',

        'calc_q4': '¿Cuál es tu presupuesto estimado por m²?',
        'calc_hint4': 'Incluye materialidad, acabados y complejidad estructural.',
        'calc_budget1_title': 'Estándar · hasta 30 UF/m²',
        'calc_budget1_sub': 'Construcción tradicional, terminaciones funcionales',
        'calc_budget2_title': 'Cómodo · 30 – 40 UF/m²',
        'calc_budget2_sub': 'Mejores aislaciones, ventanas termopanel, buen estándar',
        'calc_budget3_title': 'Premium · más de 40 UF/m²',
        'calc_budget3_sub': 'Diseño arquitectónico complejo, lujo en detalles y materialidad',

        'calc_next': 'Siguiente paso',
        'calc_back': 'Volver',
        'calc_see_result': 'Ver resultado',

        'calc_result_label': 'Tu casa ideal',
        'calc_result_unit': 'metros cuadrados construidos',
        'calc_min': 'Mínimo',
        'calc_recommended': 'Recomendado',
        'calc_max': 'Ampliado',
        'calc_m2': 'm²',
        'calc_m2_result': 'm² ← tu resultado',
        'calc_breakdown_title': 'Desglose por espacio',
        'calc_send_contact': 'Enviar esta estimación al contacto',
        'calc_restart': '↺ Calcular de nuevo',
        'calc_calculating': 'CALCULANDO ESTIMACIÓN...',

        'calc_dorms': 'Dormitorios',
        'calc_baths': 'Baños',
        'calc_living': 'Living / sala de estar',
        'calc_kitchen': 'Cocina',
        'calc_dining': 'Comedor',
        'calc_circulation': 'Circulación y muros (15%)',
        'calc_exterior_note': 'Exterior estimado (no computable): +{n} m² de terreno adicional',
        'calc_people_labels': ['', 'ti', '2 personas', 'familia de 3–4', 'familia de 5+'],
        'calc_people_labels_contact': ['', '1 persona', '2 personas', 'familia de 3–4 personas', 'familia de 5+ personas'],
        'calc_style_labels': ['', 'minimalista', 'equilibrado', 'amplio'],
        'calc_ext_labels': ['', 'terraza o jardín', 'jardín con quincho', 'piscina y jardín'],
        'calc_budget_labels_contact': ['', 'Estándar (hasta 30 UF/m²)', 'Cómodo (30–40 UF/m²)', 'Premium (más de 40 UF/m²)'],
        'calc_desc_template': 'Para {p}, estilo de vida {s}{ext}. Calculado con estándares arquitectónicos chilenos (15% circulación y muros).',
        'calc_desc_with_ext': ', con {ext}',
        'calc_none': 'Ninguno',
        'calc_wa_msg': (
            'Hola MSRAA,\n\nHe utilizado la calculadora de m² de su sitio web y me gustaría '
            'recibir una cotización formal basada en los siguientes datos estimados:\n\n'
        ),
        'calc_wa_size': '• Tamaño recomendado: {total} m² (rango: {min} m² - {max} m²)\n',
        'calc_wa_capacity': '• Capacidad: Para {p}\n',
        'calc_wa_style': '• Estilo de vida: {s}\n',
        'calc_wa_extras': '• Espacios adicionales: {extras}\n',
        'calc_wa_ext': '• Áreas exteriores: {ext}\n',
        'calc_wa_budget': '• Presupuesto estimado: {b}\n',
        'calc_wa_closing': '\nQuedo atento/a a sus comentarios para coordinar una reunión o recibir más información.',
        'calc_wa_type_field': 'Residencial - Diseño de Casa ({total} m²)',
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
        'nav_menu_btn': 'MENU',
        'nav_contact_btn': 'CONTACT',

        'calc_eyebrow': 'MSRAA — Floor Area Calculator',
        'calc_title_html': 'How many m² does<br>your <em>ideal home</em> need?',
        'calc_subtitle': '5 questions. A precise, personalized result.',

        'calc_q0': 'How many people will live in the house?',
        'calc_hint0': 'Determines the number of bedrooms and bathrooms needed.',
        'calc_opt_solo': 'Just me',
        'calc_opt_pareja': 'Couple',
        'calc_opt_fam_peq': 'Small family',
        'calc_opt_fam_grande': 'Large family',

        'calc_q1': 'What lifestyle do you prefer?',
        'calc_hint1': 'Affects the size of common areas (living room, dining room, kitchen).',
        'calc_opt_minimalista': 'Minimalist',
        'calc_opt_equilibrado': 'Balanced',
        'calc_opt_espacioso': 'Spacious',

        'calc_q2': 'Do you need additional spaces?',
        'calc_hint2': 'You can select more than one.',
        'calc_opt_office': 'Office / study',
        'calc_opt_laundry': 'Laundry room',
        'calc_opt_gym': 'Gym / game room',
        'calc_opt_none': 'Just the basics',

        'calc_q3': 'What kind of outdoor space do you imagine?',
        'calc_hint3': 'An approximate percentage is added for outdoor construction.',
        'calc_opt_ext0': 'No outdoor space',
        'calc_opt_ext1': 'Terrace or garden',
        'calc_opt_ext2': 'Garden + BBQ area',
        'calc_opt_ext3': 'Pool + garden',

        'calc_q4': "What's your estimated budget per m²?",
        'calc_hint4': 'Includes materials, finishes, and structural complexity.',
        'calc_budget1_title': 'Standard · up to 30 UF/m²',
        'calc_budget1_sub': 'Traditional construction, functional finishes',
        'calc_budget2_title': 'Comfortable · 30 – 40 UF/m²',
        'calc_budget2_sub': 'Better insulation, thermal windows, good standard',
        'calc_budget3_title': 'Premium · over 40 UF/m²',
        'calc_budget3_sub': 'Complex architectural design, luxury details and materials',

        'calc_next': 'Next step',
        'calc_back': 'Back',
        'calc_see_result': 'See result',

        'calc_result_label': 'Your ideal home',
        'calc_result_unit': 'square meters built',
        'calc_min': 'Minimum',
        'calc_recommended': 'Recommended',
        'calc_max': 'Extended',
        'calc_m2': 'm²',
        'calc_m2_result': 'm² ← your result',
        'calc_breakdown_title': 'Breakdown by space',
        'calc_send_contact': 'Send this estimate to contact',
        'calc_restart': '↺ Calculate again',
        'calc_calculating': 'CALCULATING ESTIMATE...',

        'calc_dorms': 'Bedrooms',
        'calc_baths': 'Bathrooms',
        'calc_living': 'Living room',
        'calc_kitchen': 'Kitchen',
        'calc_dining': 'Dining room',
        'calc_circulation': 'Circulation & walls (15%)',
        'calc_exterior_note': 'Estimated exterior (not included): +{n} m² additional land',
        'calc_people_labels': ['', 'you', '2 people', 'family of 3–4', 'family of 5+'],
        'calc_people_labels_contact': ['', '1 person', '2 people', 'family of 3–4', 'family of 5+'],
        'calc_style_labels': ['', 'minimalist', 'balanced', 'spacious'],
        'calc_ext_labels': ['', 'terrace or garden', 'garden with BBQ area', 'pool and garden'],
        'calc_budget_labels_contact': ['', 'Standard (up to 30 UF/m²)', 'Comfortable (30–40 UF/m²)', 'Premium (over 40 UF/m²)'],
        'calc_desc_template': 'For {p}, {s} lifestyle{ext}. Calculated using Chilean architectural standards (15% circulation and walls).',
        'calc_desc_with_ext': ', with {ext}',
        'calc_none': 'None',
        'calc_wa_msg': (
            'Hello MSRAA,\n\nI used the m² calculator on your website and would like to '
            'receive a formal quote based on the following estimated data:\n\n'
        ),
        'calc_wa_size': '• Recommended size: {total} m² (range: {min} m² - {max} m²)\n',
        'calc_wa_capacity': '• Capacity: For {p}\n',
        'calc_wa_style': '• Lifestyle: {s}\n',
        'calc_wa_extras': '• Additional spaces: {extras}\n',
        'calc_wa_ext': '• Outdoor areas: {ext}\n',
        'calc_wa_budget': '• Estimated budget: {b}\n',
        'calc_wa_closing': "\nI'll be looking forward to your reply to schedule a meeting or receive more information.",
        'calc_wa_type_field': 'Residential - House Design ({total} m²)',
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
    team_data_json = json.dumps([{
        'name': t.name,
        'role': _tf(t, 'role', is_en),
        'bio': _tf(t, 'bio', is_en),
        'photo': t.get_image_src(),
        'cvUrl': t.cv_url,
    } for t in team_members], ensure_ascii=False)

    portfolio_documents = list(PortfolioDocument.objects.filter(is_active=True))
    portfolio_documents_json = json.dumps([{
        'title': _tf(d, 'title', is_en),
        'description': _tf(d, 'description', is_en),
        'cover': d.get_cover_src(),
        'pdfUrl': f'/pdf-proxy/{d.pk}/',
        'pdfSize': d.pdf_size,
    } for d in portfolio_documents], ensure_ascii=False)

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

    parallax_projects = list(config.parallax_projects.filter(is_active=True).order_by('order'))
    parallax_projects_json = json.dumps([{
        'heroImg': p.get_hero_image_src(),
        'videoUrl': p.get_video_embed_url(),
    } for p in parallax_projects], ensure_ascii=False)

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
        'ui_json': json.dumps(_UI[lang_key], ensure_ascii=False),
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
        'parallax_projects_json': parallax_projects_json,
        'team_members': team_members,
        'team_data_json': team_data_json,
        'portfolio_documents': portfolio_documents,
        'portfolio_documents_json': portfolio_documents_json,
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
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)

    # Submission is already saved at this point — email delivery is best-effort
    # and must never turn into a false "failed to send" for the visitor.
    try:
        config = SiteConfiguration.get_solo()
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
