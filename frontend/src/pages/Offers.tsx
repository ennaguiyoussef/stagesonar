import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getOffers, getSources, type OfferPage, type Source } from '../api/client.ts'
import { CITIES } from '../constants.ts'

const PAGE_SIZE = 18 // multiple de 2 et de 3 : la dernière ligne de la grille est toujours complète
const FIELD = 'w-full rounded-md border border-line bg-foam px-3 py-2'
const BUTTON = 'rounded-md bg-abyss px-4 py-2 text-center font-medium text-foam disabled:opacity-40'

const dateFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
const isRecent = (date: string) => Date.now() - new Date(date).getTime() < 24 * 60 * 60 * 1000

export default function Offers() {
  // Les filtres vivent dans l'adresse de la page (?q=...&city=...) : on peut la recharger ou la partager.
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const city = params.get('city') ?? ''
  const source = params.get('source') ?? ''
  const page = Number(params.get('page')) || 1

  const [sources, setSources] = useState<Source[]>([])
  const [data, setData] = useState<OfferPage | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    getSources().then(setSources).catch(() => setSources([]))
  }, [attempt])

  useEffect(() => {
    let outdated = false // évite qu'une réponse lente écrase une recherche plus récente
    getOffers({ q, city, source, page, page_size: PAGE_SIZE })
      .then((result) => {
        if (outdated) return
        setData(result)
        setError(false)
      })
      .catch(() => !outdated && setError(true))
    return () => {
      outdated = true
    }
  }, [q, city, source, page, attempt])

  function setFilter(name: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    if (name !== 'page') next.delete('page') // changer un filtre ramène à la première page
    setParams(next, { replace: true })
  }

  const pageCount = data ? Math.ceil(data.total / PAGE_SIZE) : 0

  return (
    <>
      <h1 className="font-display text-4xl font-bold">Offres de stage</h1>

      <form className="mt-6 grid gap-3 sm:grid-cols-[2fr_1fr_1fr]" onSubmit={(event) => event.preventDefault()}>
        <label className="text-sm font-medium">
          Recherche
          <input
            type="search"
            className={`${FIELD} mt-1 text-base font-normal`}
            placeholder="Titre ou entreprise"
            value={q}
            onChange={(event) => setFilter('q', event.target.value)}
          />
        </label>
        <label className="text-sm font-medium">
          Ville
          <select className={`${FIELD} mt-1 text-base font-normal`} value={city} onChange={(event) => setFilter('city', event.target.value)}>
            <option value="">Toutes les villes</option>
            {CITIES.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">
          Site
          <select className={`${FIELD} mt-1 text-base font-normal`} value={source} onChange={(event) => setFilter('source', event.target.value)}>
            <option value="">Tous les sites</option>
            {sources.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      </form>

      {error ? (
        <div className="mt-8 rounded-md border border-line bg-foam p-5" role="alert">
          <p className="font-medium">Le serveur de StageSonar ne répond pas.</p>
          <p className="mt-1 text-slate">Vérifiez que le backend est lancé, puis réessayez.</p>
          <button className={`${BUTTON} mt-4`} onClick={() => setAttempt(attempt + 1)}>
            Réessayer
          </button>
        </div>
      ) : !data ? (
        <p className="mt-8 text-slate">Chargement des offres…</p>
      ) : data.total === 0 ? (
        <div className="mt-8 rounded-md border border-line bg-foam p-5">
          {q || city || source ? (
            <>
              <p className="font-medium">Aucune offre ne correspond à ces filtres.</p>
              <button className={`${BUTTON} mt-4`} onClick={() => setParams({}, { replace: true })}>
                Effacer les filtres
              </button>
            </>
          ) : (
            <p className="font-medium">Aucune offre n'a encore été collectée.</p>
          )}
        </div>
      ) : (
        <>
          <p className="mt-8 text-slate" aria-live="polite">
            {data.total} offre{data.total > 1 ? 's' : ''}
          </p>
          {/* Grille de cartes : 1 colonne sur téléphone, 2 sur tablette, 3 sur grand écran. */}
          <ul className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((offer) => (
              <li key={offer.id} className="flex flex-col rounded-lg border border-line bg-foam p-5 shadow-sm hover:shadow-md">
                <p className="flex items-center justify-between gap-2 text-sm">
                  <span className="rounded-full bg-water px-2.5 py-0.5 font-medium">{offer.source.name}</span>
                  {isRecent(offer.first_seen_at) && (
                    <span className="rounded bg-beacon px-1.5 py-0.5 font-medium text-abyss">Nouvelle</span>
                  )}
                </p>
                <h2 className="mt-3 line-clamp-2 font-display text-lg leading-snug font-bold">{offer.title}</h2>
                <p className="mt-2 font-medium">{offer.company}</p>
                <p className="text-slate">{offer.location}</p>
                {/* mt-auto pousse la date et le bouton en bas : les boutons sont alignés d'une carte à l'autre. */}
                <p className="mt-auto pt-4 text-sm text-slate">Détectée le {dateFormat.format(new Date(offer.first_seen_at))}</p>
                <a href={offer.url} target="_blank" rel="noreferrer" className={`${BUTTON} mt-3`}>
                  Voir l'offre
                </a>
              </li>
            ))}
          </ul>

          {pageCount > 1 && (
            <nav className="mt-6 flex items-center justify-between gap-3" aria-label="Pagination">
              <button className={BUTTON} disabled={page <= 1} onClick={() => setFilter('page', String(page - 1))}>
                Précédent
              </button>
              <span className="text-slate">
                Page {page} sur {pageCount}
              </span>
              <button className={BUTTON} disabled={page >= pageCount} onClick={() => setFilter('page', String(page + 1))}>
                Suivant
              </button>
            </nav>
          )}
        </>
      )}
    </>
  )
}