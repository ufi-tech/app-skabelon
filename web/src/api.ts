// Alle kald til api'et samlet ét sted.
//
// credentials: 'same-origin' er det vigtige: sessionscookien følger med, og den følger
// KUN med til vores eget domæne. Der ligger ingen nøgle i frontenden, og der skal der
// heller aldrig komme til at ligge en: alt i web/ kan læses af enhver besøgende.

import type { Bruger, Side } from './typer'

export class ApiFejl extends Error {
  status: number

  constructor(status: number, besked: string) {
    super(besked)
    this.name = 'ApiFejl'
    this.status = status
  }
}

async function kald<T>(sti: string, indstillinger: RequestInit = {}): Promise<T> {
  const svar = await fetch(sti, {
    ...indstillinger,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(indstillinger.headers ?? {}) },
  })
  if (!svar.ok) {
    let besked = 'Der skete en fejl. Prøv igen.'
    try {
      const krop = (await svar.json()) as { detail?: string }
      if (typeof krop.detail === 'string' && krop.detail) {
        besked = krop.detail
      }
    } catch {
      // Svaret var ikke JSON. Så står den generelle besked.
    }
    throw new ApiFejl(svar.status, besked)
  }
  return (await svar.json()) as T
}

export function hentSider(): Promise<{ sider: { sti: string; titel: string }[] }> {
  return kald('/api/indhold/sider')
}

export function hentSide(sti: string): Promise<Side> {
  return kald(`/api/indhold/side?sti=${encodeURIComponent(sti)}`)
}

export function logInd(epost: string, kode: string): Promise<{ bruger: Bruger }> {
  return kald('/api/log-ind', {
    method: 'POST',
    body: JSON.stringify({ epost, adgangskode: kode }),
  })
}

export function logUd(): Promise<{ logget_ud: boolean }> {
  return kald('/api/log-ud', { method: 'POST' })
}

export function hentMig(): Promise<{ bruger: Bruger }> {
  return kald('/api/mig')
}
