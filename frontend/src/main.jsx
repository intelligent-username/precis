import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// StrictMode was doubling all effects in dev (mount→unmount→remount) which
// caused duplicate /models + /warmup calls on every reload → perceived lag
// and "stops after script fetching" race. We run without it for stability.
// Re-enable only if you need to audit effects.
// import { StrictMode } from 'react'

createRoot(document.getElementById('root')).render(<App />)
