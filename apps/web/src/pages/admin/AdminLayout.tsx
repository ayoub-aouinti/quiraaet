import { useState, type FormEvent } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { api, reviewerToken } from '../../lib/api';

/** القراءةُ مفتوحة، والكتابةُ برمز مراجِعٍ يُحفَظ في الجلسة وحدها. */
export function AdminLayout() {
  const [token, setToken] = useState(reviewerToken.get());
  const [actor, setActor] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [err, setErr] = useState<string | null>(null);

  const signIn = async (e: FormEvent) => {
    e.preventDefault();
    setErr(null);
    reviewerToken.set(draft.trim());
    try {
      const r = await api.checkToken();
      setToken(draft.trim());
      setActor(r.actor ?? null);
      setDraft('');
    } catch (x) {
      reviewerToken.set(null);
      setToken(null);
      setErr(x instanceof Error ? x.message : String(x));
    }
  };
  const signOut = () => {
    reviewerToken.set(null);
    setToken(null);
    setActor(null);
  };

  return (
    <div className="admin">
      <aside className="admin-nav">
        <nav aria-label="المراجعة">
          <NavLink end to="/admin">
            اللوحة
          </NavLink>
          <NavLink to="/admin/review">طابورُ المراجعة</NavLink>
          <NavLink to="/admin/terms">المصطلحات</NavLink>
        </nav>
        <div className="signin">
          {token ? (
            <>
              <p className="small">
                أنت مراجِع{actor ? <> باسم «{actor}»</> : null}. تُقيَّد قراراتُك في سجلّ المراجعة.
              </p>
              <button type="button" className="btn small" onClick={signOut}>
                خروج
              </button>
            </>
          ) : (
            <form onSubmit={signIn}>
              <label htmlFor="tok" className="small">
                رمزُ المراجِع
              </label>
              <input id="tok" type="password" value={draft} onChange={(e) => setDraft(e.target.value)} autoComplete="off" />
              <button type="submit" className="btn small primary" disabled={!draft.trim()}>
                دخول
              </button>
              {err && <p className="error small">{err}</p>}
              <p className="muted small">بلا رمزٍ تُعرَض المراجعةُ للاطّلاع، ولا يُعتمَد فيها شيء.</p>
            </form>
          )}
        </div>
      </aside>
      <div className="admin-main">
        <Outlet context={{ canWrite: !!token }} />
      </div>
    </div>
  );
}

export interface AdminCtx {
  canWrite: boolean;
}
