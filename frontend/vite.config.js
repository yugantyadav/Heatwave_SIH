import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy /api to the FastAPI backend so the dev server and the API share an
    // origin. The target is overridable because it differs by environment:
    // http://localhost:8000 when running natively, http://web:8000 inside
    // docker compose (where "localhost" would be the frontend container).
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
