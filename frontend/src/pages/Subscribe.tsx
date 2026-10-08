import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { subscribe } from '../api/client.ts'
import { CITIES, DOMAINS } from '../constants.ts'

const FIELD = 'mt-1 w-full rounded-md border border-line bg-foam px-3 py-2 text-base font-normal'

export default function Subscribe() {
  const [email, setEmail] = useState('')
  const [selected, setSelected] = useState<string[]>([]) // noms des domaines cochés
  const [extra, setExtra] = useState('')
  const [city, setCity] = useState('')
  const [status, setStatus] = useState<'editing' | 'sending' | 'done'>('editing')
  const [error, setError] = useState('')

  function toggle(label: string) {
    setSelected(selected.includes(label) ? selected.filter((item) => item !== label) : [...selected, label])
    setError('')
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    // Les domaines cochés et les mots-clés libres deviennent une seule chaîne, séparée par des virgules.
    const keywords = [...DOMAINS.filter((domain) => selected.includes(domain.label)).map((domain) => domain.keywords), extra.trim()]
      .filter(Boolean)
      .join(', ')
    if (!keywords) return setError('Choisissez au moins un domaine ou saisissez un mot-clé.')
    setStatus('sending')
    try {
      await subscribe({ email, keywords, location: city })
      setStatus('done')
    } catch {
      setError("L'abonnement n'a pas pu être enregistré. Vérifiez votre adresse, puis réessayez.")
      setStatus('editing')
    }
  }

  if (status === 'done') {
    return (
      <>
        <h1 className="font-display text-4xl font-bold">Vous êtes abonné</h1>
        <p className="mt-4 max-w-xl text-lg text-slate">
          Dès qu'une nouvelle offre correspondant à vos critères sera publiée, vous la recevrez à l'adresse {email}. Si
          cette adresse était déjà abonnée, ses critères ont été remplacés.
        </p>
        <Link to="/offers" className="mt-6 inline-block rounded-md bg-abyss px-4 py-2 font-medium text-foam">
          Voir les offres
        </Link>
      </>
    )
  }

  return (
    <>
      <h1 className="font-display text-4xl font-bold">S'abonner</h1>
      <p className="mt-3 max-w-xl text-lg text-slate">
        Recevez par e-mail les nouvelles offres de stage qui correspondent à votre profil, dès leur publication.
      </p>

      <form className="mt-8 max-w-2xl space-y-7" onSubmit={submit}>
        <fieldset>
          <legend className="text-sm font-medium">Domaines qui vous intéressent</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {DOMAINS.map((domain) => (
              <label
                key={domain.label}
                className="cursor-pointer rounded-full border border-line bg-foam px-4 py-2 has-checked:border-abyss has-checked:bg-abyss has-checked:text-foam has-focus-visible:outline-3 has-focus-visible:outline-offset-2 has-focus-visible:outline-beacon"
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={selected.includes(domain.label)}
                  onChange={() => toggle(domain.label)}
                />
                {domain.label}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="block text-sm font-medium">
          Autres mots-clés (facultatif)
          <input className={FIELD} placeholder="Par exemple : cybersécurité, design, tourisme" value={extra} onChange={(event) => setExtra(event.target.value)} />
        </label>

        <div className="grid gap-5 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            Ville
            <select className={FIELD} value={city} onChange={(event) => setCity(event.target.value)}>
              <option value="">Toutes les villes</option>
              {CITIES.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            Adresse e-mail
            <input type="email" required className={FIELD} placeholder="vous@exemple.ma" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
        </div>

        {error && (
          <p className="font-medium text-red-700" role="alert">
            {error}
          </p>
        )}

        <button className="rounded-md bg-abyss px-5 py-2.5 font-medium text-foam disabled:opacity-40" disabled={status === 'sending'}>
          S'abonner
        </button>
        <p className="text-sm text-slate">Un lien de désinscription figure dans chaque e-mail.</p>
      </form>
    </>
  )
}
