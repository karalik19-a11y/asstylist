import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

function resolveBuildStamp(): string {
  const raw =
    process.env.VITE_BUILD_ID ||
    process.env.SOURCE_VERSION ||
    process.env.RENDER_GIT_COMMIT ||
    process.env.GITHUB_SHA ||
    process.env.COMMIT_REF ||
    ''
  if (raw) return raw.slice(0, 12)
  // local / unknown: date-time so each build is still recognizable
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `local-${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`
}

const buildStamp = resolveBuildStamp()

export default defineConfig({
  plugins: [react()],
  define: {
    __ASSTYLIST_BUILD__: JSON.stringify(buildStamp),
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 700,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    include: ['tests/**/*.test.{ts,tsx}'],
  },
})
