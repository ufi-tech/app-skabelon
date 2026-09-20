// Api-laget: fejlbeskeden fra serveren skal nå brugeren, og cookien skal følge med.
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiFejl, hentMig, logInd } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
})

function svar(status: number, krop: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => krop,
  } as Response
}

describe('api', () => {
  it('sender sessionscookien med', async () => {
    const hentet = vi.fn(async () => svar(200, { bruger: { id: 1, epost: 'a@example.com', navn: '' } }))
    vi.stubGlobal('fetch', hentet)
    await hentMig()
    expect(hentet).toHaveBeenCalledWith('/api/mig', expect.objectContaining({ credentials: 'same-origin' }))
  })

  it('giver serverens besked videre ved 401', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => svar(401, { detail: 'E-posten eller adgangskoden passer ikke.' })))
    await expect(logInd('a@example.com', 'forkert-kode-her')).rejects.toThrow(
      'E-posten eller adgangskoden passer ikke.',
    )
  })

  it('har en generel besked når svaret ikke er JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          ({
            ok: false,
            status: 500,
            json: async () => {
              throw new Error('ikke json')
            },
          }) as unknown as Response,
      ),
    )
    await expect(hentMig()).rejects.toBeInstanceOf(ApiFejl)
  })
})
