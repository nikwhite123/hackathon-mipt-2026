import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppProvider } from './hooks/AppContext.tsx'
import 'antd/dist/reset.css'
import { RTThemeProvider } from './theme'

import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RTThemeProvider>
      <AppProvider>
        <App />
      </AppProvider>
    </RTThemeProvider>
  </StrictMode>,
)
