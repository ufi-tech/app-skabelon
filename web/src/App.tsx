import { useEffect, useState } from 'react'
import { hentMig, logUd } from './api'
import { Forside } from './sider/Forside'
import { LogInd } from './sider/LogInd'
import type { Bruger } from './typer'

// En meget lille router. Den findes for ikke at trække et bibliotek ind, før der er
// brug for et. Skal appen have rigtige ruter, er react-router det næste skridt, og det
// står i README.
function stien(): string {
  return window.location.pathname === '/log-ind' ? '/log-ind' : window.location.pathname || '/'
}

export function App() {
  const [bruger, setBruger] = useState<Bruger | null>(null)
  const [sti, setSti] = useState(stien())

  useEffect(() => {
    hentMig()
      .then((svar) => setBruger(svar.bruger))
      .catch(() => setBruger(null))
  }, [])

  useEffect(() => {
    const lyt = () => setSti(stien())
    window.addEventListener('popstate', lyt)
    return () => window.removeEventListener('popstate', lyt)
  }, [])

  return (
    <div className="ramme">
      <header>
        <a href="/">site-basis</a>
        {bruger ? (
          <span>
            {bruger.navn || bruger.epost}{' '}
            <button
              type="button"
              onClick={() => {
                void logUd().then(() => setBruger(null))
              }}
            >
              Log ud
            </button>
          </span>
        ) : (
          <a href="/log-ind">Log ind</a>
        )}
      </header>
      <main>
        {sti === '/log-ind' ? <LogInd naarLoggetInd={setBruger} /> : <Forside sti={sti} />}
      </main>
    </div>
  )
}
