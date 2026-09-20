/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Udviklingsserveren binder til 127.0.0.1. I containeren er det nginx der lytter, og
// den binder i sin egen kasse. /api sendes videre til api-tjenesten, så browseren kun
// møder ét domæne og cookien aldrig skal på tværs.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
      '/healthz': { target: 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/proevegrund.ts'],
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
})
