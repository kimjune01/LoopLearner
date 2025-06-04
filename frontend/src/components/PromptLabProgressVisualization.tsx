/**
 * Prompt Lab Progress Visualization Component
 * Displays comprehensive learning progress, optimization history, and convergence trends for a prompt lab
 */

import React, { useState, useEffect } from 'react';
import { promptLabService } from '../services/promptLabService';
import { optimizationService } from '../services/optimizationService';
import { api } from '../services/api';
import { generateDiff, getDiffLineClasses, getDiffStats } from '../utils/diffUtils';
import type { PromptLab } from '../types/promptLab';

// Types for visualization data
interface ProgressData {
  promptLab: PromptLab;
  optimizationHistory: OptimizationEvent[];
  confidenceHistory: ConfidencePoint[];
  performanceMetrics: PerformancePoint[];
  convergenceAssessment: ConvergenceData | null;
  feedbackSummary: FeedbackSummary;
}

interface OptimizationEvent {
  id: string;
  timestamp: string;
  triggerReason: string;
  improvementPercentage: number;
  deployed: boolean;
  promptVersion: number;
  feedbackBatchSize: number;
  status: 'completed' | 'failed' | 'pending';
  baseline_prompt?: {
    id: string;
    content: string;
    version: number;
    parameters?: string[];
  };
  optimized_prompt?: {
    id: string;
    content: string;
    version: number;
    parameters?: string[];
  };
}

interface ConfidencePoint {
  timestamp: string;
  userConfidence: number;
  systemConfidence: number;
  combinedConfidence: number;
  feedbackCount: number;
}

interface PerformancePoint {
  timestamp: string;
  promptVersion: number;
  performanceScore: number;
  f1Score?: number;
  perplexity?: number;
  humanRating?: number;
}

interface ConvergenceData {
  converged: boolean;
  confidenceScore: number;
  factors: {
    performancePlateau: boolean;
    confidenceConvergence: boolean;
    feedbackStability: boolean;
    minimumIterationsReached: boolean;
    minimumFeedbackReached: boolean;
  };
  recommendations: Array<{
    action: string;
    reason: string;
    priority: string;
  }>;
}

interface FeedbackSummary {
  totalFeedback: number;
  actionBreakdown: {
    accept: number;
    reject: number;
    edit: number;
    ignore: number;
  };
  recentTrend: 'improving' | 'stable' | 'declining';
  acceptanceRate: number;
}

interface PromptLabProgressVisualizationProps {
  promptLabId: string;
  onOptimizationTrigger?: () => void;
}

const PromptLabProgressVisualization: React.FC<PromptLabProgressVisualizationProps> = ({
  promptLabId,
  onOptimizationTrigger
}) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');
  const [runningOptimizations, setRunningOptimizations] = useState<any[]>([]);
  const [cancellingOptimization, setCancellingOptimization] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [selectedOptimization, setSelectedOptimization] = useState<any>(null);

  const loadProgressData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load prompt lab details
      const promptLab = await promptLabService.getPromptLab(promptLabId);
      
      // Load optimization history from real API
      const optimizationHistory = await loadOptimizationHistory(promptLabId, selectedTimeRange);
      
      // Load confidence evolution
      const confidenceHistory = await loadConfidenceHistory(promptLabId, selectedTimeRange);
      
      // Load performance metrics
      const performanceMetrics = await loadPerformanceMetrics(promptLabId, selectedTimeRange);
      
      // Load convergence assessment
      const convergenceAssessment = await loadConvergenceAssessment(promptLabId);
      
      // Load feedback summary
      const feedbackSummary = await loadFeedbackSummary(promptLabId, selectedTimeRange);
      
      // Load running optimizations
      try {
        const runningOpts = await optimizationService.getRunningOptimizations(promptLabId);
        console.log('PromptLabProgressVisualization - Running optimizations:', runningOpts);
        setRunningOptimizations(runningOpts);
      } catch (error) {
        console.error('Failed to load running optimizations:', error);
        setRunningOptimizations([]);
      }

      setProgressData({
        promptLab,
        optimizationHistory,
        confidenceHistory,
        performanceMetrics,
        convergenceAssessment,
        feedbackSummary
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load progress data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProgressData();
    // Start polling immediately when component loads
    const pollRunningOptimizations = async () => {
      try {
        const runningOpts = await optimizationService.getRunningOptimizations(promptLabId);
        console.log('PromptLabProgressVisualization - Polling running optimizations (initial):', runningOpts);
        setRunningOptimizations(runningOpts);
      } catch (error) {
        console.error('Failed to poll running optimizations:', error);
      }
    };
    pollRunningOptimizations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [promptLabId, selectedTimeRange]);

  // Poll for running optimizations
  useEffect(() => {
    const pollRunningOptimizations = async () => {
      try {
        const runningOpts = await optimizationService.getRunningOptimizations(promptLabId);
        console.log('PromptLabProgressVisualization - Polling running optimizations (interval):', runningOpts);
        setRunningOptimizations(runningOpts);
      } catch (error) {
        console.error('Failed to poll running optimizations:', error);
      }
    };

    // Start polling if there are running optimizations
    if (runningOptimizations.length > 0) {
      const interval = setInterval(pollRunningOptimizations, 2000); // Poll every 2 seconds
      setPollingInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [promptLabId, runningOptimizations.length]);

  // Real API data loading functions
  const loadOptimizationHistory = async (promptLabId: string, timeRange: string): Promise<OptimizationEvent[]> => {
    try {
      const optimizations = await optimizationService.getRunningOptimizations(promptLabId);
      // Get all optimizations, not just running ones
      const allOptimizations = await api.get(`/prompt-labs/${promptLabId}/optimizations/`);
      
      return allOptimizations.data.map((opt: any) => ({
        id: opt.id,
        timestamp: opt.started_at,
        triggerReason: opt.datasets_used?.length > 0 ? `Manual optimization with ${opt.datasets_used.length} dataset(s)` : 'Manual trigger',
        improvementPercentage: opt.performance_improvement || 0,
        deployed: opt.deployed,
        promptVersion: opt.optimized_prompt?.version || opt.baseline_prompt?.version || 1,
        feedbackBatchSize: opt.test_cases_used || 0,
        status: opt.status,
        baseline_prompt: opt.baseline_prompt,
        optimized_prompt: opt.optimized_prompt
      }));
    } catch (error) {
      console.error('Failed to load optimization history:', error);
      return [];
    }
  };

  const loadConfidenceHistory = async (promptLabId: string, timeRange: string): Promise<ConfidencePoint[]> => {
    // Mock confidence evolution data
    const points: ConfidencePoint[] = [];
    const startTime = Date.now() - (timeRange === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000);
    
    for (let i = 0; i < 20; i++) {
      const timestamp = new Date(startTime + (i * (Date.now() - startTime) / 20)).toISOString();
      const userConf = Math.min(0.95, 0.3 + (i * 0.05) + (Math.random() * 0.1 - 0.05));
      const systemConf = Math.min(0.95, 0.4 + (i * 0.04) + (Math.random() * 0.1 - 0.05));
      
      points.push({
        timestamp,
        userConfidence: userConf,
        systemConfidence: systemConf,
        combinedConfidence: (userConf + systemConf) / 2,
        feedbackCount: Math.floor(5 + i * 1.2)
      });
    }
    
    return points;
  };

  const loadPerformanceMetrics = async (promptLabId: string, timeRange: string): Promise<PerformancePoint[]> => {
    // Mock performance data
    return [
      {
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        promptVersion: 1,
        performanceScore: 0.72,
        f1Score: 0.68,
        perplexity: 0.75,
        humanRating: 0.73
      },
      {
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        promptVersion: 2,
        performanceScore: 0.87,
        f1Score: 0.84,
        perplexity: 0.89,
        humanRating: 0.88
      },
      {
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        promptVersion: 3,
        performanceScore: 0.94,
        f1Score: 0.92,
        perplexity: 0.95,
        humanRating: 0.95
      }
    ];
  };

  const loadConvergenceAssessment = async (promptLabId: string): Promise<ConvergenceData | null> => {
    try {
      // This would call the real convergence API
      const response = await api.get(`/prompt-labs/${promptLabId}/convergence/`);
      return response.data;
    } catch (err) {
      console.error('Failed to load convergence data:', err);
    }
    
    // Mock convergence data
    return {
      converged: false,
      confidenceScore: 0.75,
      factors: {
        performancePlateau: false,
        confidenceConvergence: true,
        feedbackStability: true,
        minimumIterationsReached: true,
        minimumFeedbackReached: true
      },
      recommendations: [
        {
          action: 'continue_optimization',
          reason: 'Performance still improving - continue optimization',
          priority: 'medium'
        },
        {
          action: 'monitor_performance',
          reason: 'Monitor for performance plateau in next 2-3 iterations',
          priority: 'low'
        }
      ]
    };
  };

  const loadFeedbackSummary = async (promptLabId: string, timeRange: string): Promise<FeedbackSummary> => {
    // Mock feedback summary
    return {
      totalFeedback: 45,
      actionBreakdown: {
        accept: 28,
        reject: 8,
        edit: 7,
        ignore: 2
      },
      recentTrend: 'improving',
      acceptanceRate: 0.78
    };
  };

  const getProgressBarWidth = (value: number, max = 1) => {
    return `${Math.min(100, (value / max) * 100)}%`;
  };

  const getProgressColor = (value: number, thresholds = { good: 0.8, okay: 0.6 }) => {
    if (value >= thresholds.good) return 'bg-green-500';
    if (value >= thresholds.okay) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <span className="text-green-600">📈</span>;
      case 'stable':
        return <span className="text-blue-600">➡️</span>;
      case 'declining':
        return <span className="text-red-600">📉</span>;
      default:
        return <span className="text-gray-600">➖</span>;
    }
  };

  const handleCancelOptimization = async (runId: string) => {
    try {
      setCancellingOptimization(runId);
      await optimizationService.cancelOptimization(runId);
      
      // Reload running optimizations to show updated status
      const runningOpts = await optimizationService.getRunningOptimizations(promptLabId);
      setRunningOptimizations(runningOpts);
    } catch (error: any) {
      console.error('Failed to cancel optimization:', error);
      // You could add a toast notification here
    } finally {
      setCancellingOptimization(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        <span className="ml-4 text-gray-600">Loading progress visualization...</span>
      </div>
    );
  }

  if (error || !progressData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Failed to Load Progress Data</h3>
        <p className="text-red-600 mb-4">{error || 'Unknown error occurred'}</p>
        <button
          onClick={loadProgressData}
          className="btn-primary"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Learning Progress</h2>
          <p className="text-gray-600">Prompt Lab: {progressData.promptLab.name}</p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Time range selector */}
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
          
          <button onClick={loadProgressData} className="btn-secondary">
            Refresh
          </button>
        </div>
      </div>

      {/* Running Optimizations */}
      {runningOptimizations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-blue-900 flex items-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              Active Optimization
            </h3>
          </div>
          
          <div className="space-y-4">
            {runningOptimizations.map((optimization) => (
              <div key={optimization.id} className="bg-white rounded-lg p-4 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {optimization.status}
                      </span>
                      <span className="text-sm text-gray-600">
                        Started: {new Date(optimization.started_at).toLocaleString()}
                      </span>
                    </div>
                    {optimization.current_step && (
                      <p className="text-sm font-medium text-gray-900 mb-2">
                        {optimization.current_step}
                      </p>
                    )}
                    
                    {/* Live Metrics */}
                    {optimization.progress_data && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                        <div className="bg-gray-50 rounded p-2">
                          <div className="text-xs text-gray-600">Cases Evaluated</div>
                          <div className="text-lg font-semibold text-gray-900">
                            {optimization.progress_data.evaluated_cases || 0}/{optimization.progress_data.total_cases || 0}
                          </div>
                        </div>
                        
                        <div className="bg-gray-50 rounded p-2">
                          <div className="text-xs text-gray-600">Prompt Variations</div>
                          <div className="text-lg font-semibold text-gray-900">
                            {optimization.progress_data.prompt_variations || 0}
                          </div>
                        </div>
                        
                        <div className="bg-green-50 rounded p-2">
                          <div className="text-xs text-gray-600">Best Improvement</div>
                          <div className="text-lg font-semibold text-green-700">
                            +{((optimization.progress_data.current_best_improvement || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                        
                        <div className="bg-purple-50 rounded p-2">
                          <div className="text-xs text-gray-600">Est. Time Remaining</div>
                          <div className="text-lg font-semibold text-purple-700">
                            {optimization.progress_data.estimated_time_remaining 
                              ? `~${Math.ceil(optimization.progress_data.estimated_time_remaining / 60)}m`
                              : 'Calculating...'}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Progress Bar */}
                    {optimization.progress_data && optimization.progress_data.total_cases > 0 && (
                      <div className="mt-3">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                            style={{ 
                              width: `${(optimization.progress_data.evaluated_cases / optimization.progress_data.total_cases) * 100}%` 
                            }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {optimization.error_message && (
                      <p className="text-sm text-red-600 mt-2">{optimization.error_message}</p>
                    )}
                  </div>
                  
                  <button
                    onClick={() => handleCancelOptimization(optimization.id)}
                    disabled={cancellingOptimization === optimization.id}
                    className="ml-4 px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                  >
                    {cancellingOptimization === optimization.id ? 'Cancelling...' : 'Cancel'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key metrics overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card-elevated p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Current Confidence</h3>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {progressData.confidenceHistory.length > 0 
              ? (progressData.confidenceHistory[progressData.confidenceHistory.length - 1].combinedConfidence * 100).toFixed(0)
              : 'N/A'}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${getProgressColor(
                progressData.confidenceHistory.length > 0 
                  ? progressData.confidenceHistory[progressData.confidenceHistory.length - 1].combinedConfidence
                  : 0
              )}`}
              style={{ 
                width: getProgressBarWidth(
                  progressData.confidenceHistory.length > 0 
                    ? progressData.confidenceHistory[progressData.confidenceHistory.length - 1].combinedConfidence
                    : 0
                )
              }}
            />
          </div>
        </div>

        <div className="card-elevated p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Performance Score</h3>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {progressData.performanceMetrics.length > 0
              ? (progressData.performanceMetrics[progressData.performanceMetrics.length - 1].performanceScore * 100).toFixed(0)
              : 'N/A'}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${getProgressColor(
                progressData.performanceMetrics.length > 0
                  ? progressData.performanceMetrics[progressData.performanceMetrics.length - 1].performanceScore
                  : 0
              )}`}
              style={{ 
                width: getProgressBarWidth(
                  progressData.performanceMetrics.length > 0
                    ? progressData.performanceMetrics[progressData.performanceMetrics.length - 1].performanceScore
                    : 0
                )
              }}
            />
          </div>
        </div>

        <div className="card-elevated p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Acceptance Rate</h3>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {((progressData.feedbackSummary.acceptanceRate || 0) * 100).toFixed(0)}%
          </div>
          <div className="flex items-center text-sm">
            {getTrendIcon(progressData.feedbackSummary.recentTrend)}
            <span className="ml-1 text-gray-600 capitalize">
              {progressData.feedbackSummary.recentTrend}
            </span>
          </div>
        </div>

        <div className="card-elevated p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Optimizations</h3>
          <div className="text-3xl font-bold text-gray-900 mb-2">
            {progressData.optimizationHistory.filter(opt => opt.deployed).length}
          </div>
          <div className="text-sm text-gray-600">
            {progressData.optimizationHistory.length} total runs
          </div>
        </div>
      </div>

      {/* Convergence status */}
      {progressData.convergenceAssessment && (
        <div className="card-elevated p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Convergence Assessment
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-gray-700">Convergence Status</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  progressData.convergenceAssessment.converged 
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {progressData.convergenceAssessment.converged ? 'Converged' : 'Learning'}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Confidence Score</span>
                  <span className="text-sm font-medium">
                    {(progressData.convergenceAssessment.confidenceScore * 100).toFixed(0)}%
                  </span>
                </div>
                
                {progressData.convergenceAssessment.factors && Object.entries(progressData.convergenceAssessment.factors).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                    </span>
                    <span className={`text-sm ${value ? 'text-green-600' : 'text-gray-400'}`}>
                      {value ? '✓' : '○'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Recommendations</h4>
              <div className="space-y-2">
                {progressData.convergenceAssessment.recommendations && progressData.convergenceAssessment.recommendations.map((rec, index) => (
                  <div key={index} className="border-l-4 border-purple-200 pl-3 py-2">
                    <div className="text-sm font-medium text-gray-900">{rec.action.replace(/_/g, ' ')}</div>
                    <div className="text-xs text-gray-600 mt-1">{rec.reason}</div>
                    <span className={`inline-block mt-1 px-2 py-1 rounded text-xs ${
                      rec.priority === 'high' 
                        ? 'bg-red-100 text-red-800'
                        : rec.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {rec.priority} priority
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Optimization history timeline */}
      <div className="card-elevated p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization History</h3>
        
        {progressData.optimizationHistory.length > 0 ? (
          <div className="space-y-4">
            {progressData.optimizationHistory.map((event, index) => (
              <div key={event.id} className="flex items-start space-x-4">
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  event.status === 'completed' 
                    ? event.deployed 
                      ? 'bg-green-100 text-green-600'
                      : 'bg-yellow-100 text-yellow-600'
                    : event.status === 'failed'
                    ? 'bg-red-100 text-red-600'
                    : 'bg-blue-100 text-blue-600'
                }`}>
                  {event.status === 'completed' && event.deployed && '🚀'}
                  {event.status === 'completed' && !event.deployed && '⚠️'}
                  {event.status === 'failed' && '❌'}
                  {event.status === 'pending' && '⏳'}
                </div>
                
                <div 
                  className="flex-grow min-w-0 cursor-pointer hover:bg-gray-50 rounded-lg p-2 -m-2 transition-colors"
                  onClick={() => window.location.href = `/prompt-labs/${promptLabId}/optimization/runs/${event.id}`}
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900 hover:text-purple-600">
                      Optimization #{progressData.optimizationHistory.length - index}
                    </h4>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-1">{event.triggerReason}</p>
                  
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>Version: {event.promptVersion}</span>
                      <span>Cases: {event.feedbackBatchSize} items</span>
                      {event.deployed && event.improvementPercentage > 0 && (
                        <span className="text-green-600 font-medium">
                          +{event.improvementPercentage.toFixed(1)}% improvement
                        </span>
                      )}
                      {/* Prompt Changes Available Indicator */}
                      {event.status === 'completed' && event.baseline_prompt && event.optimized_prompt && (
                        <span className="inline-flex items-center gap-1 text-purple-600 font-medium">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                          </svg>
                          Prompt changes
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {/* View Details Button */}
                      <button
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs bg-gray-100 text-gray-700 hover:bg-gray-200 px-2 py-1 rounded-md font-medium transition-colors"
                        title="View full details"
                      >
                        View Details
                      </button>
                      
                      {/* Quick View Changes Button */}
                      {event.status === 'completed' && event.baseline_prompt && event.optimized_prompt && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent navigation when clicking the button
                            setSelectedOptimization(event);
                            setShowDiffModal(true);
                          }}
                          className="text-xs bg-purple-100 text-purple-700 hover:bg-purple-200 px-2 py-1 rounded-md font-medium transition-colors"
                          title="Quick view prompt changes"
                        >
                          View Changes
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p>No optimization history available yet.</p>
            {onOptimizationTrigger && (
              <button
                onClick={onOptimizationTrigger}
                className="mt-4 btn-primary"
              >
                Trigger First Optimization
              </button>
            )}
          </div>
        )}
      </div>

      {/* Feedback breakdown */}
      <div className="card-elevated p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Analysis</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Action Breakdown</h4>
            <div className="space-y-3">
              {progressData.feedbackSummary.actionBreakdown && Object.entries(progressData.feedbackSummary.actionBreakdown).map(([action, count]) => {
                const percentage = progressData.feedbackSummary.totalFeedback > 0 
                  ? (count / progressData.feedbackSummary.totalFeedback) * 100 
                  : 0;
                const colorMap = {
                  accept: 'bg-green-500',
                  reject: 'bg-red-500',
                  edit: 'bg-yellow-500',
                  ignore: 'bg-gray-500'
                };
                
                return (
                  <div key={action} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${colorMap[action as keyof typeof colorMap]}`} />
                      <span className="text-sm text-gray-700 capitalize">{action}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium">{count}</span>
                      <span className="text-xs text-gray-500">({percentage.toFixed(0)}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Trend Analysis</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Feedback</span>
                <span className="text-sm font-medium">{progressData.feedbackSummary.totalFeedback}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Acceptance Rate</span>
                <span className="text-sm font-medium">
                  {((progressData.feedbackSummary.acceptanceRate || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Recent Trend</span>
                <div className="flex items-center space-x-1">
                  {getTrendIcon(progressData.feedbackSummary.recentTrend)}
                  <span className="text-sm font-medium capitalize">
                    {progressData.feedbackSummary.recentTrend}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Prompt Diff Modal */}
      {showDiffModal && selectedOptimization && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowDiffModal(false)}></div>
            
            <div className="relative w-full max-w-6xl rounded-lg bg-white shadow-xl">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Prompt Changes</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Optimization from {new Date(selectedOptimization.timestamp).toLocaleString()}
                      {selectedOptimization.improvementPercentage > 0 && (
                        <span className="ml-2 text-green-600 font-medium">
                          +{selectedOptimization.improvementPercentage.toFixed(1)}% improvement
                        </span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowDiffModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Deployment Status Banner */}
                {selectedOptimization.deployed ? (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-green-800 font-medium">
                        This optimization was deployed and is now the active prompt
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-yellow-800 font-medium">
                        This optimization was not deployed due to insufficient improvement (below 5% threshold)
                      </span>
                    </div>
                  </div>
                )}

                {/* Unified Diff View */}
                {(() => {
                  const diffLines = generateDiff(
                    selectedOptimization.baseline_prompt?.content || '',
                    selectedOptimization.optimized_prompt?.content || ''
                  );
                  const diffStats = getDiffStats(diffLines);
                  
                  return (
                    <div className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 border-b px-4 py-3 flex items-center justify-between">
                        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                          </svg>
                          Prompt Diff (v{selectedOptimization.baseline_prompt?.version} → v{selectedOptimization.optimized_prompt?.version})
                        </h4>
                        <div className="flex items-center gap-2 text-sm">
                          {diffStats.additions > 0 && (
                            <span className="text-green-700 bg-green-100 px-2 py-1 rounded">
                              +{diffStats.additions}
                            </span>
                          )}
                          {diffStats.deletions > 0 && (
                            <span className="text-red-700 bg-red-100 px-2 py-1 rounded">
                              -{diffStats.deletions}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="max-h-96 overflow-y-auto bg-white">
                        {diffStats.hasChanges ? (
                          diffLines.map((line, index) => {
                            const classes = getDiffLineClasses(line.type);
                            return (
                              <div
                                key={index}
                                className={`px-3 py-1 font-mono text-sm ${classes.lineClass}`}
                              >
                                <span className={`inline-block w-6 text-center font-semibold ${classes.prefixClass}`}>
                                  {classes.prefixSymbol}
                                </span>
                                <span className="ml-2">{line.content || '\u00A0'}</span>
                              </div>
                            );
                          })
                        ) : (
                          <div className="p-6 text-center text-gray-500">
                            <p>No differences detected between prompt versions.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}

                {/* Quick Summary of Changes */}
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
                  <div className="text-sm text-blue-800 space-y-1">
                    <p>
                      <strong>Length:</strong> {selectedOptimization.baseline_prompt?.content.length} → {selectedOptimization.optimized_prompt?.content.length} characters
                      {selectedOptimization.optimized_prompt?.content.length !== selectedOptimization.baseline_prompt?.content.length && (
                        <span className={`ml-2 font-medium ${
                          (selectedOptimization.optimized_prompt?.content.length || 0) > (selectedOptimization.baseline_prompt?.content.length || 0)
                            ? 'text-green-700' : 'text-red-700'
                        }`}>
                          ({(selectedOptimization.optimized_prompt?.content.length || 0) > (selectedOptimization.baseline_prompt?.content.length || 0) ? '+' : ''}{(selectedOptimization.optimized_prompt?.content.length || 0) - (selectedOptimization.baseline_prompt?.content.length || 0)})
                        </span>
                      )}
                    </p>
                    <p>
                      <strong>Performance:</strong> {selectedOptimization.improvementPercentage > 0 
                        ? `+${selectedOptimization.improvementPercentage.toFixed(1)}% improvement` 
                        : 'No significant improvement'
                      }
                    </p>
                    <p>
                      <strong>Status:</strong> {selectedOptimization.deployed ? 'Deployed and active' : 'Not deployed (below threshold)'}
                    </p>
                  </div>
                </div>

                {/* Parameters comparison if different */}
                {selectedOptimization.baseline_prompt?.parameters?.length !== selectedOptimization.optimized_prompt?.parameters?.length && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-blue-900 mb-3">Parameter Changes</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-blue-800 mb-2">Before:</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedOptimization.baseline_prompt?.parameters?.map((param: string, i: number) => (
                            <span key={i} className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                              {`{{${param}}}`}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-blue-800 mb-2">After:</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedOptimization.optimized_prompt?.parameters?.map((param: string, i: number) => (
                            <span key={i} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                              {`{{${param}}}`}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end mt-6 pt-4 border-t">
                  <button
                    onClick={() => setShowDiffModal(false)}
                    className="btn-secondary"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PromptLabProgressVisualization;