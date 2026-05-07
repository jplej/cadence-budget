from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", api.urls),
    path("", include("apps.tenants.urls")),
    path("", include("apps.users.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.budget.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
