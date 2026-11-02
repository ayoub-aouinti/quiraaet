import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// En dev : Django (python manage.py runserver 8000) sert l'API, les polices et l'admin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000', '/fonts': 'http://127.0.0.1:8000' },
  },
});
