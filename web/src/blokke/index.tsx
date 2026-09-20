import type { Blok } from '../typer'
import { Billede } from './billede'
import { Knap } from './knap'
import { Overskrift } from './overskrift'
import { Tekst } from './tekst'

// Én indgang til alle bloktyper. Er typen ukendt, bliver blokken ikke vist, og resten
// af siden virker stadig.
export function Blokken({ blok }: { blok: Blok }) {
  switch (blok.type) {
    case 'overskrift':
      return <Overskrift blok={blok} />
    case 'tekst':
      return <Tekst blok={blok} />
    case 'billede':
      return <Billede blok={blok} />
    case 'knap':
      return <Knap blok={blok} />
    default:
      return null
  }
}
