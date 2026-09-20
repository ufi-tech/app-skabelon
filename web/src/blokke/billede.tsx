import type { BilledeBlok } from '../typer'

// alt-teksten er påkrævet i typen. Et billede uden alt er utilgængeligt for dem der
// bruger skærmlæser, og det er ikke et valg der skal kunne glemmes.
export function Billede({ blok }: { blok: BilledeBlok }) {
  return (
    <figure className="blok blok-billede">
      <img src={blok.kilde} alt={blok.alt} loading="lazy" />
    </figure>
  )
}
