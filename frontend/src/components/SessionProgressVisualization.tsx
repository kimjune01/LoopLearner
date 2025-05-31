/**
 * Session Progress Visualization Component
 * Displays comprehensive learning progress, optimization history, and convergence trends for a session
 */

import React, { useState, useEffect } from 'react';
import { sessionService } from '../services/sessionService';
import type { Session } from '../types/session';

// Types for visualization data
interface ProgressData {
  session: Session;
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

interface SessionProgressVisualizationProps {
  sessionId: string;
  onOptimizationTrigger?: () => void;
}

const SessionProgressVisualization: React.FC<SessionProgressVisualizationProps> = ({
  sessionId,
  onOptimizationTrigger
}) => {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');

  useEffect(() => {
    loadProgressData();
  }, [sessionId, selectedTimeRange]);

  const loadProgressData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load session details
      const session = await sessionService.getSession(sessionId);
      
      // Load optimization history (mock for now - would be real API calls)
      const optimizationHistory = await loadOptimizationHistory(sessionId, selectedTimeRange);
      
      // Load confidence evolution
      const confidenceHistory = await loadConfidenceHistory(sessionId, selectedTimeRange);
      
      // Load performance metrics
      const performanceMetrics = await loadPerformanceMetrics(sessionId, selectedTimeRange);
      
      // Load convergence assessment
      const convergenceAssessment = await loadConvergenceAssessment(sessionId);
      
      // Load feedback summary
      const feedbackSummary = await loadFeedbackSummary(sessionId, selectedTimeRange);

      setProgressData({
        session,
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

  // Mock data loading functions - these would call real APIs
  const loadOptimizationHistory = async (sessionId: string, timeRange: string): Promise<OptimizationEvent[]> => {
    // Mock data for demonstration
    return [
      {
        id: '1',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        triggerReason: 'High negative feedback ratio',
        improvementPercentage: 15.3,
        deployed: true,
        promptVersion: 2,
        feedbackBatchSize: 12,
        status: 'completed'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        triggerReason: 'Manual trigger',
        improvementPercentage: 8.7,
        deployed: true,
        promptVersion: 3,
        feedbackBatchSize: 8,
        status: 'completed'
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        triggerReason: 'Consistent quality issues',
        improvementPercentage: 3.2,
        deployed: false,
        promptVersion: 3,
        feedbackBatchSize: 15,
        status: 'completed'
      }
    ];
  };

  const loadConfidenceHistory = async (sessionId: string, timeRange: string): Promise<ConfidencePoint[]> => {
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

  const loadPerformanceMetrics = async (sessionId: string, timeRange: string): Promise<PerformancePoint[]> => {
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

  const loadConvergenceAssessment = async (sessionId: string): Promise<ConvergenceData | null> => {
    try {
      // This would call the real convergence API
      const response = await fetch(`/api/sessions/${sessionId}/convergence/`);
      if (response.ok) {
        return await response.json();
      }
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

  const loadFeedbackSummary = async (sessionId: string, timeRange: string): Promise<FeedbackSummary> => {
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
          <p className="text-gray-600">Session: {progressData.session.name}</p>
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
            {(progressData.feedbackSummary.acceptanceRate * 100).toFixed(0)}%
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
                
                {Object.entries(progressData.convergenceAssessment.factors).map(([key, value]) => (
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
                {progressData.convergenceAssessment.recommendations.map((rec, index) => (
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
                
                <div className="flex-grow min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      Optimization #{progressData.optimizationHistory.length - index}
                    </h4>
                    <span className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-1">{event.triggerReason}</p>
                  
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>Version: {event.promptVersion}</span>
                    <span>Feedback: {event.feedbackBatchSize} items</span>
                    {event.deployed && event.improvementPercentage > 0 && (
                      <span className="text-green-600 font-medium">
                        +{event.improvementPercentage.toFixed(1)}% improvement
                      </span>
                    )}
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
              {Object.entries(progressData.feedbackSummary.actionBreakdown).map(([action, count]) => {
                const percentage = (count / progressData.feedbackSummary.totalFeedback) * 100;
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
                  {(progressData.feedbackSummary.acceptanceRate * 100).toFixed(1)}%
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
    </div>
  );
};

export default SessionProgressVisualization;