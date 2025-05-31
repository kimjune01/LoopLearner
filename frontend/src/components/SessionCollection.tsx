import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import type { Session } from '../types/session';
import { sessionService } from '../services/sessionService';
import { SessionCreator } from './SessionCreator';
import { SessionCard } from './SessionCard';
import ExportDialog from './ExportDialog';

export const SessionCollection: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'name'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [exportDialog, setExportDialog] = useState<{ open: boolean; session: Session | null }>({ open: false, session: null });

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await sessionService.getAllSessions({
        search: searchTerm || undefined,
        sort_by: sortBy,
        order: sortOrder
      });
      setSessions(response.sessions);
      setError(null);
    } catch (err) {
      setError('Failed to load sessions');
      console.error('Error loading sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [searchTerm, sortBy, sortOrder]);

  const handleCreateSession = async (sessionData: { name: string; description: string; initial_prompt?: string }) => {
    try {
      await sessionService.createSession(sessionData);
      setShowCreateForm(false);
      await loadSessions(); // Reload the session list
    } catch (err) {
      console.error('Error creating session:', err);
      setError('Failed to create session');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      return;
    }

    try {
      await sessionService.deleteSession(sessionId);
      await loadSessions(); // Reload the session list
    } catch (err) {
      console.error('Error deleting session:', err);
      setError('Failed to delete session');
    }
  };

  const handleDuplicateSession = async (sessionId: string) => {
    try {
      const originalSession = sessions.find(s => s.id === sessionId);
      if (!originalSession) return;

      await sessionService.duplicateSession(sessionId, {
        name: `${originalSession.name} (Copy)`,
        description: originalSession.description,
        copy_emails: false // Don't copy emails by default
      });
      await loadSessions(); // Reload the session list
    } catch (err) {
      console.error('Error duplicating session:', err);
      setError('Failed to duplicate session');
    }
  };

  const handleExportSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setExportDialog({ open: true, session });
    }
  };

  const filteredSessions = sessions.filter(session =>
    session.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    session.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto bg-white rounded-t-2xl min-h-[calc(100vh-200px)]">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <span className="text-gray-600 text-lg">Loading sessions...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto bg-white shadow-lg min-h-[calc(100vh-120px)]">
      {/* Page Header */}
      <div className="px-8 pt-8 pb-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Learning Sessions
            </h2>
            <div className="w-px h-6 bg-gray-300"></div>
            <p className="text-gray-600">
              Create and manage your prompt evolution sessions
            </p>
          </div>
          <button 
            className="btn-primary flex items-center gap-2 shrink-0"
            onClick={() => setShowCreateForm(true)}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Session
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-8 mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button 
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700 font-bold text-lg"
          >
            ×
          </button>
        </div>
      )}

      {/* Controls */}
      <div className="px-8 py-6 border-b border-gray-100">
        <div className="flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search sessions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
              />
            </div>
          </div>
          
          {/* Sort Controls */}
          <div className="flex items-center gap-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'created_at' | 'updated_at' | 'name')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
            >
              <option value="updated_at">Last Updated</option>
              <option value="created_at">Created Date</option>
              <option value="name">Name</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
        
        {/* Stats */}
        <div className="flex gap-8 mt-6 p-4 bg-gray-50 rounded-xl">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{sessions.length}</div>
            <div className="text-sm text-gray-600">Total Sessions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{sessions.filter(s => s.is_active).length}</div>
            <div className="text-sm text-gray-600">Active Sessions</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        {filteredSessions.length === 0 ? (
          <div className="text-center py-16">
            {searchTerm ? (
              <div className="max-w-md mx-auto">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No sessions found</h3>
                <p className="text-gray-600 mb-4">No sessions match your search criteria.</p>
                <button 
                  onClick={() => setSearchTerm('')}
                  className="btn-secondary"
                >
                  Clear search
                </button>
              </div>
            ) : (
              <div className="max-w-md mx-auto">
                <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">No sessions yet</h3>
                <p className="text-gray-600 mb-6">Create your first learning session to get started with prompt evolution.</p>
                <button 
                  className="btn-primary"
                  onClick={() => setShowCreateForm(true)}
                >
                  Create Your First Session
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredSessions.map(session => (
              <SessionCard
                key={session.id}
                session={session}
                onView={(id) => navigate(`/sessions/${id}`)}
                onEdit={(id) => navigate(`/sessions/${id}/edit`)}
                onDelete={handleDeleteSession}
                onDuplicate={handleDuplicateSession}
                onExport={handleExportSession}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateForm && (
        <SessionCreator
          onCancel={() => setShowCreateForm(false)}
          onSubmit={handleCreateSession}
        />
      )}
      
      <ExportDialog
        isOpen={exportDialog.open}
        onClose={() => setExportDialog({ open: false, session: null })}
        exportType="session"
        session={exportDialog.session || undefined}
      />

      {/* Footer */}
      <footer className="border-t bg-gray-50 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Powered by cutting-edge 2025 prompt optimization research
            </div>
            <div className="flex items-center gap-6">
              <Link 
                to="/about" 
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
              >
                Learn about the technology →
              </Link>
              <div className="text-xs text-gray-400">
                Version 1.0 • Open Source
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};