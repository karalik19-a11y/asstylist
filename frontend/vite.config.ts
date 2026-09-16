import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

/** Read env without requiring @types/node (tsc runs this file in the frontend project). */
function env(name: string): string {
  const g = globalThis as { process?: { env?: Record<string, string | undefined> } }
  return g.process?.env?.[name] ?? ''
}

function resolveBuildStamp(): string {
  const raw =
    env('VITE_BUILD_ID') ||
    env('SOURCE_VERSION') ||
    env('RENDER_GIT_COMMIT') ||
    env('GITHUB_SHA') ||
    env('COMMIT_REF') ||
    ''
  if (raw) return raw.slice(0, 12)
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
