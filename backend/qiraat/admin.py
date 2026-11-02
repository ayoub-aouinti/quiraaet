from django.contrib import admin

from . import models

for m in (models.Sura, models.Reader, models.ReaderGroup, models.Riwaya, models.Font):
    admin.site.register(m)
