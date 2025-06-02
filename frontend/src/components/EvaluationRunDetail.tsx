/**
 * Evaluation Run Detail Component
 * Shows detailed view of a single evaluation run with individual case inspection
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import type { EvaluationDataset } from '../types/evaluation';

interface DetailedRunResult {
  run_id: number;
  dataset_id: number;
  dataset_name: string;
  prompt_info: {
    id: number;
    version: number;
    content: string;
    parameters: string[];
    performance_score: number | null;
  };
  status: string;
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  statistics: {
    total_cases: number;
    passed_cases: number;
    failed_cases: number;
    pass_rate: number;
    avg_similarity_score: number;
    median_similarity_score: number;
    min_similarity_score: number;
    max_similarity_score: number;
    score_distribution: {
      excellent: number;
      good: number;
      fair: number;
      poor: number;
    };
  };
  results: Array<{
    case_id: number;
    case_number: number;
    input_text: string;
    expected_output: string;
    generated_output: string;
    similarity_score: number;
    passed: boolean;
    details: any;
    case_context: any;
    performance_tier: string;
  }>;
}

const EvaluationRunDetail: React.FC = () => {
  const { datasetId, runId } = useParams<{ datasetId: string; runId: string }>();
  const navigate = useNavigate();
  
  const [runDetail, setRunDetail] = useState<DetailedRunResult | null>(null);
  const [selectedCase, setSelectedCase] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterTier, setFilterTier] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'case_number' | 'similarity_score' | 'performance_tier'>('case_number');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [runStartTime, setRunStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState<string>('0s');
  const [modelInfo, setModelInfo] = useState<{provider: string; model: string} | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  const [showFullPrompt, setShowFullPrompt] = useState<{ [key: number]: boolean }>({});

  useEffect(() => {
    if (runId) {
      loadRunDetail();
      loadModelInfo();
    }
  }, [runId]);

  // Auto-refresh for running evaluations
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
      return () => {}; // Return cleanup function for consistency
    }
  }, [runDetail?.status]);

  // Timer effect for tracking elapsed time
  useEffect(() => {
    let interval: number;
    
    if ((runDetail?.status === 'running' || runDetail?.status === 'pending') && runStartTime) {
      interval = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - runStartTime.getTime()) / 1000);
        setElapsedTime(formatElapsedTime(elapsed));
      }, 1000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [runDetail?.status, runStartTime]);

  const loadRunDetail = async () => {
    try {
      // Don't show loading state on refresh
      if (!runDetail) {
        setLoading(true);
      }
      const data = await evaluationService.getDetailedEvaluationResults(Number(runId));
      setRunDetail(data);
      
      // Update start time if just started
      if (!runStartTime && data.started_at) {
        setRunStartTime(new Date(data.started_at));
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load run details');
      console.error('Error loading run details:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadModelInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/llm/status/');
      if (response.ok) {
        const data = await response.json();
        setModelInfo({
          provider: data.provider || 'Unknown',
          model: data.model || 'Unknown'
        });
      }
    } catch (err) {
      // Fallback to default if API not available
      setModelInfo({
        provider: 'Ollama',
        model: 'llama3.2:3b'
      });
    }
  };

  const formatElapsedTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}m ${secs}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${mins}m`;
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

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'excellent': return 'bg-green-100 text-green-800 border-green-200';
      case 'good': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'fair': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'poor': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-800';
    if (score >= 0.7) return 'text-blue-800';
    if (score >= 0.5) return 'text-yellow-800';
    return 'text-red-800';
  };

  const filteredAndSortedResults = runDetail ? runDetail.results
    .filter(result => filterTier === 'all' || result.performance_tier === filterTier)
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'case_number':
          aValue = a.case_number;
          bValue = b.case_number;
          break;
        case 'similarity_score':
          aValue = a.similarity_score;
          bValue = b.similarity_score;
          break;
        case 'performance_tier':
          const tierOrder = { excellent: 4, good: 3, fair: 2, poor: 1 };
          aValue = tierOrder[a.performance_tier as keyof typeof tierOrder] || 0;
          bValue = tierOrder[b.performance_tier as keyof typeof tierOrder] || 0;
          break;
        default:
          return 0;
      }
      
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    }) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4">
          <p className="text-gray-600">Loading run details...</p>
        </div>
      </div>
    );
  }

  if (error || !runDetail) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4">
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error || 'Run not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <button
              onClick={() => navigate(`/evaluation/datasets/${datasetId}/runs`)}
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
            >
              <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Run History
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={() => navigate(`/evaluation/datasets/${datasetId}`)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Back to Dataset
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Run #{runDetail.run_id} Details
              </h1>
              <p className="mt-2 text-gray-600">
                Dataset: {runDetail.dataset_name} • Prompt v{runDetail.prompt_info.version}
              </p>
            </div>
            <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(runDetail.status)}`}>
              {runDetail.status}
            </span>
          </div>
        </div>

        {/* Running Status Display */}
        {(runDetail.status === 'running' || runDetail.status === 'pending') && (
          <div className="mb-8 card-elevated p-6 bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <div>
                  <h3 className="text-lg font-medium text-blue-900">Evaluation Running</h3>
                  <p className="text-sm text-blue-700">
                    Processing {runDetail.statistics?.total_cases || 0} evaluation cases...
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-900">{elapsedTime}</div>
                <div className="text-sm text-blue-700">Elapsed Time</div>
              </div>
            </div>
            
            {modelInfo && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-800">Provider:</span>
                    <div className="text-blue-900">{modelInfo.provider}</div>
                  </div>
                  <div>
                    <span className="font-medium text-blue-800">Model:</span>
                    <div className="text-blue-900">{modelInfo.model}</div>
                  </div>
                  <div>
                    <span className="font-medium text-blue-800">Dataset:</span>
                    <div className="text-blue-900">{runDetail.dataset_name}</div>
                  </div>
                  <div>
                    <span className="font-medium text-blue-800">Progress:</span>
                    <div className="text-blue-900">
                      {runDetail.results.length} / {runDetail.statistics?.total_cases || 0} cases
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Progress Bar */}
            <div className="mt-4">
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${(runDetail.results.length / (runDetail.statistics?.total_cases || 1)) * 100}%` 
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Overview Statistics */}
        <div className="mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-6 shadow">
            <p className="text-sm font-medium text-gray-500">Overall Score</p>
            <p className="text-3xl font-bold text-gray-900">
              {runDetail.overall_score ? (runDetail.overall_score * 100).toFixed(1) : '0'}%
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow">
            <p className="text-sm font-medium text-gray-500">Pass Rate</p>
            <p className="text-3xl font-bold text-gray-900">
              {runDetail.statistics.pass_rate.toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500">
              {runDetail.statistics.passed_cases}/{runDetail.statistics.total_cases} cases
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow">
            <p className="text-sm font-medium text-gray-500">Median Score</p>
            <p className="text-3xl font-bold text-gray-900">
              {(runDetail.statistics.median_similarity_score * 100).toFixed(1)}%
            </p>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow">
            <p className="text-sm font-medium text-gray-500">Duration</p>
            <p className="text-3xl font-bold text-gray-900">
              {formatDuration(runDetail.duration_seconds)}
            </p>
            <p className="text-sm text-gray-500">
              {formatDate(runDetail.started_at)}
            </p>
          </div>
        </div>

        {/* Performance Distribution */}
        <div className="mb-8 bg-white rounded-lg p-6 shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Distribution</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">
                {runDetail.statistics.score_distribution.excellent}
              </p>
              <p className="text-sm text-gray-600">Excellent (≥90%)</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">
                {runDetail.statistics.score_distribution.good}
              </p>
              <p className="text-sm text-gray-600">Good (70-89%)</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-600">
                {runDetail.statistics.score_distribution.fair}
              </p>
              <p className="text-sm text-gray-600">Fair (50-69%)</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">
                {runDetail.statistics.score_distribution.poor}
              </p>
              <p className="text-sm text-gray-600">Poor (&lt;50%)</p>
            </div>
          </div>
        </div>

        {/* Prompt Information */}
        <div className="mb-8 bg-white rounded-lg p-6 shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Prompt Details</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Version {runDetail.prompt_info.version}</p>
              <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                <pre className="text-sm text-gray-900 whitespace-pre-wrap font-mono">
                  {runDetail.prompt_info.content}
                </pre>
              </div>
            </div>
            {runDetail.prompt_info.parameters && runDetail.prompt_info.parameters.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-500">Parameters</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {runDetail.prompt_info.parameters.map((param) => (
                    <span
                      key={param}
                      className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800"
                    >
                      {param}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Case Results */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">
                Individual Case Results 
                {(runDetail.status === 'running' || runDetail.status === 'pending') && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    ({runDetail.results.length} completed)
                  </span>
                )}
              </h3>
              <div className="flex items-center space-x-4">
                {/* Filter */}
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium text-gray-700">Filter:</label>
                  <select
                    value={filterTier}
                    onChange={(e) => setFilterTier(e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 text-sm"
                  >
                    <option value="all">All ({runDetail.results.length})</option>
                    <option value="excellent">Excellent ({runDetail.statistics.score_distribution.excellent})</option>
                    <option value="good">Good ({runDetail.statistics.score_distribution.good})</option>
                    <option value="fair">Fair ({runDetail.statistics.score_distribution.fair})</option>
                    <option value="poor">Poor ({runDetail.statistics.score_distribution.poor})</option>
                  </select>
                </div>

                {/* Sort */}
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium text-gray-700">Sort:</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 text-sm"
                  >
                    <option value="case_number">Case Number</option>
                    <option value="similarity_score">Similarity Score</option>
                    <option value="performance_tier">Performance Tier</option>
                  </select>
                  <button
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            {runDetail.results.length === 0 && (runDetail.status === 'running' || runDetail.status === 'pending') ? (
              <div className="text-center py-12">
                <svg className="animate-spin h-8 w-8 text-purple-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-gray-600">Waiting for results to come in...</p>
                <p className="text-sm text-gray-500 mt-2">Results will appear here as cases are processed</p>
              </div>
            ) : runDetail.results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No results available for this evaluation run.
              </div>
            ) : (
              <div className="space-y-4">
                {filteredAndSortedResults.map((result) => (
                <div
                  key={result.case_id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedCase === result.case_id ? 'ring-2 ring-purple-500' : ''
                  } ${getTierColor(result.performance_tier)}`}
                  onClick={() => setSelectedCase(selectedCase === result.case_id ? null : result.case_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          Case #{result.case_number}
                        </span>
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          result.performance_tier === 'excellent' ? 'bg-green-100 text-green-800' :
                          result.performance_tier === 'good' ? 'bg-blue-100 text-blue-800' :
                          result.performance_tier === 'fair' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {result.performance_tier}
                        </span>
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          result.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {result.passed ? 'Passed' : 'Failed'}
                        </span>
                      </div>
                      
                      {selectedCase !== result.case_id ? (
                        <div className="text-sm text-gray-600">
                          {/* Show parameters if available */}
                          {result.case_context && Object.keys(result.case_context).length > 0 ? (
                            <div className="mb-2">
                              <strong>Parameters:</strong>
                              <div className="mt-1 flex flex-wrap gap-2">
                                {Object.entries(result.case_context).map(([key, value]) => (
                                  <span
                                    key={key}
                                    className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs"
                                  >
                                    <span className="font-medium text-gray-700">{key}:</span>
                                    <span className="ml-1 text-gray-600">{String(value)}</span>
                                  </span>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="truncate">
                              <strong>Input:</strong> {result.input_text.substring(0, 100)}...
                            </p>
                          )}
                          <p className="truncate">
                            <strong>Expected:</strong> {result.expected_output.substring(0, 100)}...
                          </p>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-700 space-y-4 mt-4">
                          {/* Parameters Section */}
                          {result.case_context && Object.keys(result.case_context).length > 0 && (
                            <div>
                              <strong className="block text-gray-900 mb-1">Parameters:</strong>
                              <div className="p-3 bg-purple-50 rounded border border-purple-200">
                                <div className="grid grid-cols-1 gap-2">
                                  {Object.entries(result.case_context).map(([key, value]) => (
                                    <div key={key} className="flex items-start">
                                      <span className="font-medium text-purple-800 min-w-[120px]">{key}:</span>
                                      <span className="text-purple-700 ml-2">{String(value)}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Input Prompt Section with Toggle */}
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <strong className="text-gray-900">Input Prompt:</strong>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setShowFullPrompt(prev => ({ ...prev, [result.case_id]: !prev[result.case_id] }));
                                }}
                                className="text-xs text-purple-600 hover:text-purple-800 font-medium"
                              >
                                {showFullPrompt[result.case_id] ? 'Hide' : 'Show'} Full Prompt
                              </button>
                            </div>
                            {showFullPrompt[result.case_id] ? (
                              <div className="p-3 bg-white rounded border">
                                <p className="whitespace-pre-wrap font-mono text-xs">{result.input_text}</p>
                              </div>
                            ) : (
                              <div className="p-3 bg-gray-50 rounded border">
                                <p className="text-gray-600 italic text-sm">
                                  Full prompt hidden. Click "Show Full Prompt" to expand.
                                </p>
                              </div>
                            )}
                          </div>
                          
                          <div>
                            <strong className="block text-gray-900 mb-1">Expected Output:</strong>
                            <div className="p-3 bg-green-50 rounded border">
                              <p className="whitespace-pre-wrap">{result.expected_output}</p>
                            </div>
                          </div>
                          
                          <div>
                            <strong className="block text-gray-900 mb-1">Generated Output:</strong>
                            <div className="p-3 bg-blue-50 rounded border">
                              <p className="whitespace-pre-wrap">{result.generated_output}</p>
                            </div>
                          </div>


                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4 text-right">
                      <p className="text-sm font-medium text-gray-500">Similarity</p>
                      <p className={`text-lg font-bold ${getScoreColor(result.similarity_score)}`}>
                        {(result.similarity_score * 100).toFixed(1)}%
                      </p>
                      <div className="mt-2 w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full"
                          style={{ width: `${result.similarity_score * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {selectedCase === result.case_id ? 'Click to collapse' : 'Click to expand'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              
                {filteredAndSortedResults.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No cases match the selected filter.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationRunDetail;