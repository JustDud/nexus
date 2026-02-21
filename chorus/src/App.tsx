import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { SimulationProvider } from './context/SimulationContext'
import { HomePage } from './pages/HomePage'
import { SimulationPage } from './pages/SimulationPage'

function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.01 }}
      transition={{ duration: 0.4, ease: 'easeInOut' }}
      style={{ position: 'absolute', inset: 0 }}
    >
      {children}
    </motion.div>
  )
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100vh' }}>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route
            path="/"
            element={
              <PageWrapper>
                <HomePage />
              </PageWrapper>
            }
          />
          <Route
            path="/simulation"
            element={
              <PageWrapper>
                <SimulationPage />
              </PageWrapper>
            }
          />
        </Routes>
      </AnimatePresence>
    </div>
  )
}

export default function App() {
  return (
    <SimulationProvider>
      <BrowserRouter>
        <AnimatedRoutes />
      </BrowserRouter>
    </SimulationProvider>
  )
}
