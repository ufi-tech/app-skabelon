// Grundopsætning til vitest. Den giver expect(...).toBeInTheDocument() og rydder op
// efter hver prøve, så to prøver aldrig deler et DOM.
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
