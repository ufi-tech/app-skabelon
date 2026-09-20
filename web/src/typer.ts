// Formen på indholdet. Den samme form som api/indhold.py leverer, og den er det eneste
// sted typerne står. Tilføjer du en bloktype i api'et, tilføjer du den her og i
// src/blokke/.

export type Bloktype = 'overskrift' | 'tekst' | 'billede' | 'knap'

export interface OverskriftBlok {
  type: 'overskrift'
  niveau?: number
  tekst: string
}

export interface TekstBlok {
  type: 'tekst'
  tekst: string
}

export interface BilledeBlok {
  type: 'billede'
  kilde: string
  alt: string
}

export interface KnapBlok {
  type: 'knap'
  tekst: string
  href: string
}

export type Blok = OverskriftBlok | TekstBlok | BilledeBlok | KnapBlok

export interface Side {
  sti: string
  titel: string
  blokke: Blok[]
}

export interface Bruger {
  id: number
  epost: string
  navn: string
}
