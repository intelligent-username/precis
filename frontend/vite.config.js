import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  envDir: '..',
  envPrefix: ['VITE_', 'PRECIS_', 'API_', 'DEFAULT_', 'AVAILABLE_'],
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Polling is needed for Docker bind mounts on Windows (virtiofs/gRPC-FUSE),
    // but 300ms is too aggressive and causes constant CPU + HMR thrash.
    // 1000ms is enough for dev; overridden via CHOKIDAR_INTERVAL env if needed.
    watch: {
      usePolling: Boolean(process.env.CHOKIDAR_USEPOLLING || process.env.DOCKER),
      interval: Number(process.env.CHOKIDAR_INTERVAL) || 1000,
      ignored: ['**/node_modules/**', '**/dist/**', '**/.git/**'],
    },
    // Proxy fixes "frontend stops after script fetching" streaming bug:
    // Vite's http-proxy buffers responses by default, which breaks NDJSON streaming.
    // We use `configure` to disable buffering and ensure chunked transfer passes through.
    proxy: (() => {
      const target = process.env.VITE_PROXY_TARGET || process.env.API_BASE_URL || process.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const streamingProxy = {
        target,
        changeOrigin: true,
        // Don't buffer streaming responses — critical for /summarize/* NDJSON
        selfHandleResponse: false,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            // Disable proxy buffering for streaming endpoints
            proxyReq.setHeader('X-Accel-Buffering', 'no')
            proxyReq.setHeader('Cache-Control', 'no-cache')
          })
        },
      }
      return {
        '/health': target,
        '/status': target,
        '/models': target,
        '/warmup': target,
        '/unload': target,
        // Streaming endpoints need special handling to avoid lag/buffering
        '/summarize': streamingProxy,
        '/docs': target,
        '/openapi.json': target,
      }
    })(),
  },
})
