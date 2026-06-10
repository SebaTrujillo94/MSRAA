from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
