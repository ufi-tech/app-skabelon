import { type FormEvent, useState } from 'react'
import { logInd } from '../api'
import type { Bruger } from '../typer'

export function LogInd({ naarLoggetInd }: { naarLoggetInd: (bruger: Bruger) => void }) {
  const [epost, setEpost] = useState('')
  const [kode, setKode] = useState('')
  const [fejl, setFejl] = useState('')
  const [sender, setSender] = useState(false)

  async function send(haendelse: FormEvent) {
    haendelse.preventDefault()
    setFejl('')
    setSender(true)
    try {
      const svar = await logInd(epost, kode)
      naarLoggetInd(svar.bruger)
    } catch (aarsag: unknown) {
      setFejl(aarsag instanceof Error ? aarsag.message : 'Der skete en fejl. Prøv igen.')
    } finally {
      setSender(false)
      setKode('')
    }
  }

  return (
    <form onSubmit={send} className="log-ind">
      <h1>Log ind</h1>
      <label htmlFor="epost">E-post</label>
      <input
        id="epost"
        name="epost"
        type="email"
        autoComplete="username"
        value={epost}
        onChange={(h) => setEpost(h.target.value)}
        required
      />
      <label htmlFor="kode">Adgangskode</label>
      <input
        id="kode"
        name="kode"
        type="password"
        autoComplete="current-password"
        value={kode}
        onChange={(h) => setKode(h.target.value)}
        required
      />
      {fejl ? <p role="alert">{fejl}</p> : null}
      <button type="submit" disabled={sender}>
        {sender ? 'Logger ind ...' : 'Log ind'}
      </button>
    </form>
  )
}
