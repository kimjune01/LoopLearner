import { useState, useEffect } from 'react'
import { healthCheck } from './services/api'
import { InnerLoopProgress } from './components/InnerLoopProgress'
import './App.css'

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
    <>
      <div>
        <h1>Loop Learner</h1>
        <p>Human-in-the-loop machine learning system</p>
        <div className="card">
          <p>Backend Status: <strong>{backendStatus}</strong></p>
        </div>
        
        <InnerLoopProgress />
      </div>
    </>
  )
}

export default App
