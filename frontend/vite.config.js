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
    // `npm run dev` on host -> localhost:5555, `docker compose up` frontend -> api:5555
    proxy: (() => {
      const target = process.env.VITE_PROXY_TARGET || (process.env.DOCKER ? 'http://api:5555' : 'http://localhost:5555')
      return {
        '/health': target,
        '/status': target,
        '/models': target,
        '/warmup': target,
        '/unload': target,
        '/summarize': target,
        '/docs': target,
        '/openapi.json': target,
      }
    })(),
  },
})
