import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, unsubscribe } from '../api/client.ts'

// Page ouverte par le lien « Se désinscrire » des e-mails : /unsubscribe/<jeton>
export default function Unsubscribe() {
  const { token = '' } = useParams()
  const [status, setStatus] = useState<'asking' | 'done' | 'invalid' | 'error'>('asking')

  async function confirm() {
    try {
      await unsubscribe(token)
      setStatus('done')
    } catch (error) {
      // 404 : le jeton n'existe pas. Autre cas : le serveur ne répond pas.
      setStatus(error instanceof ApiError && error.status === 404 ? 'invalid' : 'error')
    }
  }

  if (status === 'done') {
    return (
      <>
        <h1 className="font-display text-4xl font-bold">Vous êtes désabonné</h1>
        <p className="mt-4 max-w-xl text-lg text-slate">Vous ne recevrez plus d'e-mails de StageSonar.</p>
        <Link to="/subscribe" className="mt-6 inline-block underline">
          Se réabonner
        </Link>
      </>
    )
  }

  if (status === 'invalid') {
    return (
      <>
        <h1 className="font-display text-4xl font-bold">Lien invalide</h1>
        <p className="mt-4 max-w-xl text-lg text-slate">
          Ce lien de désinscription n'est pas reconnu. Utilisez celui qui figure en bas du dernier e-mail reçu.
        </p>
      </>
    )
  }

  return (
    <>
      <h1 className="font-display text-4xl font-bold">Se désabonner</h1>
      <p className="mt-4 max-w-xl text-lg text-slate">Confirmez pour ne plus recevoir les offres de stage par e-mail.</p>
      <button className="mt-6 rounded-md bg-abyss px-5 py-2.5 font-medium text-foam" onClick={confirm}>
        Me désabonner
      </button>
      {status === 'error' && (
        <p className="mt-4 font-medium text-red-700" role="alert">
          Le serveur de StageSonar ne répond pas. Réessayez dans un instant.
        </p>
      )}
    </>
  )
}
