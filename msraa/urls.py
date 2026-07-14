from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.urls import reverse
from django.shortcuts import redirect

def _mantenedor_redirect(request):
    return redirect('/admin/core/siteconfiguration/mantenedor/')

urlpatterns = [
    path('admin/mantenedor/', admin.site.admin_view(_mantenedor_redirect), name='mantenedor_shortcut'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', views.index, name='index'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('pdf-proxy/<int:pk>/', views.pdf_proxy, name='pdf_proxy'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
