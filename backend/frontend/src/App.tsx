import { useState, useEffect } from 'react'
import './App.css'

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
      // API returns the email data directly, not nested under 'email'
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
    <div className="app">
      <header className="app-header">
        <h1>Loop Learner</h1>
        <p>Human-in-the-Loop Email Response Optimization</p>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        <section className="email-section">
          <div className="section-header">
            <h2>Incoming Email</h2>
            <button onClick={generateSyntheticEmail} disabled={loading}>
              {loading ? 'Generating...' : 'Generate New Email'}
            </button>
          </div>
          
          {currentEmail && (
            <div className="email-card">
              <div className="email-meta">
                <strong>From:</strong> {currentEmail.sender} | <strong>Type:</strong> {currentEmail.scenario_type}
              </div>
              <h3>{currentEmail.subject}</h3>
              <p>{currentEmail.body}</p>
            </div>
          )}
        </section>

        <section className="drafts-section">
          <div className="section-header">
            <h2>Response Drafts</h2>
            <button 
              onClick={generateDrafts} 
              disabled={loading || !currentEmail}
            >
              {loading ? 'Generating...' : 'Generate Drafts'}
            </button>
          </div>

          {drafts.length > 0 && (
            <div className="drafts-container">
              <div className="draft-selector">
                {drafts.map((draft, index) => (
                  <button
                    key={draft.id}
                    className={`draft-tab ${selectedDraft?.id === draft.id ? 'active' : ''}`}
                    onClick={() => setSelectedDraft(draft)}
                  >
                    Draft {index + 1}
                  </button>
                ))}
              </div>

              {selectedDraft && (
                <div className="draft-content">
                  <div className="draft-text">
                    {selectedDraft.content}
                  </div>
                  
                  <div className="feedback-actions">
                    <button 
                      className="feedback-btn accept"
                      onClick={() => submitFeedback('accept')}
                      disabled={loading}
                    >
                      ✓ Accept
                    </button>
                    <button 
                      className="feedback-btn reject"
                      onClick={() => submitFeedback('reject')}
                      disabled={loading}
                    >
                      ✗ Reject
                    </button>
                    <button 
                      className="feedback-btn edit"
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
                      className="feedback-btn ignore"
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
      </main>
    </div>
  )
}

export default App