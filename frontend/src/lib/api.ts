import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

const BASE_URL = (import.meta.env.VITE_API_URL as string) || ''

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('clipforge.token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err?.response?.status === 401) {
      // Don't redirect from /login itself
      if (!window.location.pathname.startsWith('/login')) {
        localStorage.removeItem('clipforge.token')
        localStorage.removeItem('clipforge.user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const r = await api.get<T>(url, config)
  return r.data
}

export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const r = await api.post<T>(url, data, config)
  return r.data
}

export async function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const r = await api.patch<T>(url, data, config)
  return r.data
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const r = await api.delete<T>(url, config)
  return r.data
}

/**
 * Suit un job asynchrone jusqu'à son état final.
 *
 * Les traitements lourds (analyse, rendu) tournent dans le worker : la requête
 * HTTP rend la main tout de suite avec un job, et c'est ici qu'on attend. Évite
 * les requêtes qui restent ouvertes plusieurs minutes et expirent en silence.
 */
export async function waitForJob(
  jobId: string,
  opts: { intervalMs?: number; timeoutMs?: number; onTick?: (job: import('@/types').Job) => void } = {}
): Promise<import('@/types').Job> {
  const interval = opts.intervalMs ?? 2000
  const timeout = opts.timeoutMs ?? 60 * 60 * 1000
  const startedAt = Date.now()

  for (;;) {
    const job = await get<import('@/types').Job>(`/api/v1/jobs/${jobId}`)
    opts.onTick?.(job)
    if (job.status === 'completed') return job
    if (job.status === 'failed' || job.status === 'cancelled') {
      throw new Error(job.error || job.message || 'Job failed')
    }
    if (Date.now() - startedAt > timeout) {
      throw new Error('Job still running after the maximum wait time')
    }
    await new Promise((r) => setTimeout(r, interval))
  }
}
