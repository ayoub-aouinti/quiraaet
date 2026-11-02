"""Schéma hybride : tables pour le texte de qālūn et les métadonnées,
JSONB pour les couches de divergence (format identique à la sortie du pipeline)."""
from django.db import models


class Sura(models.Model):
    number = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=60)
    ayah_count = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['number']


class Word(models.Model):
    """Mot de qālūn ; `seq` est la position dans la sourate (clé des couches de divergence)."""
    sura = models.ForeignKey(Sura, on_delete=models.CASCADE, related_name='words')
    ayah = models.PositiveSmallIntegerField()
    seq = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ['sura_id', 'seq']
        constraints = [models.UniqueConstraint(fields=['sura', 'seq'], name='uniq_word_seq')]
        indexes = [models.Index(fields=['sura', 'ayah'])]


class ReaderGroup(models.Model):
    slug = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=60)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']


class Reader(models.Model):
    slug = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=60)
    group = models.ForeignKey(ReaderGroup, on_delete=models.CASCADE, related_name='readers')
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['group__order', 'order']


class Font(models.Model):
    slug = models.CharField(max_length=40, primary_key=True)
    filename = models.CharField(max_length=80)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']


class Riwaya(models.Model):
    slug = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=80)
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, related_name='riwayat')
    font_file = models.CharField(max_length=80)
    basmala = models.TextField(blank=True)
    is_reference = models.BooleanField(default=False)
    mushaf = models.CharField(max_length=40, null=True, blank=True)  # clé du mushaf ; null = pas de mushaf
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']


class LayerData(models.Model):
    """Une couche de divergence pour une sourate : reads | usul | khilaf | badur."""
    READS, USUL, KHILAF, BADUR = 'reads', 'usul', 'khilaf', 'badur'
    LAYERS = [(READS, 'reads'), (USUL, 'usul'), (KHILAF, 'khilaf'), (BADUR, 'badur')]

    layer = models.CharField(max_length=10, choices=LAYERS)
    sura = models.ForeignKey(Sura, on_delete=models.CASCADE, related_name='layers')
    data = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['layer', 'sura'], name='uniq_layer_sura')]


class MushafSura(models.Model):
    """Texte d'une riwāya (mushaf du Complexe) pour une sourate, comparé mot à mot à qālūn."""
    mushaf = models.CharField(max_length=40)
    sura = models.ForeignKey(Sura, on_delete=models.CASCADE, related_name='mushafs')
    data = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['mushaf', 'sura'], name='uniq_mushaf_sura')]


class Resource(models.Model):
    """Documents globaux : meta_stats, rules, badur_unlocated (conservés, jamais supprimés)."""
    key = models.CharField(max_length=40, primary_key=True)
    data = models.JSONField()
