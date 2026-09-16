import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './styles.trend.css'
import './styles.polish.css'
import './styles.chrome.css'
import './styles.ambient.css'

const container = document.getElementById('root')
if (!container) throw new Error('Root container #root not found')

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
