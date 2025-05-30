import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Session } from '../types/session';
import { sessionService } from '../services/sessionService';
import { PromptEditor } from './PromptEditor';

export const SessionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPromptEditor, setShowPromptEditor] = useState(false);

  const loadSession = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const sessionData = await sessionService.getSession(id);
      setSession(sessionData);
      setError(null);
    } catch (err) {
      setError('Failed to load session');
      console.error('Error loading session:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, [id]);

  const handleSavePrompt = async (prompt: string) => {
    if (!session || !id) return;
    
    try {
      // TODO: Implement API call to save/update session prompt
      // await sessionService.updateSessionPrompt(id, prompt);
      
      // For now, just update the local state
      setSession(prev => prev ? { ...prev, initial_prompt: prompt } : null);
      setShowPromptEditor(false);
      
      // Reload session to get updated data
      await loadSession();
    } catch (err) {
      console.error('Error saving prompt:', err);
      setError('Failed to save prompt');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Sessions
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">Loading...</h1>
            </div>
          </div>
        </div>
        
        {/* Loading Content */}
        <div className="flex items-center justify-center min-h-[calc(100vh-120px)]">
          <div className="flex items-center gap-3 text-gray-600">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <span className="text-lg">Loading session...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Sessions
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">Session Not Found</h1>
            </div>
          </div>
        </div>
        
        {/* Error Content */}
        <div className="flex items-center justify-center min-h-[calc(100vh-120px)]">
          <div className="max-w-md mx-auto text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Session Not Found</h2>
            <p className="text-gray-600 mb-6">{error || 'The requested session could not be found.'}</p>
            <Link 
              to="/" 
              className="btn-primary"
            >
              Back to Sessions
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compact Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Sessions
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">
                {session.name}
              </h1>
              {session.description && (
                <>
                  <div className="hidden sm:block w-px h-6 bg-white/30"></div>
                  <p className="hidden sm:block text-white/90 text-sm max-w-md truncate">
                    {session.description}
                  </p>
                </>
              )}
            </div>
            
            {/* Session Status */}
            <div className="flex items-center gap-3 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${session.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                <span className="text-white/80 text-sm font-medium">
                  {session.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-0">
        <div className="max-w-7xl mx-auto bg-white shadow-lg min-h-[calc(100vh-120px)]">
          <div className="p-8">
            {/* Current System Prompt - Most Prominent Section */}
            <div className="mb-12">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  Current System Prompt
                </h2>
                <p className="text-gray-600 text-lg">
                  The evolving intelligence guiding this session
                </p>
              </div>
              
              <div className="card-elevated p-8 mb-6">
                {session.initial_prompt ? (
                  <div className="space-y-6">
                    {/* Prompt Content */}
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6 border-l-4 border-purple-500">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                            Active Prompt • Version 1
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Last updated: {new Date(session.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      
                      <div className="text-lg leading-relaxed text-gray-800 font-medium">
                        {session.initial_prompt}
                      </div>
                    </div>
                    
                    {/* Prompt Actions */}
                    <div className="flex flex-wrap gap-3 justify-center">
                      <button 
                        onClick={() => setShowPromptEditor(true)}
                        className="btn-primary flex items-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Edit Prompt
                      </button>
                      <button className="btn-secondary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        View History
                      </button>
                      <button className="btn-secondary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Performance Metrics
                      </button>
                      <button className="btn-secondary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                        Export Prompt
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No System Prompt Set</h3>
                    <p className="text-gray-600 mb-6">
                      This session needs a system prompt to begin learning.
                      {session.description && (
                        <span className="block mt-2 text-sm italic">
                          Use your session description "{session.description}" as inspiration.
                        </span>
                      )}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <a 
                        href="https://console.anthropic.com/dashboard"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Generate with Claude
                      </a>
                      <button 
                        onClick={() => setShowPromptEditor(true)}
                        className="btn-secondary flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Write Manually
                      </button>
                    </div>
                    
                    {/* Helpful tip */}
                    <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-2xl mx-auto">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0">
                          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div className="text-left">
                          <p className="text-sm text-blue-800">
                            <strong>Tip:</strong> Ask Claude to create a system prompt for "{session.name}"{session.description && ` based on: "${session.description}"`}. 
                            This will give you a great starting point for your learning session.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Secondary Info Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Session Metadata */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Session Info
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="font-medium">{new Date(session.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Updated:</span>
                    <span className="font-medium">{new Date(session.updated_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      session.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {session.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Learning Stats */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Progress
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Iterations:</span>
                    <span className="font-medium text-green-600">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Emails Processed:</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Feedback Collected:</span>
                    <span className="font-medium">0</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Quick Actions
                </h3>
                <div className="space-y-2">
                  <button className="w-full btn-secondary text-left justify-start">
                    Start Learning Session
                  </button>
                  <button className="w-full btn-secondary text-left justify-start">
                    Generate Test Email
                  </button>
                  <button className="w-full btn-secondary text-left justify-start">
                    Export Session Data
                  </button>
                </div>
              </div>
            </div>

            {/* Learning Components Placeholder */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              {/* Email Generation Section */}
              <div className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Email Testing
                </h3>
                <div className="text-center py-8 text-gray-500">
                  <div className="w-12 h-12 mx-auto mb-3 bg-indigo-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <p className="mb-4">Generate test emails to train your prompt</p>
                  <button className="btn-primary">
                    Generate Test Email
                  </button>
                </div>
              </div>

              {/* Learning Progress Section */}
              <div className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                  Learning Analytics
                </h3>
                <div className="text-center py-8 text-gray-500">
                  <div className="w-12 h-12 mx-auto mb-3 bg-green-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <p className="mb-4">Track prompt performance and evolution</p>
                  <button className="btn-secondary">
                    View Analytics
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Prompt Editor Modal */}
      {showPromptEditor && (
        <PromptEditor
          initialPrompt={session?.initial_prompt || ''}
          sessionName={session?.name}
          sessionDescription={session?.description}
          onSave={handleSavePrompt}
          onCancel={() => setShowPromptEditor(false)}
          isCreating={!session?.initial_prompt}
        />
      )}
    </div>
  );
};