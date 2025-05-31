/**
 * Reasoning Factors Component
 * Displays and allows rating of AI-generated reasoning factors for draft responses
 */

import React, { useState, useEffect } from 'react';
import { reasoningService } from '../services/reasoningService';
import type { ReasoningFactor, DraftReasoningFactors, ReasonRating } from '../types/reasoning';

interface ReasoningFactorsProps {
  sessionId: string;
  draftId: number;
  onRatingSubmitted?: () => void;
}

const ReasoningFactors: React.FC<ReasoningFactorsProps> = ({ 
  sessionId, 
  draftId, 
  onRatingSubmitted 
}) => {
  const [data, setData] = useState<DraftReasoningFactors | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReasons, setSelectedReasons] = useState<Set<number>>(new Set());
  const [bulkRating, setBulkRating] = useState<boolean | null>(null); // true = like, false = dislike, null = mixed
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadReasoningFactors();
  }, [sessionId, draftId]);

  const loadReasoningFactors = async () => {
    try {
      setLoading(true);
      const reasoningData = await reasoningService.getReasoningFactors(sessionId, draftId);
      setData(reasoningData);
      setError(null);
    } catch (err) {
      setError('Failed to load reasoning factors');
      console.error('Error loading reasoning factors:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickRate = async (reasonId: number, liked: boolean) => {
    try {
      await reasoningService.quickRateReason(sessionId, reasonId, {
        liked,
        create_feedback: true
      });
      
      // Reload to get updated stats
      await loadReasoningFactors();
      onRatingSubmitted?.();
    } catch (err) {
      console.error('Error rating reason:', err);
      setError('Failed to rate reasoning factor');
    }
  };

  const toggleReasonSelection = (reasonId: number) => {
    const newSelection = new Set(selectedReasons);
    if (newSelection.has(reasonId)) {
      newSelection.delete(reasonId);
    } else {
      newSelection.add(reasonId);
    }
    setSelectedReasons(newSelection);
  };

  const selectAllReasons = () => {
    if (!data) return;
    
    if (selectedReasons.size === data.reasoning_factors.length) {
      setSelectedReasons(new Set());
    } else {
      setSelectedReasons(new Set(data.reasoning_factors.map(r => r.id)));
    }
  };

  const handleBulkAction = async (action: 'accept' | 'reject' | 'rate') => {
    if (!data || selectedReasons.size === 0) return;
    
    try {
      setSubmitting(true);
      
      if (action === 'accept') {
        await reasoningService.bulkAcceptReasons(sessionId, draftId, 'Bulk accepted selected reasoning factors');
      } else if (action === 'reject') {
        await reasoningService.bulkRejectReasons(sessionId, draftId, 'Bulk rejected selected reasoning factors');
      } else if (action === 'rate' && bulkRating !== null) {
        const reasonRatings: ReasonRating = {};
        selectedReasons.forEach(reasonId => {
          reasonRatings[reasonId.toString()] = bulkRating;
        });
        
        await reasoningService.bulkRateReasons(sessionId, draftId, {
          action: 'accept',
          reason: `Bulk ${bulkRating ? 'liked' : 'disliked'} selected reasoning factors`,
          reason_ratings: reasonRatings
        });
      }
      
      // Clear selections and reload
      setSelectedReasons(new Set());
      setBulkRating(null);
      await loadReasoningFactors();
      onRatingSubmitted?.();
      
    } catch (err) {
      console.error('Error in bulk action:', err);
      setError('Failed to submit bulk rating');
    } finally {
      setSubmitting(false);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        <span className="ml-3 text-gray-600">Loading reasoning factors...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-red-800">{error}</span>
        </div>
        <button
          onClick={loadReasoningFactors}
          className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!data || data.reasoning_factors.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p>No reasoning factors available for this draft.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Reasoning Factors ({data.reasoning_factors.length})
        </h3>
        
        <span className="text-sm text-gray-500">
          Rate the AI's reasoning for this response
        </span>
      </div>

      {/* Bulk Actions */}
      {data.reasoning_factors.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={selectedReasons.size === data.reasoning_factors.length}
                onChange={selectAllReasons}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                Select all ({selectedReasons.size} of {data.reasoning_factors.length} selected)
              </span>
            </label>
            
            <div className="text-xs text-gray-500">
              Bulk actions for selected factors
            </div>
          </div>
          
          {selectedReasons.size > 0 && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleBulkAction('accept')}
                disabled={submitting}
                className="inline-flex items-center px-3 py-1 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 disabled:opacity-50"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Accept All ({selectedReasons.size})
              </button>
              
              <button
                onClick={() => handleBulkAction('reject')}
                disabled={submitting}
                className="inline-flex items-center px-3 py-1 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 disabled:opacity-50"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Reject All ({selectedReasons.size})
              </button>
              
              <div className="flex items-center space-x-2">
                <select
                  value={bulkRating === null ? '' : bulkRating.toString()}
                  onChange={(e) => setBulkRating(e.target.value === '' ? null : e.target.value === 'true')}
                  className="text-sm border-gray-300 rounded-md"
                >
                  <option value="">Rate as...</option>
                  <option value="true">👍 Like</option>
                  <option value="false">👎 Dislike</option>
                </select>
                
                <button
                  onClick={() => handleBulkAction('rate')}
                  disabled={submitting || bulkRating === null}
                  className="inline-flex items-center px-3 py-1 border border-purple-300 text-sm font-medium rounded-md text-purple-700 bg-purple-50 hover:bg-purple-100 disabled:opacity-50"
                >
                  Rate ({selectedReasons.size})
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Reasoning Factors List */}
      <div className="space-y-4">
        {data.reasoning_factors.map((factor) => (
          <ReasoningFactorCard
            key={factor.id}
            factor={factor}
            selected={selectedReasons.has(factor.id)}
            onToggleSelection={() => toggleReasonSelection(factor.id)}
            onQuickRate={handleQuickRate}
          />
        ))}
      </div>
    </div>
  );
};

// Individual Reasoning Factor Card Component
interface ReasoningFactorCardProps {
  factor: ReasoningFactor;
  selected: boolean;
  onToggleSelection: () => void;
  onQuickRate: (reasonId: number, liked: boolean) => void;
}

const ReasoningFactorCard: React.FC<ReasoningFactorCardProps> = ({
  factor,
  selected,
  onToggleSelection,
  onQuickRate
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRatingColor = (likes: number, dislikes: number) => {
    const total = likes + dislikes;
    if (total === 0) return 'text-gray-400';
    if (likes > dislikes) return 'text-green-600';
    if (dislikes > likes) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className={`card-elevated p-4 ${selected ? 'ring-2 ring-purple-500 bg-purple-50' : ''}`}>
      <div className="flex items-start space-x-3">
        {/* Selection Checkbox */}
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelection}
          className="mt-1 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
        />
        
        {/* Factor Content */}
        <div className="flex-1 min-w-0">
          <p className="text-gray-900 leading-relaxed">{factor.text}</p>
          
          {/* Metadata */}
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Confidence Badge */}
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(factor.confidence)}`}>
                {(factor.confidence * 100).toFixed(0)}% confidence
              </span>
              
              {/* Rating Stats */}
              {factor.rating_stats.total_ratings > 0 && (
                <div className={`text-sm ${getRatingColor(factor.rating_stats.likes, factor.rating_stats.dislikes)}`}>
                  👍 {factor.rating_stats.likes} · 👎 {factor.rating_stats.dislikes}
                </div>
              )}
            </div>
            
            {/* Quick Rating Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onQuickRate(factor.id, true)}
                className="inline-flex items-center p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                title="Like this reasoning"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
              </button>
              
              <button
                onClick={() => onQuickRate(factor.id, false)}
                className="inline-flex items-center p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                title="Dislike this reasoning"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2M17 4H19a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReasoningFactors;