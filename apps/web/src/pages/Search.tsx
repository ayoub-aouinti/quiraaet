import { Link, useSearchParams } from 'react-router-dom';
import { arNum } from '@jamei/shared';
import { api } from '../lib/api';
import { useAsync } from '../lib/useAsync';

export function Search() {
  const [sp, setSp] = useSearchParams();
  const q = sp.get('q') ?? '';
  const res = useAsync(() => (q.trim().length >= 2 ? api.search(q, 100) : Promise.resolve([])), [q]);
  return (
    <div className="page narrow">
      <h1>البحث في المصحف</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const v = new FormData(e.currentTarget).get('q');
          setSp({ q: String(v ?? '') });
        }}
      >
        <input className="filter" name="q" type="search" defaultValue={q} key={q} placeholder="كلمةٌ أو عبارة، بلا ضبط" aria-label="عبارة البحث" />
      </form>
      <p className="muted small">يُسقَط الضبطُ عند البحث، وتُوحَّد صورُ الألف. والعبارةُ تُطلَب كلماتٍ متتالية.</p>
      {res.loading && <p className="muted">يُبحَث…</p>}
      {res.error && <p className="error">{res.error.message}</p>}
      {res.data && q && (
        <>
          <p className="muted">{res.data.length ? `${arNum(res.data.length)} موضعاً${res.data.length === 100 ? ' (أوّلُ مئة)' : ''}` : 'لا نتائج.'}</p>
          <ul className="hits">
            {res.data.map((h) => (
              <li key={h.seq}>
                <Link to={`/read/${h.sura}?from=${h.ayah}&seq=${h.seq}`}>
                  <span className="quran">{h.text}</span>
                  <span className="muted small">
                    {h.sura_name} {arNum(h.sura)}:{arNum(h.ayah)}
                  </span>
                  <span className="small">{h.rulings_count ? `${arNum(h.rulings_count)} أحكام` : 'لا حكمَ مسجَّلاً'}</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
