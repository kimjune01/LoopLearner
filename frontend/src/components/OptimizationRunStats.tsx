import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { optimizationService } from '../services/optimizationService';

interface OptimizationRun {
  id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  datasets_used: number[];
  test_cases_used: number;
  performance_improvement: number | null;
  deployed: boolean;
  error_message: string;
  current_step: string;
  progress_data: any;
  detailed_metrics: any;
  candidate_metrics: any[];
  statistical_analysis: any;
  threshold_analysis: any;
  cost_analysis: any;
  baseline_prompt: {
    id: string;
    content: string;
    version: number;
    parameters?: string[];
  } | null;
  optimized_prompt: {
    id: string;
    content: string;
    version: number;
    parameters?: string[];
  } | null;
}

export const OptimizationRunStats: React.FC = () => {
  const { runId, promptLabId } = useParams<{ runId: string; promptLabId?: string }>();
  const navigate = useNavigate();
  const [optimizationRun, setOptimizationRun] = useState<OptimizationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOptimizationRun = async () => {
      if (!runId) return;
      
      try {
        setLoading(true);
        const run = await optimizationService.getOptimizationRun(runId);
        console.log('OptimizationRunStats - received data:', run);
        setOptimizationRun(run);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load optimization run');
      } finally {
        setLoading(false);
      }
    };

    loadOptimizationRun();
  }, [runId]);

  const formatDuration = (start: string, end: string | null, status: string) => {
    if (!end) {
      if (status === 'completed') {
        return 'Completed (duration unknown)';
      }
      return 'In progress...';
    }
    const duration = new Date(end).getTime() - new Date(start).getTime();
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getMetricsFromOptimizationRun = (optimizationRun: OptimizationRun) => {
    const progressData = optimizationRun.progress_data || {};
    const detailedMetrics = optimizationRun.detailed_metrics || {};
    const statisticalAnalysis = optimizationRun.statistical_analysis || {};
    const costAnalysis = optimizationRun.cost_analysis || {};
    const thresholdAnalysis = optimizationRun.threshold_analysis || {};
    
    // Extract metrics from various sources
    const metrics = {
      // Progress tracking
      total_cases: progressData.total_cases || 0,
      evaluated_cases: progressData.evaluated_cases || 0,
      prompt_variations: progressData.prompt_variations || 0,
      current_best_improvement: progressData.current_best_improvement || 0,
      
      // Performance metrics from detailed_metrics
      f1_score_baseline: detailedMetrics.baseline_metrics?.component_metrics?.f1_score || null,
      f1_score_optimized: detailedMetrics.best_candidate_metrics?.component_metrics?.f1_score || null,
      perplexity_baseline: detailedMetrics.baseline_metrics?.component_metrics?.perplexity_score || null,
      perplexity_optimized: detailedMetrics.best_candidate_metrics?.component_metrics?.perplexity_score || null,
      human_feedback_baseline: detailedMetrics.baseline_metrics?.component_metrics?.human_feedback_score || null,
      human_feedback_optimized: detailedMetrics.best_candidate_metrics?.component_metrics?.human_feedback_score || null,
      
      // Component improvements
      f1_improvement: detailedMetrics.component_scores_comparison?.f1_improvement || null,
      perplexity_improvement: detailedMetrics.component_scores_comparison?.perplexity_improvement || null,
      human_feedback_improvement: detailedMetrics.component_scores_comparison?.human_feedback_improvement || null,
      
      // Summary metrics
      total_candidates_tested: detailedMetrics.summary?.total_candidates_tested || 0,
      baseline_performance_score: detailedMetrics.summary?.baseline_performance_score || null,
      best_performance_score: detailedMetrics.summary?.best_performance_score || null,
      optimization_time_seconds: detailedMetrics.summary?.optimization_time_seconds || null,
      
      // Statistical analysis
      p_value: statisticalAnalysis.p_value || null,
      confidence_level: statisticalAnalysis.confidence_level || null,
      statistical_significance: statisticalAnalysis.statistical_significance || null,
      sample_size: statisticalAnalysis.sample_size || null,
      
      // Cost analysis
      total_cost_usd: costAnalysis.total_cost_usd || null,
      iterations_performed: costAnalysis.iterations_performed || null,
      evaluations_performed: costAnalysis.evaluations_performed || null,
      roi_percentage: costAnalysis.roi_percentage || null,
      
      // Threshold analysis
      deployment_decision: thresholdAnalysis.deployment_decision || null,
      deployment_reason: thresholdAnalysis.deployment_reason || null,
      min_improvement_threshold: thresholdAnalysis.min_improvement_threshold || null,
      improvement_met: thresholdAnalysis.improvement_met || null,
      confidence_met: thresholdAnalysis.confidence_met || null,
    };
    
    return metrics;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
            <div className="flex items-center gap-3 text-gray-600">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="text-lg">Loading optimization statistics...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !optimizationRun) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
            <div className="max-w-md mx-auto text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Optimization Run Not Found</h2>
              <p className="text-gray-600 mb-6">{error || 'The requested optimization run could not be found.'}</p>
              <button 
                onClick={() => navigate(-1)}
                className="btn-primary"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const metrics = getMetricsFromOptimizationRun(optimizationRun);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => navigate(-1)}
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Run Details
              </button>
              <div className="w-px h-6 bg-white/30"></div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Performance Statistics
                </h1>
                <p className="text-white/80 text-sm">
                  Detailed metrics for optimization run #{optimizationRun.id} - Status: {optimizationRun.status}
                </p>
              </div>
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors duration-200"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Key Performance Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Performance Improvement */}
          <div className="card-elevated p-6 text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {optimizationRun.performance_improvement 
                ? `+${optimizationRun.performance_improvement.toFixed(1)}%` 
                : metrics.current_best_improvement 
                  ? `+${metrics.current_best_improvement.toFixed(1)}%`
                  : 'N/A'
              }
            </div>
            <div className="text-sm text-gray-600">
              {optimizationRun.status === 'completed' ? 'Final Improvement' : 'Current Best Improvement'}
            </div>
          </div>

          {/* Cases Processed */}
          <div className="card-elevated p-6 text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {metrics.evaluated_cases || optimizationRun.test_cases_used}
              {metrics.total_cases > 0 && ` / ${metrics.total_cases}`}
            </div>
            <div className="text-sm text-gray-600">
              {optimizationRun.status === 'completed' ? 'Total Cases Used' : 'Cases Processed'}
            </div>
          </div>

          {/* Candidates Tested */}
          <div className="card-elevated p-6 text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {metrics.total_candidates_tested || metrics.prompt_variations || 0}
            </div>
            <div className="text-sm text-gray-600">Prompt Candidates Tested</div>
          </div>

          {/* Cost or Time */}
          <div className="card-elevated p-6 text-center">
            <div className="text-3xl font-bold text-orange-600 mb-2">
              {metrics.total_cost_usd 
                ? `$${metrics.total_cost_usd.toFixed(2)}` 
                : formatDuration(optimizationRun.started_at, optimizationRun.completed_at, optimizationRun.status)
              }
            </div>
            <div className="text-sm text-gray-600">
              {metrics.total_cost_usd ? 'Optimization Cost' : 'Duration'}
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Overall Performance */}
          <div className="card-elevated p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Performance Summary
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border">
                <span className="text-sm font-medium text-purple-800">Overall Improvement</span>
                <span className="text-2xl font-bold text-purple-700">
                  +{optimizationRun.performance_improvement?.toFixed(1) || '0.0'}%
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Baseline Prompt Version</span>
                <span className="text-lg font-bold text-gray-800">
                  v{optimizationRun.baseline_prompt?.version || 'N/A'}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm font-medium text-green-800">Optimized Prompt Version</span>
                <span className="text-lg font-bold text-green-700">
                  v{optimizationRun.optimized_prompt?.version || 'N/A'}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-blue-800">Deployment Status</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  optimizationRun.deployed 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-orange-100 text-orange-800'
                }`}>
                  {optimizationRun.deployed ? 'Deployed' : 'Not Deployed'}
                </span>
              </div>
            </div>
          </div>

          {/* Optimization Details */}
          <div className="card-elevated p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Optimization Details
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium text-blue-800">Test Cases Used</span>
                <span className="text-lg font-bold text-blue-700">
                  {optimizationRun.test_cases_used}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-indigo-50 rounded-lg">
                <span className="text-sm font-medium text-indigo-800">Datasets Used</span>
                <span className="text-lg font-bold text-indigo-700">
                  {optimizationRun.datasets_used.length}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Started</span>
                <span className="text-sm font-medium text-gray-800">
                  {new Date(optimizationRun.started_at).toLocaleString()}
                </span>
              </div>
              
              {optimizationRun.completed_at && (
                <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                  <span className="text-sm font-medium text-green-800">Completed</span>
                  <span className="text-sm font-medium text-green-700">
                    {new Date(optimizationRun.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Process Details & Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Process Metrics */}
          <div className="card-elevated p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              Optimization Process
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className={`text-sm font-medium px-2 py-1 rounded ${
                  optimizationRun.status === 'completed' ? 'bg-green-100 text-green-800' :
                  optimizationRun.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  optimizationRun.status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {optimizationRun.status.charAt(0).toUpperCase() + optimizationRun.status.slice(1)}
                </span>
              </div>
              
              {optimizationRun.current_step && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Current Step:</span>
                  <span className="text-sm font-medium text-right max-w-xs">{optimizationRun.current_step}</span>
                </div>
              )}
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Cases Evaluated:</span>
                <span className="text-sm font-medium">
                  {metrics.evaluated_cases || optimizationRun.test_cases_used}
                  {metrics.total_cases > 0 && ` / ${metrics.total_cases}`}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Candidates Tested:</span>
                <span className="text-sm font-medium">{metrics.total_candidates_tested || metrics.prompt_variations || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Datasets Used:</span>
                <span className="text-sm font-medium">{optimizationRun.datasets_used.length}</span>
              </div>
              
              {metrics.iterations_performed !== null && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Optimization Iterations:</span>
                  <span className="text-sm font-medium">{metrics.iterations_performed}</span>
                </div>
              )}
            </div>
          </div>

          {/* Analysis & Cost */}
          <div className="card-elevated p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Analysis & Economics
            </h3>
            <div className="space-y-4">
              {/* Cost Information */}
              {metrics.total_cost_usd !== null && (
                <>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Cost:</span>
                    <span className="text-sm font-medium text-green-600">${metrics.total_cost_usd.toFixed(2)}</span>
                  </div>
                  {metrics.roi_percentage !== null && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">ROI:</span>
                      <span className={`text-sm font-medium ${metrics.roi_percentage > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {metrics.roi_percentage > 0 ? '+' : ''}{metrics.roi_percentage.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </>
              )}
              
              {/* Statistical Significance */}
              {metrics.p_value !== null && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Statistical Significance:</span>
                  <span className={`text-sm font-medium ${metrics.p_value > 0.05 ? 'text-red-600' : 'text-green-600'}`}>
                    p = {metrics.p_value.toFixed(4)}
                  </span>
                </div>
              )}
              
              {metrics.confidence_level !== null && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Confidence Level:</span>
                  <span className="text-sm font-medium">{(metrics.confidence_level * 100).toFixed(1)}%</span>
                </div>
              )}
              
              {/* Deployment Analysis */}
              {metrics.deployment_decision && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Deployment Decision:</span>
                  <span className={`text-sm font-medium px-2 py-1 rounded ${
                    metrics.deployment_decision === 'deployed' ? 'bg-green-100 text-green-800' :
                    metrics.deployment_decision === 'not_deployed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {metrics.deployment_decision.replace('_', ' ')}
                  </span>
                </div>
              )}
              
              {metrics.deployment_reason && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <span className="text-xs text-gray-600 uppercase tracking-wide">Deployment Reason:</span>
                  <p className="text-sm text-gray-800 mt-1">{metrics.deployment_reason}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Data Availability Status */}
        <div className="card-elevated p-6 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Data Availability
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
                Object.keys(optimizationRun.detailed_metrics || {}).length > 0 ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span className="text-xs text-gray-600">Detailed Metrics</span>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
                Object.keys(optimizationRun.statistical_analysis || {}).length > 0 ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span className="text-xs text-gray-600">Statistical Analysis</span>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
                Object.keys(optimizationRun.cost_analysis || {}).length > 0 ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span className="text-xs text-gray-600">Cost Analysis</span>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
                (optimizationRun.candidate_metrics || []).length > 0 ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span className="text-xs text-gray-600">Candidate Metrics</span>
            </div>
          </div>
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">Note:</span> This optimization run shows limited detailed metrics. 
              This may be because it was completed before comprehensive metrics collection was implemented, 
              or detailed analysis is still being processed.
            </p>
          </div>
        </div>

        {/* Raw Data (if available) */}
        {(optimizationRun.progress_data && Object.keys(optimizationRun.progress_data).length > 0) && (
          <div className="card-elevated p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Available Raw Data
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-96">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                {JSON.stringify({
                  progress_data: optimizationRun.progress_data,
                  evaluation_results: optimizationRun.evaluation_results,
                  basic_info: {
                    status: optimizationRun.status,
                    performance_improvement: optimizationRun.performance_improvement,
                    test_cases_used: optimizationRun.test_cases_used,
                    datasets_used: optimizationRun.datasets_used,
                    deployed: optimizationRun.deployed
                  }
                }, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OptimizationRunStats;