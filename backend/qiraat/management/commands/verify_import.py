"""Compare, sourate par sourate, les réponses de l'API aux fichiers JSON d'origine (parité exacte)."""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from qiraat.models import LayerData
from qiraat.views import strip_bk


def load(path: Path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Command(BaseCommand):
    help = "Vérifie que l'API restitue fidèlement data/** (reads sans `bk`)."

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', default=str(settings.DATA_DIR))

    def handle(self, *args, data_dir, **opts):
        d = Path(data_dir)
        c = Client(HTTP_HOST='localhost')
        bad = []

        def check(label, got, want):
            if got != want:
                bad.append(label)

        meta = load(d / 'meta.json')
        meta.pop('fonts_src', None)
        check('meta', c.get('/api/meta/').json(), meta)
        for s in meta['suras']:
            n = s['n']
            check(f'qalun/{n}', c.get(f'/api/suras/{n}/qalun/').json(), load(d / 'qalun' / f'{n}.json'))
            check(f'reads/{n}', c.get(f'/api/suras/{n}/reads/').json(), strip_bk(load(d / 'reads' / f'{n}.json')))
            for layer in ('usul', 'khilaf', 'badur'):  # non exposées : on compare la base
                row = LayerData.objects.get(layer=layer, sura_id=n)
                check(f'{layer}/{n}', row.data, load(d / layer / f'{n}.json'))
            for r in meta['riwayat']:
                if r.get('mush'):
                    check(f'riw/{r["mush"]}/{n}', c.get(f'/api/mushafs/{r["mush"]}/{n}/').json(),
                          load(d / 'riw' / r['mush'] / f'{n}.json'))
        if bad:
            raise CommandError(f'{len(bad)} divergences : {bad[:10]}')
        self.stdout.write(self.style.SUCCESS('Parité exacte : tous les JSON sont restitués.'))
