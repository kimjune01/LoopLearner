import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { healthCheck } from './services/api'
import { SessionCollection } from './components/SessionCollection'
import { SessionDetail } from './components/SessionDetail'
import { AboutPage } from './components/AboutPage'
import EvaluationDatasetList from './components/EvaluationDatasetList'
import EvaluationDatasetDetail from './components/EvaluationDatasetDetail'
import ReasoningFeedbackDemo from './components/ReasoningFeedbackDemo'
import ProgressVisualizationDemo from './components/ProgressVisualizationDemo'

// Navigation component
const Navigation: React.FC<{ backendStatus: string }> = ({ backendStatus }) => {
  const location = useLocation()
  
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
  
  const isActive = (path: string) => {
    return location.pathname.startsWith(path)
  }
  
  return (
    <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-2xl font-bold text-white hover:text-white/90">
              Loop Learner
            </Link>
            <div className="hidden sm:block w-px h-6 bg-white/30"></div>
            <nav className="hidden sm:flex items-center gap-6">
              <Link 
                to="/" 
                className={`text-white/90 hover:text-white text-sm font-medium ${
                  location.pathname === '/' ? 'text-white' : ''
                }`}
              >
                Sessions
              </Link>
              <Link 
                to="/evaluation/datasets" 
                className={`text-white/90 hover:text-white text-sm font-medium ${
                  isActive('/evaluation') ? 'text-white' : ''
                }`}
              >
                Evaluation
              </Link>
              <Link 
                to="/reasoning-demo" 
                className={`text-white/90 hover:text-white text-sm font-medium ${
                  isActive('/reasoning-demo') ? 'text-white' : ''
                }`}
              >
                Reasoning Demo
              </Link>
              <Link 
                to="/progress-demo" 
                className={`text-white/90 hover:text-white text-sm font-medium ${
                  isActive('/progress-demo') ? 'text-white' : ''
                }`}
              >
                Progress Demo
              </Link>
              <Link 
                to="/about" 
                className={`text-white/90 hover:text-white text-sm font-medium ${
                  isActive('/about') ? 'text-white' : ''
                }`}
              >
                About
              </Link>
            </nav>
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
  )
}

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

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation backendStatus={backendStatus} />
        
        <Routes>
          <Route path="/" element={<SessionCollection />} />
          <Route path="/sessions/:id" element={<SessionDetail />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/evaluation/datasets" element={<EvaluationDatasetList />} />
          <Route path="/evaluation/datasets/:datasetId" element={<EvaluationDatasetDetail />} />
          <Route path="/reasoning-demo" element={<ReasoningFeedbackDemo />} />
          <Route path="/progress-demo" element={<ProgressVisualizationDemo />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
