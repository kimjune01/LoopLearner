import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { healthCheck } from './services/api'
import { SessionCollection } from './components/SessionCollection'
import { SessionDetail } from './components/SessionDetail'

function App() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...')

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const result = await healthCheck()
        setBackendStatus(result.status)
      } catch (error) {
        setBackendStatus('disconnected')
      }
    }
    checkBackend()
  }, [])

  const getStatusStyles = (status: string) => {
    const baseStyles = "px-4 py-1.5 rounded-full font-semibold text-xs uppercase tracking-wider shadow-sm"
    switch (status) {
      case 'healthy':
        return `${baseStyles} bg-gradient-to-r from-green-400 to-green-600 text-white`
      case 'checking':
        return `${baseStyles} bg-gradient-to-r from-yellow-400 to-yellow-600 text-white`
      case 'disconnected':
        return `${baseStyles} bg-gradient-to-r from-red-400 to-red-600 text-white`
      default:
        return `${baseStyles} bg-gray-400 text-white`
    }
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={
          <div className="min-h-screen bg-gray-50">
            {/* Compact Header */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
              <div className="max-w-7xl mx-auto px-8 py-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold text-white">
                      Loop Learner
                    </h1>
                    <div className="hidden sm:block w-px h-6 bg-white/30"></div>
                    <p className="hidden sm:block text-white/90 text-sm">
                      Human-in-the-loop machine learning system
                    </p>
                  </div>
                  
                  {/* Status Indicator */}
                  <div className="flex items-center gap-3 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
                    <span className="text-white/80 text-sm font-medium">Backend:</span>
                    <span className={getStatusStyles(backendStatus)}>
                      {backendStatus}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Main Content */}
            <div className="pt-0">
              <SessionCollection />
            </div>
          </div>
        } />
        <Route path="/sessions/:id" element={<SessionDetail />} />
      </Routes>
    </Router>
  )
}

export default App
