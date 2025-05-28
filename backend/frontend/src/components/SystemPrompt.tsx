import { useState, useEffect } from 'react'

interface SystemPromptData {
  id: number
  version: number
  content: string
  is_active: boolean
  created_at: string
  updated_at: string
  scenario_type: string
  performance_score: number | null
  metadata: {
    word_count: number
    character_count: number
    line_count: number
  }
}

function SystemPrompt() {
  const [promptData, setPromptData] = useState<SystemPromptData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exportLoading, setExportLoading] = useState<string | null>(null)

  const API_BASE = 'http://localhost:8000/api'

  const fetchSystemPrompt = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/system/prompt/`)
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No system prompt found')
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setPromptData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system prompt')
    } finally {
      setLoading(false)
    }
  }

  const exportPrompt = async (format: 'json' | 'txt' | 'md', includeMetadata: boolean = true) => {
    if (!promptData) return
    
    setExportLoading(format)
    try {
      const params = new URLSearchParams({
        format,
        include_metadata: includeMetadata.toString()
      })
      
      const response = await fetch(`${API_BASE}/system/prompt/export/?${params}`)
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`)
      }
      
      // Get the filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `system_prompt_v${promptData.version}.${format}`
      
      // Create download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to export ${format.toUpperCase()}`)
    } finally {
      setExportLoading(null)
    }
  }

  useEffect(() => {
    fetchSystemPrompt()
  }, [])

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading system prompt...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-red-600 text-xl mr-3">⚠️</div>
            <div>
              <h3 className="text-red-800 font-semibold">Error Loading System Prompt</h3>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
          <button 
            onClick={fetchSystemPrompt}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!promptData) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="text-yellow-800">
            <h3 className="font-semibold">No System Prompt Found</h3>
            <p className="mt-1">There is no active system prompt configured.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Prompt</h1>
          <p className="text-gray-600 mt-2">View and export the current active system prompt</p>
        </div>
        <button 
          onClick={fetchSystemPrompt}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Prompt Info Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Prompt Information</h2>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                promptData.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {promptData.is_active ? 'Active' : 'Inactive'}
              </span>
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                v{promptData.version}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Scenario Type:</span>
              <p className="font-medium text-gray-900 capitalize">{promptData.scenario_type}</p>
            </div>
            <div>
              <span className="text-gray-500">Performance Score:</span>
              <p className="font-medium text-gray-900">
                {promptData.performance_score ? `${(promptData.performance_score * 100).toFixed(1)}%` : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Created:</span>
              <p className="font-medium text-gray-900">
                {new Date(promptData.created_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Last Updated:</span>
              <p className="font-medium text-gray-900">
                {new Date(promptData.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="p-6 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-blue-600">{promptData.metadata.word_count}</div>
              <div className="text-gray-600">Words</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-green-600">{promptData.metadata.character_count}</div>
              <div className="text-gray-600">Characters</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-purple-600">{promptData.metadata.line_count}</div>
              <div className="text-gray-600">Lines</div>
            </div>
          </div>
        </div>
      </div>

      {/* Prompt Content */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Prompt Content</h2>
        </div>
        <div className="p-6">
          <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm leading-relaxed">
            <pre className="whitespace-pre-wrap text-gray-800">{promptData.content}</pre>
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Export Options</h2>
          <p className="text-gray-600 mt-1">Download the system prompt in various formats</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* JSON Export */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-blue-600 text-lg">📄</div>
                <h3 className="font-semibold text-gray-900">JSON Format</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Structured data format with all metadata included
              </p>
              <button
                onClick={() => exportPrompt('json')}
                disabled={exportLoading === 'json'}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {exportLoading === 'json' ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download JSON
                  </>
                )}
              </button>
            </div>

            {/* Text Export */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-green-600 text-lg">📝</div>
                <h3 className="font-semibold text-gray-900">Text Format</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Plain text file with optional metadata header
              </p>
              <button
                onClick={() => exportPrompt('txt')}
                disabled={exportLoading === 'txt'}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {exportLoading === 'txt' ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download TXT
                  </>
                )}
              </button>
            </div>

            {/* Markdown Export */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-purple-600 text-lg">📖</div>
                <h3 className="font-semibold text-gray-900">Markdown Format</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                Formatted markdown file with documentation structure
              </p>
              <button
                onClick={() => exportPrompt('md')}
                disabled={exportLoading === 'md'}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {exportLoading === 'md' ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download MD
                  </>
                )}
              </button>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="text-blue-600 text-lg">💡</div>
              <div>
                <h4 className="font-semibold text-blue-800">Export Tips</h4>
                <ul className="text-blue-700 text-sm mt-1 space-y-1">
                  <li>• JSON format includes all metadata and is machine-readable</li>
                  <li>• TXT format is best for simple text editors and code integration</li>
                  <li>• Markdown format is ideal for documentation and sharing</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemPrompt