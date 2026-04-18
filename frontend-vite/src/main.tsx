/**
 * Application entry: Ant Design reset, theme, app context, and React root.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'antd/dist/reset.css'
import './index.css'
import { RTThemeProvider } from './theme'

import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RTThemeProvider>
      <App />
    </RTThemeProvider>
  </StrictMode>,
)
