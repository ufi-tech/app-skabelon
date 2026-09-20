import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './stil.css'

const rod = document.getElementById('rod')
if (!rod) {
  throw new Error('Elementet med id "rod" mangler i index.html.')
}

createRoot(rod).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
