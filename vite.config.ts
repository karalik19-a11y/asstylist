import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Хост превью ( *.e2b.app ) разрешён через allowedHosts, чтобы dev-сервер
// корректно отвечал в проксируемом iframe.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['.e2b.app', '.arena.ai', 'localhost', '127.0.0.1'],
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: ['.e2b.app', '.arena.ai', 'localhost', '127.0.0.1'],
  },
})
