import { NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home.tsx'
import Offers from './pages/Offers.tsx'
import Subscribe from './pages/Subscribe.tsx'

const LINKS = [
  { to: '/', label: 'Accueil' },
  { to: '/offers', label: 'Offres' },
  { to: '/subscribe', label: "S'abonner" },
]

export default function App() {
  return (
    <>
      <header className="bg-abyss text-foam">
        <nav className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-4">
          <NavLink to="/" className="font-display text-2xl font-bold">
            StageSonar
          </NavLink>
          <ul className="flex gap-5">
            {LINKS.map((link) => (
              <li key={link.to}>
                <NavLink
                  to={link.to}
                  className={({ isActive }) =>
                    `border-b-2 pb-1 ${isActive ? 'border-beacon' : 'border-transparent hover:border-foam/50'}`
                  }
                >
                  {link.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/offers" element={<Offers />} />
          <Route path="/subscribe" element={<Subscribe />} />
        </Routes>
      </main>
    </>
  )
}
