import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <>
      <h1 className="font-display text-4xl font-bold">Les nouveaux stages, dès leur publication</h1>
      <p className="mt-4 max-w-xl text-lg text-slate">
        StageSonar surveille plusieurs sites de stages au Maroc, repère les offres qui viennent d'être publiées et
        envoie à chaque abonné celles qui correspondent à son profil.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/offers" className="rounded-md bg-abyss px-4 py-2 font-medium text-foam">
          Voir les offres
        </Link>
        <Link to="/subscribe" className="rounded-md border border-abyss px-4 py-2 font-medium">
          S'abonner
        </Link>
      </div>
    </>
  )
}
