import type { TekstBlok } from '../typer'

// Teksten sættes som tekst, aldrig som HTML. dangerouslySetInnerHTML hører ikke til i
// en bloktype: kommer indholdet en dag fra et api, er det den vej et script kommer ind.
export function Tekst({ blok }: { blok: TekstBlok }) {
  return <p className="blok blok-tekst">{blok.tekst}</p>
}
