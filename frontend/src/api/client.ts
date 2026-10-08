// Toutes les requêtes vers le backend passent par ce fichier : une fonction par route.

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Source = {
  id: number
  name: string
  base_url: string
  is_active: boolean
  last_run_at: string | null
}

export type Offer = {
  id: number
  title: string
  company: string
  location: string
  url: string
  published_at: string | null
  first_seen_at: string
  source: Source
}

export type OfferPage = { items: Offer[]; total: number }

export type OfferFilters = { q?: string; city?: string; source?: string; page?: number; page_size?: number }

export type Stats = {
  offers_by_source: { source_id: number; source: string; count: number }[]
  new_offers_by_day: { date: string; count: number }[]
}

export type Subscription = { email: string; keywords: string; location: string }

// Erreur renvoyée par l'API, avec son code HTTP (404, 422, ...).
export class ApiError extends Error {
  status: number
  constructor(status: number) {
    super(`L'API a répondu avec le code ${status}`)
    this.status = status
  }
}

type Options = { method?: string; params?: Record<string, string | number | undefined>; body?: unknown }

async function request<T>(path: string, { method = 'GET', params = {}, body }: Options = {}): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params)) {
    if (value) url.searchParams.set(key, String(value)) // les filtres vides ne sont pas envoyés
  }
  const response = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) throw new ApiError(response.status)
  return response.json()
}

export const getOffers = (filters: OfferFilters = {}) => request<OfferPage>('/api/offers', { params: filters })
export const getSources = () => request<Source[]>('/api/sources')
export const getStats = () => request<Stats>('/api/stats')
export const subscribe = (subscription: Subscription) => request('/api/subscribers', { method: 'POST', body: subscription })
export const unsubscribe = (token: string) => request(`/api/subscribers/${encodeURIComponent(token)}`, { method: 'DELETE' })
