import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import DemoWorkflow from './components/DemoWorkflow'

interface Email {
  id: number
  subject: string
  body: string
  sender: string
  scenario_type: string
}

interface Draft {
  id: number
  content: string
  version: number
  email: number
}

function App() {
  const [currentView, setCurrentView] = useState<'demo' | 'dashboard' | 'workflow'>('demo')
  const [currentEmail, setCurrentEmail] = useState<Email | null>(null)
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [selectedDraft, setSelectedDraft] = useState<Draft | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = 'http://localhost:8000/api'

  const generateSyntheticEmail = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/generate-synthetic-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario_type: 'random'
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setCurrentEmail({
        id: data.email_id,
        subject: data.subject,
        body: data.body,
        sender: data.sender,
        scenario_type: data.scenario_type
      })
      setDrafts([])
      setSelectedDraft(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate email')
    } finally {
      setLoading(false)
    }
  }

  const generateDrafts = async () => {
    if (!currentEmail) return
    
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/generate-drafts/${currentEmail.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          num_drafts: 3,
          constraints: {
            max_length: 200,
            tone: 'professional'
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setDrafts(data.drafts)
      setSelectedDraft(data.drafts[0] || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate drafts')
    } finally {
      setLoading(false)
    }
  }

  const submitFeedback = async (action: 'accept' | 'reject' | 'edit' | 'ignore', editedContent?: string) => {
    if (!selectedDraft) return
    
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/submit-feedback/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          draft_id: selectedDraft.id,
          action,
          edited_content: editedContent,
          reasoning_factors: {
            clarity: 4,
            tone: 4,
            completeness: 4,
            relevance: 4
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Feedback submitted:', data)
      
      // Generate new email after feedback
      generateSyntheticEmail()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    generateSyntheticEmail()
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col items-center text-center">
            <h1 className="text-4xl font-bold mb-2">Loop Learner</h1>
            <p className="text-blue-100 text-lg mb-6">Human-in-the-Loop Email Response Optimization</p>
            <nav className="flex gap-4">
              <button 
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  currentView === 'demo' 
                    ? 'bg-white text-blue-600 shadow-lg' 
                    : 'bg-white/20 text-white border-2 border-white/30 hover:bg-white/30'
                }`}
                onClick={() => setCurrentView('demo')}
              >
                Demo
              </button>
              <button 
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  currentView === 'workflow' 
                    ? 'bg-white text-blue-600 shadow-lg' 
                    : 'bg-white/20 text-white border-2 border-white/30 hover:bg-white/30'
                }`}
                onClick={() => setCurrentView('workflow')}
              >
                Workflow
              </button>
              <button 
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  currentView === 'dashboard' 
                    ? 'bg-white text-blue-600 shadow-lg' 
                    : 'bg-white/20 text-white border-2 border-white/30 hover:bg-white/30'
                }`}
                onClick={() => setCurrentView('dashboard')}
              >
                Dashboard
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {currentView === 'dashboard' ? (
          <Dashboard />
        ) : currentView === 'workflow' ? (
          <DemoWorkflow />
        ) : (
          <div className="max-w-5xl mx-auto px-6 py-8">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <div className="text-red-800">
                  <strong>Error:</strong> {error}
                </div>
              </div>
            )}

            <section className="mb-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Incoming Email</h2>
                <button 
                  onClick={generateSyntheticEmail} 
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  {loading ? 'Generating...' : 'Generate New Email'}
                </button>
              </div>
              
              {currentEmail && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                  <div className="flex gap-4 text-sm text-gray-600 mb-4">
                    <span><strong>From:</strong> {currentEmail.sender}</span>
                    <span><strong>Type:</strong> {currentEmail.scenario_type}</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">{currentEmail.subject}</h3>
                  <p className="text-gray-700 leading-relaxed">{currentEmail.body}</p>
                </div>
              )}
            </section>

            <section>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Response Drafts</h2>
                <button 
                  onClick={generateDrafts} 
                  disabled={loading || !currentEmail}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  {loading ? 'Generating...' : 'Generate Drafts'}
                </button>
              </div>

              {drafts.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="flex border-b border-gray-200">
                    {drafts.map((draft, index) => (
                      <button
                        key={draft.id}
                        className={`flex-1 px-6 py-4 font-medium transition-colors ${
                          selectedDraft?.id === draft.id
                            ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                        onClick={() => setSelectedDraft(draft)}
                      >
                        Draft {index + 1}
                      </button>
                    ))}
                  </div>

                  {selectedDraft && (
                    <div className="p-6">
                      <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <p className="text-gray-800 leading-relaxed">
                          {selectedDraft.content}
                        </p>
                      </div>
                      
                      <div className="flex gap-3">
                        <button 
                          className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                          onClick={() => submitFeedback('accept')}
                          disabled={loading}
                        >
                          ✓ Accept
                        </button>
                        <button 
                          className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                          onClick={() => submitFeedback('reject')}
                          disabled={loading}
                        >
                          ✗ Reject
                        </button>
                        <button 
                          className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                          onClick={() => {
                            const edited = prompt('Edit the draft:', selectedDraft.content)
                            if (edited && edited !== selectedDraft.content) {
                              submitFeedback('edit', edited)
                            }
                          }}
                          disabled={loading}
                        >
                          ✎ Edit
                        </button>
                        <button 
                          className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                          onClick={() => submitFeedback('ignore')}
                          disabled={loading}
                        >
                          Skip
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App