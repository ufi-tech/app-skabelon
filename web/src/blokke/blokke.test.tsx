// En prøve pr. bloktype. Bliver en bloktype tilføjet i api/indhold.py uden en
// komponent her, fejler api-prøven test_hver_bloktype_har_en_komponent, og bliver
// komponenten tilføjet uden en prøve, fanger den her liste det.
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Blokken } from './index'
import { Billede } from './billede'
import { Knap } from './knap'
import { Overskrift } from './overskrift'
import { Tekst } from './tekst'

describe('overskrift', () => {
  it('viser teksten som h1 som standard', () => {
    render(<Overskrift blok={{ type: 'overskrift', tekst: 'Velkommen' }} />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Velkommen')
  })

  it('bruger niveauet når det er 2 eller 3', () => {
    render(<Overskrift blok={{ type: 'overskrift', niveau: 3, tekst: 'Underoverskrift' }} />)
    expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument()
  })

  it('falder tilbage til niveau 1 ved et umuligt niveau', () => {
    render(<Overskrift blok={{ type: 'overskrift', niveau: 9, tekst: 'Skæv' }} />)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})

describe('tekst', () => {
  it('viser teksten', () => {
    render(<Tekst blok={{ type: 'tekst', tekst: 'Noget om os' }} />)
    expect(screen.getByText('Noget om os')).toBeInTheDocument()
  })

  it('viser markup som tekst og ikke som html', () => {
    render(<Tekst blok={{ type: 'tekst', tekst: '<script>alarm()</script>' }} />)
    expect(screen.getByText('<script>alarm()</script>')).toBeInTheDocument()
    expect(document.querySelector('script')).toBeNull()
  })
})

describe('billede', () => {
  it('viser billedet med alt-tekst', () => {
    render(<Billede blok={{ type: 'billede', kilde: '/billeder/hus.svg', alt: 'Et hus' }} />)
    const billede = screen.getByAltText('Et hus')
    expect(billede).toHaveAttribute('src', '/billeder/hus.svg')
  })
})

describe('knap', () => {
  it('viser en intern adresse', () => {
    render(<Knap blok={{ type: 'knap', tekst: 'Log ind', href: '/log-ind' }} />)
    expect(screen.getByRole('link', { name: 'Log ind' })).toHaveAttribute('href', '/log-ind')
  })

  it('viser ikke en fremmed adresse', () => {
    render(<Knap blok={{ type: 'knap', tekst: 'Udad', href: 'https://example.com' }} />)
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('viser ikke en adresse der starter med to skråstreger', () => {
    render(<Knap blok={{ type: 'knap', tekst: 'Udad', href: '//example.com' }} />)
    expect(screen.queryByRole('link')).toBeNull()
  })
})

describe('Blokken', () => {
  it('vælger komponenten ud fra typen', () => {
    render(<Blokken blok={{ type: 'tekst', tekst: 'Gennem vælgeren' }} />)
    expect(screen.getByText('Gennem vælgeren')).toBeInTheDocument()
  })

  it('viser ingenting for en ukendt type', () => {
    const ukendt = { type: 'findes-ikke', tekst: 'skjult' } as unknown as Parameters<
      typeof Blokken
    >[0]['blok']
    const { container } = render(<Blokken blok={ukendt} />)
    expect(container).toBeEmptyDOMElement()
  })
})
