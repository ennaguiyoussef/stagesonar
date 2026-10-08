import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSources, getStats, type Source, type Stats } from '../api/client.ts'

const dateFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
const plural = (count: number, word: string) => `${count} ${word}${count > 1 ? 's' : ''}`

export default function Home() {
  const [data, setData] = useState<{ sources: Source[]; stats: Stats } | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([getSources(), getStats()])
      .then(([sources, stats]) => setData({ sources, stats }))
      .catch(() => setError(true))
  }, [])

  const total = data?.stats.offers_by_source.reduce((sum, row) => sum + row.count, 0) ?? 0
  const thisWeek = data?.stats.new_offers_by_day.reduce((sum, row) => sum + row.count, 0) ?? 0
  const countOf = (source: Source) => data?.stats.offers_by_source.find((row) => row.source_id === source.id)?.count ?? 0

  return (
    <>
      <section className="grid items-center gap-8 md:grid-cols-[3fr_2fr]">
        <div>
          <h1 className="max-w-xl font-display text-4xl leading-tight font-bold sm:text-5xl">
            Les nouveaux stages, dès leur publication
          </h1>
          <p className="mt-4 max-w-xl text-lg text-slate">
            StageSonar surveille plusieurs sites de stages au Maroc, repère les offres qui viennent d'être publiées et
            envoie à chaque abonné celles qui correspondent à son profil.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/subscribe" className="rounded-md bg-abyss px-4 py-2 font-medium text-foam">
              S'abonner
            </Link>
            <Link to="/offers" className="rounded-md border border-abyss px-4 py-2 font-medium">
              Voir les offres
            </Link>
          </div>
        </div>
        <svg viewBox="0 0 200 200" className="mx-auto hidden w-full max-w-xs md:block lg:max-w-sm" aria-hidden="true">
          <g fill="none" stroke="var(--color-sonar)" opacity="0.45">
            <circle cx="100" cy="100" r="30" />
            <circle cx="100" cy="100" r="60" />
            <circle cx="100" cy="100" r="90" />
          </g>
          <path className="sonar-sweep" d="M100 100 L100 10 A90 90 0 0 1 163.6 36.4 Z" fill="var(--color-sonar)" opacity="0.25" />
          <g fill="var(--color-beacon)">
            <circle cx="150" cy="96" r="5" />
            <circle cx="74" cy="160" r="5" />
            <circle cx="62" cy="78" r="5" />
          </g>
        </svg>
      </section>

      {error && <p className="mt-12 text-slate">Les chiffres ne sont pas disponibles : le serveur de StageSonar ne répond pas.</p>}

      {data && (
        <section className="mt-12">
          <p className="font-display text-2xl font-bold">
            {plural(total, 'offre')} collectée{total > 1 ? 's' : ''} sur {plural(data.sources.length, 'site')}, dont {thisWeek} ces sept derniers jours.
          </p>
          {/* Une carte par site suivi. */}
          <ul className="mt-4 grid gap-4 sm:grid-cols-2">
            {data.sources.map((source) => (
              <li key={source.id} className="rounded-lg border border-line bg-foam p-5 shadow-sm">
                <a href={source.base_url} target="_blank" rel="noreferrer" className="font-medium underline">
                  {source.name}
                </a>
                <p className="mt-3 font-display text-4xl font-bold">{countOf(source)}</p>
                <p className="text-slate">offre{countOf(source) > 1 ? 's' : ''} collectée{countOf(source) > 1 ? 's' : ''}</p>
                <p className="mt-3 text-sm text-slate">
                  {source.last_run_at ? `Dernière collecte le ${dateFormat.format(new Date(source.last_run_at))}` : 'Pas encore collecté'}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}