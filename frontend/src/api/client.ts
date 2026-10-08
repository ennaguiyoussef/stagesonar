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

async function get<T>(path: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params)) {
    if (value) url.searchParams.set(key, String(value)) // les filtres vides ne sont pas envoyés
  }
  const response = await fetch(url)
  if (!response.ok) throw new Error(`L'API a répondu avec le code ${response.status}`)
  return response.json()
}

export const getOffers = (filters: OfferFilters = {}) => get<OfferPage>('/api/offers', filters)
export const getSources = () => get<Source[]>('/api/sources')
export const getStats = () => get<Stats>('/api/stats')
