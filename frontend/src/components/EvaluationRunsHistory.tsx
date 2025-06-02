/**
 * Enhanced Evaluation Runs History Component
 * Shows detailed evaluation run history with statistics and analysis
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import type { EvaluationDataset } from '../types/evaluation';

interface EvaluationRunSummary {
  id: number;
  status: string;
  overall_score: number | null;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
  avg_similarity_score: number;
  prompt_version: number;
  prompt_id: number;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
}


const EvaluationRunsHistory: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [runs, setRuns] = useState<EvaluationRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'started_at' | 'overall_score' | 'pass_rate'>('started_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showComparison, setShowComparison] = useState(false);
  const [compareRuns, setCompareRuns] = useState<Set<number>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (datasetId) {
      loadDataset();
      loadRuns();
    }
  }, [datasetId]);

  const loadDataset = async () => {
    try {
      const data = await evaluationService.getDataset(Number(datasetId));
      setDataset(data);
    } catch (err) {
      setError('Failed to load dataset');
      console.error('Error loading dataset:', err);
    }
  };

  const loadRuns = async () => {
    try {
      setLoading(true);
      const runsData = await evaluationService.getEvaluationRuns(Number(datasetId));
      // Map the API response to our interface
      const mappedRuns: EvaluationRunSummary[] = runsData.map(run => ({
        id: run.id!,
        status: run.status,
        overall_score: run.overall_score,
        total_cases: run.total_cases || 0,
        passed_cases: run.passed_cases || 0,
        failed_cases: run.failed_cases || 0,
        pass_rate: run.pass_rate || 0,
        avg_similarity_score: run.avg_similarity_score || 0,
        prompt_version: run.prompt_version || 1,
        prompt_id: run.prompt_id || 0,
        started_at: run.started_at,
        completed_at: run.completed_at,
        duration_seconds: run.duration_seconds || null
      }));
      setRuns(mappedRuns);
      setError(null);
    } catch (err) {
      setError('Failed to load evaluation runs');
      console.error('Error loading runs:', err);
    } finally {
      setLoading(false);
    }
  };


  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-800 bg-green-100';
      case 'running': return 'text-blue-800 bg-blue-100';
      case 'failed': return 'text-red-800 bg-red-100';
      case 'pending': return 'text-yellow-800 bg-yellow-100';
      default: return 'text-gray-800 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-800';
    if (score >= 0.7) return 'text-blue-800';
    if (score >= 0.5) return 'text-yellow-800';
    return 'text-red-800';
  };

  const sortedRuns = [...runs].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'started_at':
        aValue = new Date(a.started_at).getTime();
        bValue = new Date(b.started_at).getTime();
        break;
      case 'overall_score':
        aValue = a.overall_score || 0;
        bValue = b.overall_score || 0;
        break;
      case 'pass_rate':
        aValue = a.pass_rate;
        bValue = b.pass_rate;
        break;
      default:
        return 0;
    }

    return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
  });

  const toggleCompareRun = (runId: number) => {
    const newCompareRuns = new Set(compareRuns);
    if (newCompareRuns.has(runId)) {
      newCompareRuns.delete(runId);
    } else if (newCompareRuns.size < 3) {
      newCompareRuns.add(runId);
    }
    setCompareRuns(newCompareRuns);
  };

  const handleDeleteAllRuns = async () => {
    if (!datasetId) return;
    
    try {
      setIsDeleting(true);
      const result = await evaluationService.deleteAllEvaluationRuns(Number(datasetId));
      // Reload the runs after deletion
      await loadRuns();
      setShowDeleteConfirm(false);
      // Show success message (could add a toast notification here)
      console.log(`Deleted ${result.deleted_count} runs`);
    } catch (err) {
      setError('Failed to delete evaluation runs');
      console.error('Error deleting runs:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4">
          <p className="text-gray-600">Loading evaluation runs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/evaluation/datasets/${datasetId}`)}
            className="mb-4 text-sm text-gray-600 hover:text-gray-900 flex items-center"
          >
            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dataset
          </button>
          
          <h1 className="text-3xl font-bold text-gray-900">Evaluation Runs History</h1>
          <p className="mt-2 text-gray-600">
            {dataset ? `Dataset: ${dataset.name}` : 'Loading...'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Controls */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
              >
                <option value="started_at">Date</option>
                <option value="overall_score">Score</option>
                <option value="pass_rate">Pass Rate</option>
              </select>
            </div>
            
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
            
            {sortedRuns.length > 0 && (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="text-sm text-red-600 hover:text-red-800 font-medium flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Remove All History
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {compareRuns.size > 0 && (
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="btn-primary text-sm"
              >
                Compare Runs ({compareRuns.size})
              </button>
            )}
            
            <button
              onClick={() => navigate(`/evaluation/datasets/${datasetId}/run`)}
              className="btn-primary"
            >
              Run New Evaluation
            </button>
          </div>
        </div>

        {/* Runs List */}
        <div className="space-y-4">
          {sortedRuns.length === 0 ? (
            <div className="card-elevated p-8 text-center">
              <p className="text-gray-500">No evaluation runs found.</p>
            </div>
          ) : (
            sortedRuns.map((run) => (
              <div
                key={run.id}
                className="card-elevated p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        Run #{run.id} (Prompt v{run.prompt_version})
                      </h3>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                      {showComparison && (
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={compareRuns.has(run.id)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleCompareRun(run.id);
                            }}
                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                          />
                          <span className="ml-2 text-sm text-gray-600">Compare</span>
                        </label>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-gray-500">Overall Score</p>
                        <p className={`text-lg font-semibold ${getScoreColor(run.overall_score || 0)}`}>
                          {run.overall_score ? (run.overall_score * 100).toFixed(1) : '0'}%
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Pass Rate</p>
                        <p className={`text-lg font-semibold ${getScoreColor(run.pass_rate / 100)}`}>
                          {run.pass_rate.toFixed(1)}%
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Cases</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {run.passed_cases}/{run.total_cases}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Avg Similarity</p>
                        <p className={`text-lg font-semibold ${getScoreColor(run.avg_similarity_score)}`}>
                          {(run.avg_similarity_score * 100).toFixed(1)}%
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Duration</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {formatDuration(run.duration_seconds)}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Started</p>
                        <p className="text-sm text-gray-700">
                          {formatDate(run.started_at)}
                        </p>
                      </div>
                    </div>

                    {/* Progress bar for pass rate */}
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${run.pass_rate}%` }}
                      />
                    </div>
                  </div>

                  <div className="ml-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/evaluation/datasets/${datasetId}/runs/${run.id}`);
                      }}
                      className="text-sm bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition-colors"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3 text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 mt-4">
                  Delete All Evaluation Runs?
                </h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    This will permanently delete all {sortedRuns.length} evaluation runs for this dataset. This action cannot be undone.
                  </p>
                </div>
                <div className="items-center px-4 py-3">
                  <button
                    onClick={handleDeleteAllRuns}
                    disabled={isDeleting}
                    className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isDeleting ? (
                      <svg className="animate-spin h-5 w-5 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      'Delete'
                    )}
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={isDeleting}
                    className="px-4 py-2 bg-gray-300 text-gray-700 text-base font-medium rounded-md w-24 hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default EvaluationRunsHistory;