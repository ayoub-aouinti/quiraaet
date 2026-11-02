"""API en lecture seule. Les formes JSON reproduisent celles des anciens fichiers statiques."""
from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import Font, LayerData, MushafSura, ReaderGroup, Resource, Riwaya, Sura, Word

NO_STALE = cache_control(max_age=0, must_revalidate=True)


def strip_bk(entries):
    """`bk` (texte de la source « البدور ») est conservé en base mais jamais exposé (CLAUDE.md)."""
    return [{k: v for k, v in e.items() if k != 'bk'} for e in entries]


@require_GET
@NO_STALE
def meta(request):
    riwayat = []
    for r in Riwaya.objects.all():
        item = {'id': r.slug, 'name': r.name, 'font': r.font_file, 'ref': r.is_reference,
                'bsm': r.basmala, 'reader': r.reader_id}
        if not r.is_reference:   # le pipeline émet `mush: null` pour les riwayat sans mushaf, et rien pour qālūn
            item['mush'] = r.mushaf
        riwayat.append(item)
    groups = [{'id': g.slug, 'name': g.name,
               'readers': [{'id': r.slug, 'name': r.name} for r in g.readers.all()]}
              for g in ReaderGroup.objects.prefetch_related('readers')]
    stats = Resource.objects.filter(key='meta_stats').values_list('data', flat=True).first() or {}
    return JsonResponse({
        'suras': [{'n': s.number, 'name': s.name, 'ayat': s.ayah_count} for s in Sura.objects.all()],
        'riwayat': riwayat, 'groups': groups, 'stats': stats,
        'fonts': [{'id': f.slug, 'font': f.filename} for f in Font.objects.all()],
    })


@require_GET
@NO_STALE
def qalun(request, n):
    try:
        sura = Sura.objects.get(pk=n)
    except Sura.DoesNotExist:
        raise Http404
    ayat, cur = [], None
    for ayah, seq, text in Word.objects.filter(sura=sura).order_by('ayah', 'seq').values_list('ayah', 'seq', 'text'):
        if cur is None or cur[0] != ayah:
            cur = [ayah, []]
            ayat.append(cur)
        cur[1].append([seq, text])
    return JsonResponse({'n': sura.number, 'name': sura.name, 'ayat': ayat})


@require_GET
@NO_STALE
def reads(request, n):
    row = LayerData.objects.filter(layer=LayerData.READS, sura_id=n).first()
    if row is None:
        raise Http404
    return JsonResponse(strip_bk(row.data), safe=False)


@require_GET
@NO_STALE
def mushaf(request, mushaf, n):
    row = MushafSura.objects.filter(mushaf=mushaf, sura_id=n).first()
    if row is None:
        raise Http404
    return JsonResponse(row.data)


@require_GET
def font_file(request, name):
    path = (settings.FONTS_DIR / name).resolve()
    if path.parent != settings.FONTS_DIR.resolve() or not path.is_file():
        raise Http404
    resp = FileResponse(open(path, 'rb'))
    resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp


def spa(request):
    index = settings.FRONTEND_DIST / 'index.html'
    if not index.is_file():
        raise Http404('Frontend non compilé : cd frontend && npm run build')
    return FileResponse(open(index, 'rb'), content_type='text/html; charset=utf-8')
