import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Session } from '../types/session';
import { sessionService } from '../services/sessionService';

export const SessionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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

    loadSession();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-700 flex items-center justify-center">
        <div className="flex items-center gap-3 text-white">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <span className="text-lg">Loading session...</span>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-700 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center text-white">
          <div className="w-16 h-16 mx-auto mb-4 bg-white/20 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-2">Session Not Found</h2>
          <p className="text-white/80 mb-6">{error || 'The requested session could not be found.'}</p>
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Sessions
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-700">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10 px-8 py-12">
          <div className="max-w-7xl mx-auto">
            {/* Navigation */}
            <div className="mb-8">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Sessions
              </Link>
            </div>

            {/* Session Header */}
            <div className="text-center">
              <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight drop-shadow-lg">
                {session.name}
              </h1>
              {session.description && (
                <p className="text-xl text-white/90 font-light mb-8 max-w-3xl mx-auto leading-relaxed">
                  {session.description}
                </p>
              )}
              
              {/* Session Status */}
              <div className="inline-flex items-center gap-4 bg-white/15 backdrop-blur-sm px-6 py-3 rounded-full border border-white/20 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${session.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                  <span className="text-white/80 font-medium">
                    {session.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="w-px h-4 bg-white/30"></div>
                <span className="text-white/80 font-medium">
                  ID: {session.id}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative -mt-4 z-20">
        <div className="max-w-7xl mx-auto bg-white rounded-t-2xl shadow-2xl min-h-[calc(100vh-300px)]">
          <div className="p-8">
            {/* Session Info Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Metadata */}
              <div className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Session Details</h3>
                <div className="space-y-3">
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

              {/* Initial Prompt */}
              {session.initial_prompt && (
                <div className="card p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Initial Prompt</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {session.initial_prompt}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-4 mb-8">
              <button className="btn-primary">
                Start Learning Session
              </button>
              <button className="btn-secondary">
                View Progress
              </button>
              <button className="btn-secondary">
                Export Data
              </button>
              <button className="btn-secondary">
                Edit Session
              </button>
            </div>

            {/* Placeholder for Learning Components */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              {/* Email Generation Section */}
              <div className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Email Generation</h3>
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <p>Email generation tools will appear here</p>
                </div>
              </div>

              {/* Learning Progress Section */}
              <div className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Learning Progress</h3>
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <p>Learning analytics will appear here</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};