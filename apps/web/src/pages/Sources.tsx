import { arNum, caveatText, caveatTitle, sourceColor, sourceShort } from '@jamei/shared';
import { SourceStateBadge } from '../components/Badges';
import { useMeta } from '../lib/meta';

/** ورقةُ المصادر: حالُ كلِّ مصدرٍ ظاهرةٌ، ومعها حدودُ نسخته ونواقصُها وتبعيّتُه. */
export function Sources() {
  const { sources, suras } = useMeta();
  const suraName = (n: number | null) => (n == null ? '' : suras.find((s) => s.sura === n)?.name ?? arNum(n));
  return (
    <div className="page">
      <h1>المصادر</h1>
      <p className="muted lead-sm">
        حالُ كلِّ مصدرٍ محسوبٌ من أحكامه: «مقترَح» ما استُخرج ولم يُراجَع، و«مستورَد» ما نُقل من جدولٍ سابق، و«محقَّق» ما اعتمده
        مراجِع. وتنبيهاتُ كلِّ نسخةٍ منقولةٌ كما قُيِّدت.
      </p>
      <div className="src-cards">
        {sources.map((s) => (
          <article key={s.id} className="src-card" style={{ borderTopColor: sourceColor(s.id) }}>
            <header>
              <div>
                <h2>{s.name}</h2>
                <p className="muted">
                  {s.author ?? sourceShort(s.id)}
                  {s.died && <> · {s.died}</>}
                  {s.kind === 'mushaf' && <> · علاماتُ مصحف</>}
                </p>
              </div>
              <SourceStateBadge state={s.state} />
            </header>

            <dl className="counts">
              <div>
                <dt>المواضع</dt>
                <dd>{arNum(s.counts.total)}</dd>
              </div>
              <div>
                <dt>مقترَح</dt>
                <dd>{arNum(s.counts.proposed)}</dd>
              </div>
              <div>
                <dt>مستورَد</dt>
                <dd>{arNum(s.counts.imported)}</dd>
              </div>
              <div>
                <dt>محقَّق</dt>
                <dd>{arNum(s.counts.verified)}</dd>
              </div>
              <div>
                <dt>مقابلةٌ تقريبية</dt>
                <dd>{arNum(s.counts.approx)}</dd>
              </div>
              <div>
                <dt>للمراجعة</dt>
                <dd>{arNum(s.counts.review)}</dd>
              </div>
            </dl>

            <dl className="facts">
              {s.edition && (
                <>
                  <dt>النسخة المعتمدة</dt>
                  <dd>{s.edition}</dd>
                </>
              )}
              {(s.sura_lo != null || s.sura_hi != null) && (
                <>
                  <dt>حدودُ النسخة</dt>
                  <dd>
                    من {suraName(s.sura_lo ?? 1)} إلى {suraName(s.sura_hi ?? 114)} — وما وقع خارجها فليس حكماً للمؤلف.
                  </dd>
                </>
              )}
              {s.owner.length > 0 && (
                <>
                  <dt>ألفاظُ نسبة القول إليه</dt>
                  <dd>{s.owner.join('، ')}</dd>
                </>
              )}
              {s.owner_unattributed && (
                <>
                  <dt>العزو</dt>
                  <dd>يسوق حكمَه مجرَّداً ويعزو ما خالفه، فالمجرَّدُ من العزو قولُه.</dd>
                </>
              )}
              <dt>التحقُّق من البيانات</dt>
              <dd>{s.verified ? 'بياناتُ النسخة متحقَّقٌ منها' : 'بياناتُ النسخة لم يُتحقَّق منها بعد'}</dd>
            </dl>

            {Object.keys(s.caveats).length > 0 && (
              <div className="caveats">
                {Object.entries(s.caveats).map(([k, v]) => (
                  <div key={k} className="caveat">
                    <b>{caveatTitle(k)}</b>
                    <p>{caveatText(v)}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
