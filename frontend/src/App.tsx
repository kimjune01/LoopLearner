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
          <div className="min-h-screen bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-700">
            {/* Hero Header */}
            <div className="relative overflow-hidden">
              {/* Background Pattern */}
              <div className="absolute inset-0 bg-black/10"></div>
              <div className="absolute inset-0 opacity-30">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent transform -skew-y-12"></div>
              </div>
              
              {/* Floating Elements */}
              <div 
                className="absolute top-20 left-10 w-24 h-24 bg-white/10 rounded-full animate-float"
                style={{ animationDelay: '0s' }}
              ></div>
              <div 
                className="absolute top-40 right-20 w-16 h-16 bg-white/5 rounded-full animate-float"
                style={{ animationDelay: '-2s' }}
              ></div>
              <div 
                className="absolute bottom-20 left-1/4 w-20 h-20 bg-white/5 rounded-full animate-float"
                style={{ animationDelay: '-4s' }}
              ></div>
              
              {/* Header Content */}
              <div className="relative z-10 text-center py-16 px-8">
                <h1 className="text-6xl font-extrabold text-white mb-4 tracking-tight drop-shadow-lg">
                  Loop Learner
                </h1>
                <p className="text-xl text-white/90 font-light mb-8 max-w-2xl mx-auto leading-relaxed">
                  Human-in-the-loop machine learning system for adaptive prompt evolution
                </p>
                
                {/* Status Indicator */}
                <div className="inline-flex items-center gap-3 bg-white/15 backdrop-blur-sm px-6 py-3 rounded-full border border-white/20 shadow-lg">
                  <span className="text-white/80 font-medium">Backend Status:</span>
                  <span className={getStatusStyles(backendStatus)}>
                    {backendStatus}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Main Content */}
            <div className="relative -mt-4 z-20">
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
