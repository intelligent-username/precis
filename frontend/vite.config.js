import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  envDir: '..',
  envPrefix: ['VITE_', 'PRECIS_', 'API_', 'DEFAULT_', 'AVAILABLE_'],
  plugins: [react()],
})
