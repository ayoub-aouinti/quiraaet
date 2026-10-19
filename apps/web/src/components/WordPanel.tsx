import { SILENCE_NOTE, arNum, sourceColor, sourceShort } from '@jamei/shared';
import { api } from '../lib/api';
import { useMeta } from '../lib/meta';
import { useAsync } from '../lib/useAsync';
import { RulingCard } from './RulingCard';

const ALIGN_LABEL: Record<string, string> = {
  exact: 'مطابِق',
  variant: 'بخُلفٍ في الرسم',
  unmatched: 'لم يُحاذَ',
};

/** تفصيلُ الموضع: كلُّ ما قالته المصادرُ بعد الكلمة، بلفظها وعللها. */
export function WordPanel({
  seq,
  hidden,
  onClose,
}: {
  seq: number;
  hidden: Set<string>;
  onClose: () => void;
}) {
  const meta = useMeta();
  const { data, error, loading } = useAsync(() => api.word(seq), [seq]);

  return (
    <aside className="panel" aria-label="تفصيل الموضع">
      <div className="panel-head">
        <div>
          <span className="muted small">الوقف بعد</span>
          <h2 className="panel-word">{data?.word.text ?? '…'}</h2>
          {data && (
            <span className="muted small">
              {data.word.sura_name} {arNum(data.word.sura)}:{arNum(data.word.ayah)}
              {data.word.wpos != null && <> · الكلمة {arNum(data.word.wpos)}</>}
            </span>
          )}
        </div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="إغلاق التفصيل">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>

      {loading && <p className="muted">يُحمَّل…</p>}
      {error && <p className="error">{error.message}</p>}

      {data && (
        <>
          {(() => {
            const shown = data.rulings.filter((r) => !hidden.has(r.source));
            const off = data.rulings.length - shown.length;
            return (
              <section className="panel-sec">
                <h3>
                  أقوالُ المصادر <span className="muted small">({arNum(shown.length)})</span>
                </h3>
                {off > 0 && <p className="muted small">وأُخفي {arNum(off)} من مصادر أطفأتَها.</p>}
                {shown.length === 0 && <p className="muted">لا حكمَ عند المصادر المختارة هنا.</p>}
                <div className="rulings">
                  {shown.map((r) => (
                    <RulingCard key={r.source} ruling={r} source={meta.sourceById[r.source]} categories={meta.categories} />
                  ))}
                </div>
              </section>
            );
          })()}

          {data.silent.length > 0 && (
            <section className="panel-sec">
              <h3>مصادرُ ساكتةٌ هنا</h3>
              <p className="muted small">{SILENCE_NOTE}</p>
              <ul className="silent">
                {data.silent.map((s) => (
                  <li key={s.source}>
                    <span className="dot" style={{ background: sourceColor(s.source) }} />
                    {sourceShort(s.source, meta.sourceById[s.source]?.name)}
                    {!s.in_range && <span className="muted small"> — الموضعُ خارجَ حدود نسخته المعتمدة</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {data.riwayat.length > 0 && (
            <section className="panel-sec">
              <h3>الموضعُ في الروايات</h3>
              <ul className="riw-list">
                {data.riwayat.map((r) => {
                  const name = meta.riwayat.find((x) => x.id === r.riwaya)?.name ?? r.riwaya;
                  return (
                    <li key={r.riwaya}>
                      <span className="riw-name">{name}</span>
                      <span className="quran riw-text">{r.words.map((w) => w.text).join(' ')}</span>
                      <span className="muted small">
                        {[...new Set(r.words.map((w) => ALIGN_LABEL[w.align ?? ''] ?? '—'))].join('، ')}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </section>
          )}
        </>
      )}
    </aside>
  );
}
