import type { KnapBlok } from '../typer'

// Kun interne adresser. En href fra indholdet må ikke kunne blive til javascript: eller
// til et fremmed domæne uden at nogen har taget stilling.
function erInternAdresse(href: string): boolean {
  return href.startsWith('/') && !href.startsWith('//')
}

export function Knap({ blok }: { blok: KnapBlok }) {
  if (!erInternAdresse(blok.href)) {
    return null
  }
  return (
    <a className="blok blok-knap" href={blok.href}>
      {blok.tekst}
    </a>
  )
}
