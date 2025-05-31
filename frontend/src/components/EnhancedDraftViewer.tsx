/**
 * Enhanced Draft Viewer Component
 * Displays email drafts with integrated reasoning feedback UI
 */

import React, { useState } from 'react';
import ReasoningFactors from './ReasoningFactors';
import type { EmailDraft } from '../types/email';

interface EnhancedDraftViewerProps {
  sessionId: string;
  drafts: EmailDraft[];
  onDraftAction: (draftId: string, action: 'accept' | 'reject' | 'edit' | 'ignore', reason?: string, editedContent?: string) => void;
  onRatingSubmitted?: () => void;
}

interface DraftCardProps {
  sessionId: string;
  draft: EmailDraft;
  onAction: (action: 'accept' | 'reject' | 'edit' | 'ignore', reason?: string, editedContent?: string) => void;
  onRatingSubmitted?: () => void;
}

const DraftCard: React.FC<DraftCardProps> = ({ sessionId, draft, onAction, onRatingSubmitted }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(draft.content);
  const [actionReason, setActionReason] = useState('');
  const [showReasoningFactors, setShowReasoningFactors] = useState(false);
  const [feedbackProvided, setFeedbackProvided] = useState(false);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    onAction('edit', actionReason || 'Edited response', editedContent);
    setIsEditing(false);
    setFeedbackProvided(true);
  };

  const handleCancelEdit = () => {
    setEditedContent(draft.content);
    setIsEditing(false);
  };

  const handleAction = (action: 'accept' | 'reject' | 'ignore') => {
    onAction(action, actionReason || `User ${action}ed the draft`);
    setFeedbackProvided(true);
  };

  const handleRatingSubmitted = () => {
    onRatingSubmitted?.();
    // Keep the reasoning factors open so user can continue rating
  };

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden">
      {/* Draft Header */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Draft Response
          </h3>
          <div className="flex items-center space-x-2">
            {feedbackProvided && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Feedback Provided
              </span>
            )}
            <button
              onClick={() => setShowReasoningFactors(!showReasoningFactors)}
              className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {showReasoningFactors ? 'Hide' : 'Show'} Reasoning
            </button>
          </div>
        </div>
      </div>

      {/* Draft Content */}
      <div className="p-6">
        {isEditing ? (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700">
              Edit Draft Response
            </label>
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full min-h-[200px] p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
              placeholder="Edit the draft response..."
            />
          </div>
        ) : (
          <div className="prose prose-gray max-w-none">
            <p className="whitespace-pre-wrap">{draft.content}</p>
          </div>
        )}

        {/* Action Reason Input */}
        <div className="mt-6 space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Feedback Reason (Optional)
          </label>
          <input
            type="text"
            placeholder="Why did you choose this action?"
            value={actionReason}
            onChange={(e) => setActionReason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-sm"
          />
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex flex-wrap gap-3">
          {isEditing ? (
            <>
              <button
                onClick={handleSaveEdit}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Save Edit
              </button>
              <button
                onClick={handleCancelEdit}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => handleAction('accept')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Accept
              </button>
              <button
                onClick={() => handleAction('reject')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Reject
              </button>
              <button
                onClick={handleEdit}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
              </button>
              <button
                onClick={() => handleAction('ignore')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-500 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
                </svg>
                Ignore
              </button>
            </>
          )}
        </div>
      </div>

      {/* Reasoning Factors Section */}
      {showReasoningFactors && (
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-6">
          <ReasoningFactors
            sessionId={sessionId}
            draftId={parseInt(draft.id)}
            onRatingSubmitted={handleRatingSubmitted}
          />
        </div>
      )}
    </div>
  );
};

export const EnhancedDraftViewer: React.FC<EnhancedDraftViewerProps> = ({ 
  sessionId,
  drafts, 
  onDraftAction, 
  onRatingSubmitted 
}) => {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Draft Responses ({drafts.length})
        </h2>
        <p className="text-sm text-gray-500">
          Review AI-generated responses and provide feedback on reasoning
        </p>
      </div>
      
      {drafts.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No drafts available</h3>
          <p className="mt-1 text-sm text-gray-500">Generate drafts for an email to see responses here.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {drafts.map(draft => (
            <DraftCard
              key={draft.id}
              sessionId={sessionId}
              draft={draft}
              onAction={(action, reason, editedContent) => onDraftAction(draft.id, action, reason, editedContent)}
              onRatingSubmitted={onRatingSubmitted}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default EnhancedDraftViewer;