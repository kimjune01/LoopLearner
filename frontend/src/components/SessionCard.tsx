import React, { useState, useEffect } from 'react';
import type { Session, SessionStats } from '../types/session';
import { sessionService } from '../services/sessionService';

interface SessionCardProps {
  session: Session;
  onView: (sessionId: string) => void;
  onEdit: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onDuplicate: (sessionId: string) => void;
  onExport: (sessionId: string) => void;
}

export const SessionCard: React.FC<SessionCardProps> = ({
  session,
  onView,
  onEdit,
  onDelete,
  onDuplicate,
  onExport
}) => {
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [showActions, setShowActions] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const sessionStats = await sessionService.getSessionStats(session.id);
        setStats(sessionStats);
      } catch (err) {
        console.error('Failed to load session stats:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [session.id]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = () => {
    if (session.optimization_iterations > 0) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Learning
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Idle
      </span>
    );
  };

  const getProgressIndicator = () => {
    if (!stats) return null;
    
    const progress = Math.min((stats.emails.total_processed / 10) * 100, 100); // Assume 10 emails is "complete"
    return (
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Progress</span>
          <span>{stats.emails.total_processed} emails</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-purple-600 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="card-elevated p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{session.name}</h3>
          {getStatusBadge()}
        </div>
        <div className="relative">
          <button
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200"
            onClick={() => setShowActions(!showActions)}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>
          {showActions && (
            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-48 py-1">
              <button 
                onClick={() => onView(session.id)}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                View Session
              </button>
              <button 
                onClick={() => onEdit(session.id)}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Edit Details
              </button>
              <button 
                onClick={() => onDuplicate(session.id)}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Duplicate
              </button>
              <button 
                onClick={() => onExport(session.id)}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Export Data
              </button>
              <hr className="my-1" />
              <button 
                onClick={() => onDelete(session.id)}
                className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      <div className="text-gray-600 text-sm mb-4 flex-1">
        {session.description || 'No description provided'}
      </div>

      {/* Metadata */}
      <div className="text-xs text-gray-500 mb-4 space-y-1">
        <div className="flex justify-between">
          <span>Created</span>
          <span>{formatDate(session.created_at)}</span>
        </div>
        <div className="flex justify-between">
          <span>Last Updated</span>
          <span>{formatDate(session.updated_at)}</span>
        </div>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="text-center text-gray-500 italic py-4">Loading stats...</div>
      ) : stats ? (
        <div className="mb-4">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-lg font-bold text-purple-600">{stats.prompts.current_version}</div>
              <div className="text-xs text-gray-500">Prompt Version</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{stats.optimization_iterations}</div>
              <div className="text-xs text-gray-500">Optimizations</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{stats.feedback.total_collected}</div>
              <div className="text-xs text-gray-500">Feedback</div>
            </div>
          </div>
          
          {getProgressIndicator()}
          
          {stats.prompts.current_performance_score && (
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg mt-3">
              <span className="text-sm text-blue-700 font-medium">Performance</span>
              <span className="text-sm font-bold text-blue-700">
                {(stats.prompts.current_performance_score * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-red-500 text-sm py-4">Failed to load stats</div>
      )}

      {/* Footer */}
      <button 
        className="w-full mt-auto py-3 px-4 bg-gray-50 hover:bg-purple-600 hover:text-white text-gray-700 font-medium rounded-lg transition-all duration-200 border border-gray-200 hover:border-purple-600"
        onClick={() => onView(session.id)}
      >
        Open Session →
      </button>
    </div>
  );
};