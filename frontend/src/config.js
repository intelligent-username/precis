const requiredEnv = (names) => {
  const list = Array.isArray(names) ? names : [names]
  for (const name of list) {
    const value = import.meta.env[name]
    if (value && String(value).trim()) return String(value).trim()
  }
  throw new Error(`Missing required environment variable. Tried: ${list.join(', ')}`)
}

export const API_BASE = requiredEnv([
  'API_BASE_URL',
  'VITE_API_BASE_URL',
  'PRECIS_API_BASE_URL',
])
export const API_KEY = requiredEnv([
  'PRECIS_API_KEY',
  'VITE_API_KEY',
])

export const authHeaders = (headers = {}) => (
  API_KEY ? { ...headers, 'X-API-Key': API_KEY } : headers
)
