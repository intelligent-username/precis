const parseCsv = (raw, fallback = []) => {
  if (!raw || !raw.trim()) return fallback
  return raw.split(',').map((part) => part.trim()).filter(Boolean)
}

const requiredEnv = (name) => {
  const value = import.meta.env[name]
  if (!value || !String(value).trim()) {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return String(value).trim()
}

export const API_BASE = requiredEnv('PRECIS_API_BASE_URL')
export const API_KEY = requiredEnv('PRECIS_API_KEY')

export const DEFAULT_MODEL = requiredEnv('PRECIS_DEFAULT_MODEL')
export const AVAILABLE_MODELS = parseCsv(
  import.meta.env.PRECIS_AVAILABLE_MODELS,
  [DEFAULT_MODEL],
)

export const authHeaders = (headers = {}) => (
  API_KEY ? { ...headers, 'X-API-Key': API_KEY } : headers
)
