import type { OverskriftBlok } from '../typer'

// Niveauet begrænses til 1-3. Et tal fra indholdet må aldrig blive til et frit
// elementnavn: så kunne en forkert værdi lave et element der ikke findes.
const NIVEAUER = { 1: 'h1', 2: 'h2', 3: 'h3' } as const

export function Overskrift({ blok }: { blok: OverskriftBlok }) {
  const niveau = blok.niveau === 2 ? 2 : blok.niveau === 3 ? 3 : 1
  const Element = NIVEAUER[niveau]
  return <Element className={`blok blok-overskrift niveau-${niveau}`}>{blok.tekst}</Element>
}
