from django.contrib import admin
from django.urls import include, path, re_path

from qiraat.views import font_file, spa

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('qiraat.urls')),
    path('fonts/<str:name>', font_file),
    # tout le reste -> SPA React (routage côté client)
    re_path(r'^(?!api/|admin/|static/|fonts/).*$', spa),
]
