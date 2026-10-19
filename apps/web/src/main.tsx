import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { MetaProvider } from './lib/meta';
import { AdminLayout } from './pages/admin/AdminLayout';
import { Dashboard } from './pages/admin/Dashboard';
import { Review } from './pages/admin/Review';
import { Terms } from './pages/admin/Terms';
import { Landing } from './pages/Landing';
import { Reader } from './pages/Reader';
import { Search } from './pages/Search';
import { Sources } from './pages/Sources';
import { Suras } from './pages/Suras';
import './styles.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <MetaProvider>
        <Shell>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/suras" element={<Suras />} />
            <Route path="/read" element={<Navigate to="/read/1" replace />} />
            <Route path="/read/:sura" element={<Reader />} />
            <Route path="/sources" element={<Sources />} />
            <Route path="/search" element={<Search />} />
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="review" element={<Review />} />
              <Route path="terms" element={<Terms />} />
            </Route>
            <Route path="*" element={<div className="page narrow"><h1>لا صفحةَ هنا</h1></div>} />
          </Routes>
        </Shell>
      </MetaProvider>
    </BrowserRouter>
  </StrictMode>,
);
