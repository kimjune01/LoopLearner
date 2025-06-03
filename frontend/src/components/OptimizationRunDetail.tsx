/**
 * Optimization Run Detail Component
 * Shows detailed view of a single optimization run with real-time progress
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { optimizationService } from '../services/optimizationService';
import { promptLabService } from '../services/promptLabService';

interface OptimizationRunDetail {
  id: string;
  prompt_lab_id: string;
  prompt_lab_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  baseline_prompt: {
    id: number;
    version: number;
    content: string;
    parameters: string[];
    performance_score?: number;
  };
  candidate_prompts?: Array<{
    content: string;
    improvement: number;
    performance_score: number;
  }>;
  best_candidate?: {
    content: string;
    improvement: number;
    deployed: boolean;
    performance_score: number;
  };
  datasets_used: Array<{
    id: number;
    name: string;
    case_count: number;
  }>;
  test_cases_used: number;
  evaluation_results?: any;
  error_message?: string;
  progress?: {
    current_step: string;
    progress_percentage: number;
    steps_completed: string[];
    steps_remaining: string[];
  };
}

const OptimizationRunDetail: React.FC = () => {
  const { promptLabId, runId } = useParams<{ promptLabId: string; runId: string }>();
  const navigate = useNavigate();
  
  const [runDetail, setRunDetail] = useState<OptimizationRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState<string>('0s');
  const [runStartTime, setRunStartTime] = useState<Date | null>(null);
  const [showFullPrompt, setShowFullPrompt] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    if (runId) {
      loadRunDetail();
    }
  }, [runId]);

  // Auto-refresh for running optimizations
  useEffect(() => {
    if (runDetail?.status === 'running' || runDetail?.status === 'pending') {
      const interval = setInterval(() => {
        loadRunDetail();
      }, 3000); // Refresh every 3 seconds
      setRefreshInterval(interval as any);
      
      // Set start time if not already set
      if (!runStartTime && runDetail?.started_at) {
        setRunStartTime(new Date(runDetail.started_at));
      }
      
      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [runDetail?.status, runStartTime, refreshInterval]);

  // Update elapsed time for running optimizations
  useEffect(() => {
    if (runStartTime && (runDetail?.status === 'running' || runDetail?.status === 'pending')) {
      const interval = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - runStartTime.getTime()) / 1000);
        setElapsedTime(formatDuration(elapsed));
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [runStartTime, runDetail?.status]);

  const loadRunDetail = async () => {
    try {
      setLoading(true);
      const detail = await optimizationService.getOptimizationRun(runId!);
      setRunDetail(detail);
      setError(null);
    } catch (err: any) {
      setError('Failed to load optimization run details');
      console.error('Error loading optimization run:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': 
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'running':
        return (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current"></div>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const togglePromptView = (key: string) => {
    setShowFullPrompt(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  if (loading && !runDetail) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-8 py-12">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <span className="ml-3 text-lg text-gray-600">Loading optimization run...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !runDetail) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-8 py-12">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Optimization Run Not Found</h1>
            <p className="text-gray-600 mb-6">{error || 'The requested optimization run could not be found.'}</p>
            <Link 
              to={`/prompt-labs/${promptLabId}`}
              className="btn-primary"
            >
              Back to Prompt Lab
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                to={`/prompt-labs/${promptLabId}`}
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to {runDetail.prompt_lab_name}
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">
                Optimization Run #{runId?.slice(-8)}
              </h1>
            </div>
            
            {/* Status Badge */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${getStatusColor(runDetail.status)}`}>
              {getStatusIcon(runDetail.status)}
              <span className="font-semibold capitalize">{runDetail.status}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Progress Section */}
        {(runDetail.status === 'running' || runDetail.status === 'pending') && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
              Optimization in Progress
            </h2>
            
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Elapsed Time:</span>
                <span className="font-mono font-medium">{elapsedTime}</span>
              </div>
              
              {runDetail.progress && (
                <>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${runDetail.progress.progress_percentage}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Current Step:</span>
                    <span className="font-medium">{runDetail.progress.current_step}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Results Section */}
        {runDetail.status === 'completed' && runDetail.best_candidate && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Optimization Results
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  +{(runDetail.best_candidate.improvement * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-green-800">Performance Improvement</div>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {runDetail.test_cases_used}
                </div>
                <div className="text-sm text-blue-800">Test Cases Evaluated</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {runDetail.best_candidate.deployed ? 'Yes' : 'No'}
                </div>
                <div className="text-sm text-purple-800">New Prompt Deployed</div>
              </div>
            </div>

            {runDetail.best_candidate.deployed && (
              <div className="bg-gradient-to-r from-green-50 to-green-100 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-900 mb-3">New Optimized Prompt</h3>
                <div className="bg-white rounded border p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Version {runDetail.baseline_prompt.version + 1}
                    </span>
                    <button
                      onClick={() => togglePromptView('optimized')}
                      className="text-xs text-green-600 hover:text-green-800"
                    >
                      {showFullPrompt['optimized'] ? 'Show Less' : 'Show More'}
                    </button>
                  </div>
                  <div className={`text-sm text-gray-800 whitespace-pre-wrap ${
                    !showFullPrompt['optimized'] ? 'line-clamp-3' : ''
                  }`}>
                    {runDetail.best_candidate.content}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Section */}
        {runDetail.status === 'failed' && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-red-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Optimization Failed
            </h2>
            {runDetail.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{runDetail.error_message}</p>
              </div>
            )}
          </div>
        )}

        {/* Run Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Baseline Prompt */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Baseline Prompt</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Version:</span>
                <span className="font-medium">{runDetail.baseline_prompt.version}</span>
              </div>
              {runDetail.baseline_prompt.performance_score && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Performance Score:</span>
                  <span className="font-medium">{runDetail.baseline_prompt.performance_score.toFixed(3)}</span>
                </div>
              )}
              <div className="bg-gray-50 rounded border p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm font-medium text-gray-700">Content</span>
                  <button
                    onClick={() => togglePromptView('baseline')}
                    className="text-xs text-purple-600 hover:text-purple-800"
                  >
                    {showFullPrompt['baseline'] ? 'Show Less' : 'Show More'}
                  </button>
                </div>
                <div className={`text-sm text-gray-800 whitespace-pre-wrap ${
                  !showFullPrompt['baseline'] ? 'line-clamp-3' : ''
                }`}>
                  {runDetail.baseline_prompt.content}
                </div>
              </div>
            </div>
          </div>

          {/* Run Metadata */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Run Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Started:</span>
                <span className="font-medium">{new Date(runDetail.started_at).toLocaleString()}</span>
              </div>
              {runDetail.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Completed:</span>
                  <span className="font-medium">{new Date(runDetail.completed_at).toLocaleString()}</span>
                </div>
              )}
              {runDetail.duration_seconds && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="font-medium">{formatDuration(runDetail.duration_seconds)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Test Cases:</span>
                <span className="font-medium">{runDetail.test_cases_used}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Datasets Used:</span>
                <span className="font-medium">{runDetail.datasets_used.length}</span>
              </div>
            </div>

            {runDetail.datasets_used.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Evaluation Datasets</h4>
                <div className="space-y-2">
                  {runDetail.datasets_used.map(dataset => (
                    <div key={dataset.id} className="bg-gray-50 rounded p-3">
                      <div className="font-medium text-sm">{dataset.name}</div>
                      <div className="text-xs text-gray-600">{dataset.case_count} cases</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptimizationRunDetail;