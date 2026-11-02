"""Importe la sortie du pipeline Python (data/**) dans PostgreSQL. Idempotent : remplace tout."""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from qiraat.models import (Font, LayerData, MushafSura, Reader, ReaderGroup, Resource, Riwaya, Sura,
                           Word)

LAYERS = ['reads', 'usul', 'khilaf', 'badur']


def load(path: Path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Command(BaseCommand):
    help = 'Importe data/** (meta, qalun, reads, usul, khilaf, badur, riw) dans la base.'

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', default=str(settings.DATA_DIR))

    @transaction.atomic
    def handle(self, *args, data_dir, **opts):
        d = Path(data_dir)
        if not (d / 'meta.json').is_file():
            raise CommandError(f'{d}/meta.json introuvable (lancer build_app_data.py ?)')
        meta = load(d / 'meta.json')

        for model in (MushafSura, LayerData, Word, Riwaya, Reader, ReaderGroup, Font, Sura, Resource):
            model.objects.all().delete()

        Sura.objects.bulk_create(Sura(number=s['n'], name=s['name'], ayah_count=s['ayat'])
                                 for s in meta['suras'])

        for gi, g in enumerate(meta['groups']):
            ReaderGroup.objects.create(slug=g['id'], name=g['name'], order=gi)
            Reader.objects.bulk_create(Reader(slug=r['id'], name=r['name'], group_id=g['id'], order=ri)
                                       for ri, r in enumerate(g['readers']))
        Font.objects.bulk_create(Font(slug=f['id'], filename=f['font'], order=i)
                                 for i, f in enumerate(meta['fonts']))
        Riwaya.objects.bulk_create(
            Riwaya(slug=r['id'], name=r['name'], reader_id=r['reader'], font_file=r['font'],
                   basmala=r.get('bsm', ''), is_reference=bool(r.get('ref')),
                   mushaf=r.get('mush') or None, order=i)
            for i, r in enumerate(meta['riwayat']))
        Resource.objects.create(key='meta_stats', data=meta.get('stats', {}))
        Resource.objects.create(key='meta_fonts_src', data=meta.get('fonts_src', []))
        for key in ('rules', 'badur_unlocated'):
            if (d / f'{key}.json').is_file():
                Resource.objects.create(key=key, data=load(d / f'{key}.json'))

        for s in meta['suras']:
            n = s['n']
            q = load(d / 'qalun' / f'{n}.json')
            Word.objects.bulk_create(Word(sura_id=n, ayah=ay, seq=seq, text=text)
                                     for ay, words in q['ayat'] for seq, text in words)
            for layer in LAYERS:
                p = d / layer / f'{n}.json'
                if p.is_file():
                    LayerData.objects.create(layer=layer, sura_id=n, data=load(p))
            for r in meta['riwayat']:
                if r.get('mush'):
                    p = d / 'riw' / r['mush'] / f'{n}.json'
                    if p.is_file() and not MushafSura.objects.filter(mushaf=r['mush'], sura_id=n).exists():
                        MushafSura.objects.create(mushaf=r['mush'], sura_id=n, data=load(p))
            self.stdout.write(f'sourate {n}', ending='\r')
        self.stdout.write(self.style.SUCCESS(
            f'\nOK : {Word.objects.count()} mots, {LayerData.objects.count()} couches, '
            f'{MushafSura.objects.count()} mushafs.'))
