import { useState } from 'react';
import { Link } from 'react-router-dom';
import { arNum, normalizeArabic } from '@jamei/shared';
import { useMeta } from '../lib/meta';

export function Suras() {
  const { suras } = useMeta();
  const [q, setQ] = useState('');
  const nq = normalizeArabic(q);
  const list = nq ? suras.filter((s) => normalizeArabic(s.name).includes(nq) || String(s.sura) === q.trim()) : suras;
  return (
    <div className="page narrow">
      <h1>السور</h1>
      <input className="filter" type="search" placeholder="اسمُ السورة أو رقمُها" value={q} onChange={(e) => setQ(e.target.value)} aria-label="تصفية السور" />
      <ul className="sura-grid">
        {list.map((s) => (
          <li key={s.sura}>
            <Link to={`/read/${s.sura}`}>
              <span className="sura-no">{arNum(s.sura)}</span>
              <span className="sura-name">{s.name}</span>
              <span className="muted small">{arNum(s.ayat)} آية</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
