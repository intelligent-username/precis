const optionalEnv = (names, fallback = '') => {
  const list = Array.isArray(names) ? names : [names]
  for (const name of list) {
    const value = import.meta.env[name]
    if (value && String(value).trim()) return String(value).trim()
  }
  return fallback
}

// In Docker/production the frontend is served from the same origin as the API
// (FastAPI StaticFiles at /), so empty string means "same origin" -> fetch("/models").
// In local dev, set VITE_API_BASE_URL=http://localhost:8000 in .env or rely on Vite proxy.
export const API_BASE = optionalEnv(
  ['API_BASE_URL', 'VITE_API_BASE_URL', 'PRECIS_API_BASE_URL'],
  '',
)

// API key is baked at `npm run build` time. For Docker, pass --build-arg PRECIS_API_KEY
// or VITE_API_KEY (docker-compose does this from .env). Falls back to empty so the
// production image can still build; backend will 401 until a real key is set.
export const API_KEY = optionalEnv(['PRECIS_API_KEY', 'VITE_API_KEY', 'VITE_PRECIS_API_KEY'], '')

export const authHeaders = (headers = {}) => (API_KEY ? { ...headers, 'X-API-Key': API_KEY } : headers)
