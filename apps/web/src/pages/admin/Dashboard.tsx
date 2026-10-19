import { Link } from 'react-router-dom';
import { arNum, sourceColor, sourceShort } from '@jamei/shared';
import { SourceStateBadge } from '../../components/Badges';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useAsync } from '../../lib/useAsync';

export function Dashboard() {
  const { sources } = useMeta();
  const stats = useAsync(() => api.stats(), []);
  const s = stats.data;
  return (
    <div>
      <h1>اللوحة</h1>
      <p className="muted">حالةُ الجامع اليوم.</p>
      {stats.error && <p className="error">{stats.error.message}</p>}
      {s && (
        <>
          <dl className="kpis">
            <div>
              <dt>كلمات المصحف</dt>
              <dd>{arNum(s.words)}</dd>
            </div>
            <div>
              <dt>كلماتٌ عليها حكم</dt>
              <dd>{arNum(s.words_with_rulings)}</dd>
            </div>
            <div>
              <dt>الأحكام</dt>
              <dd>{arNum(s.rulings)}</dd>
            </div>
            <div>
              <dt>مقترَح</dt>
              <dd>{arNum(s.by_status.proposed)}</dd>
            </div>
            <div>
              <dt>مستورَد</dt>
              <dd>{arNum(s.by_status.imported)}</dd>
            </div>
            <div>
              <dt>محقَّق</dt>
              <dd>{arNum(s.by_status.verified)}</dd>
            </div>
          </dl>

          <h2>ما يحتاج قراراً</h2>
          <ul className="todo">
            <li>
              <span>
                <b>{arNum(s.pending_review)}</b> حكماً مقترَحاً لم يُقضَ فيه
              </span>
              <Link className="btn small" to="/admin/review">
                راجِع
              </Link>
            </li>
            <li>
              <span>
                <b>{arNum(s.terms.total - s.terms.reviewed)}</b> مصطلحاً من {arNum(s.terms.total)} بلا مقابلةٍ مراجَعة
              </span>
              <Link className="btn small" to="/admin/terms">
                اضبط
              </Link>
            </li>
            <li>
              <span>
                <b>{arNum(s.unknown_symbol)}</b> موضعاً لم يُفهَم رمزُه، محفوظةٌ معلَّمةٌ ولم تُخمَّن
              </span>
            </li>
            <li>
              <span>
                <b>{arNum(s.review_flags)}</b> حكماً عليه تعليمُ مراجعة
              </span>
            </li>
          </ul>
        </>
      )}

      <h2>المصادر</h2>
      <table className="table">
        <thead>
          <tr>
            <th>المصدر</th>
            <th>المواضع</th>
            <th>مقترَح</th>
            <th>محقَّق</th>
            <th>تقريبية</th>
            <th>الحال</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((x) => (
            <tr key={x.id}>
              <td>
                <span className="dot" style={{ background: sourceColor(x.id) }} /> {sourceShort(x.id, x.name)}
              </td>
              <td>{arNum(x.counts.total)}</td>
              <td>{arNum(x.counts.proposed)}</td>
              <td>{arNum(x.counts.verified)}</td>
              <td>{arNum(x.counts.approx)}</td>
              <td>
                <SourceStateBadge state={x.state} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
