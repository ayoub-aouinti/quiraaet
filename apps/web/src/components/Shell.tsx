import { useState, type FormEvent, type ReactNode } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { LogoMark } from './Logo';

export function Shell({ children }: { children: ReactNode }) {
  const nav = useNavigate();
  const [q, setQ] = useState('');
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (q.trim()) nav(`/search?q=${encodeURIComponent(q.trim())}`);
  };
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <LogoMark size={24} />
          <span>جامع الوقوف</span>
        </Link>
        <nav className="topnav" aria-label="الأقسام">
          <NavLink to="/read/1">المصحف</NavLink>
          <NavLink to="/suras">السور</NavLink>
          <NavLink to="/sources">المصادر</NavLink>
          <NavLink to="/admin">المراجعة</NavLink>
        </nav>
        <form className="topsearch" role="search" onSubmit={submit}>
          <label htmlFor="q" className="sr-only">
            ابحث في المصحف
          </label>
          <input id="q" type="search" placeholder="ابحث في المصحف" value={q} onChange={(e) => setQ(e.target.value)} />
        </form>
      </header>
      <div className="shell-body">{children}</div>
    </div>
  );
}
