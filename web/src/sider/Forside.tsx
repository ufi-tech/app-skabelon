import { useEffect, useState } from 'react'
import { hentSide } from '../api'
import { Blokken } from '../blokke'
import type { Side } from '../typer'

export function Forside({ sti }: { sti: string }) {
  const [side, setSide] = useState<Side | null>(null)
  const [fejl, setFejl] = useState<string>('')

  useEffect(() => {
    let gaelder = true
    hentSide(sti)
      .then((hentet) => {
        if (gaelder) setSide(hentet)
      })
      .catch((aarsag: unknown) => {
        if (gaelder) setFejl(aarsag instanceof Error ? aarsag.message : 'Siden kunne ikke hentes.')
      })
    return () => {
      gaelder = false
    }
  }, [sti])

  if (fejl) {
    return <p role="alert">{fejl}</p>
  }
  if (!side) {
    return <p>Henter indholdet ...</p>
  }
  return (
    <article>
      {side.blokke.map((blok, nr) => (
        <Blokken key={nr} blok={blok} />
      ))}
    </article>
  )
}
