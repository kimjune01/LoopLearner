import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { optimizationService } from '../services/optimizationService';
import { generateDiff, getDiffLineClasses, getDiffStats } from '../utils/diffUtils';

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

export const OptimizationRunDetail: React.FC = () => {
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
        console.log('OptimizationRunDetail - received data:', run);
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return optimizationRun?.deployed ? '🚀' : '⚠️';
      case 'failed':
        return '❌';
      case 'running':
        return '⏳';
      case 'pending':
        return '🔄';
      default:
        return '❓';
    }
  };

  const getStatusColor = (status: string, deployed?: boolean) => {
    switch (status) {
      case 'completed':
        return deployed ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'pending':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const highlightParameters = (text: string) => {
    const parameterRegex = /(?<!\{)\{\{([^{}]+)\}\}(?!\})/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = parameterRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      parts.push(
        <span 
          key={match.index}
          className="inline-flex items-center px-2 py-1 mx-1 bg-purple-100 text-purple-800 rounded-md border border-purple-200 font-semibold text-sm"
          title={`Parameter: ${match[1]}`}
        >
          <span className="text-purple-600 mr-1">{'{{'}</span>
          {match[1]}
          <span className="text-purple-600 ml-1">{'}}'}</span>
        </span>
      );
      
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
            <div className="flex items-center gap-3 text-gray-600">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="text-lg">Loading optimization details...</span>
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
                Back
              </button>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">
                Optimization Run
              </h1>
            </div>
            
            {/* Status Badge */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border border-white/20 ${getStatusColor(optimizationRun.status, optimizationRun.deployed)} bg-white/15 backdrop-blur-sm`}>
              <span className="text-lg">{getStatusIcon(optimizationRun.status)}</span>
              <span className="text-white font-medium capitalize">{optimizationRun.status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Status Card */}
          <div className="card-elevated p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Run Details</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Started:</span>
                <span className="text-sm font-medium">{new Date(optimizationRun.started_at).toLocaleString()}</span>
              </div>
              {optimizationRun.completed_at && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Completed:</span>
                  <span className="text-sm font-medium">{new Date(optimizationRun.completed_at).toLocaleString()}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Datasets Used:</span>
                <span className="text-sm font-medium">{optimizationRun.datasets_used.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Test Cases:</span>
                <span className="text-sm font-medium">{optimizationRun.test_cases_used}</span>
              </div>
            </div>
          </div>

          {/* Performance Card */}
          <div className="card-elevated p-6 group hover:shadow-lg transition-all duration-200 cursor-pointer" 
               onClick={() => navigate(`${window.location.pathname}/stats`)}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Performance</h3>
              <div className="flex items-center gap-2 text-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <span className="text-sm font-medium">View Details</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Improvement:</span>
                <span className={`text-sm font-medium ${
                  (optimizationRun.performance_improvement || 0) > 0 ? 'text-green-600' : 'text-gray-600'
                }`}>
                  {optimizationRun.performance_improvement 
                    ? `+${optimizationRun.performance_improvement.toFixed(1)}%` 
                    : 'No improvement'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Deployed:</span>
                <span className={`text-sm font-medium ${optimizationRun.deployed ? 'text-green-600' : 'text-gray-600'}`}>
                  {optimizationRun.deployed ? 'Yes' : 'No'}
                </span>
              </div>
              {optimizationRun.baseline_prompt && optimizationRun.optimized_prompt && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Version:</span>
                  <span className="text-sm font-medium">
                    v{optimizationRun.baseline_prompt.version} → v{optimizationRun.optimized_prompt.version}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Progress Card */}
          <div className="card-elevated p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Progress</h3>
            <div className="space-y-3">
              {optimizationRun.current_step && (
                <div>
                  <span className="text-sm text-gray-600">Current Step:</span>
                  <p className="text-sm font-medium mt-1">{optimizationRun.current_step}</p>
                </div>
              )}
              {optimizationRun.error_message && (
                <div>
                  <span className="text-sm text-red-600">Error:</span>
                  <p className="text-sm text-red-700 mt-1">{optimizationRun.error_message}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Prompt Comparison - Main Feature */}
        {optimizationRun.baseline_prompt && optimizationRun.optimized_prompt && (() => {
          const diffLines = generateDiff(optimizationRun.baseline_prompt.content, optimizationRun.optimized_prompt.content);
          const diffStats = getDiffStats(diffLines);
          
          return (
            <div className="card-elevated p-8 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Prompt Changes</h3>
                
                {/* Diff Stats */}
                <div className="flex items-center gap-4 text-sm">
                  {diffStats.additions > 0 && (
                    <span className="inline-flex items-center gap-1 text-green-700 bg-green-100 px-3 py-1 rounded-full">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m6-6H6" />
                      </svg>
                      +{diffStats.additions} lines
                    </span>
                  )}
                  {diffStats.deletions > 0 && (
                    <span className="inline-flex items-center gap-1 text-red-700 bg-red-100 px-3 py-1 rounded-full">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
                      </svg>
                      -{diffStats.deletions} lines
                    </span>
                  )}
                  <span className="text-gray-600">
                    v{optimizationRun.baseline_prompt.version} → v{optimizationRun.optimized_prompt.version}
                  </span>
                </div>
              </div>
              
              {/* Unified Diff View */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 border-b px-4 py-3 flex items-center justify-between">
                  <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                    Prompt Diff
                  </h4>
                  <div className="text-sm text-gray-600">
                    {diffStats.hasChanges ? `${diffStats.total} lines` : 'No changes'}
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
              
              {/* Parameters Comparison */}
              {(optimizationRun.baseline_prompt.parameters?.length || optimizationRun.optimized_prompt.parameters?.length) && (
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Baseline Parameters */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      Before Parameters ({optimizationRun.baseline_prompt.parameters?.length || 0})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {optimizationRun.baseline_prompt.parameters?.map((param, i) => (
                        <span key={i} className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded font-mono">
                          {`{{${param}}}`}
                        </span>
                      )) || <span className="text-gray-500 text-sm">No parameters</span>}
                    </div>
                  </div>
                  
                  {/* Optimized Parameters */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      After Parameters ({optimizationRun.optimized_prompt.parameters?.length || 0})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {optimizationRun.optimized_prompt.parameters?.map((param, i) => (
                        <span key={i} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded font-mono">
                          {`{{${param}}}`}
                        </span>
                      )) || <span className="text-gray-500 text-sm">No parameters</span>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })()}


        {/* Progress Data */}
        {optimizationRun.progress_data && Object.keys(optimizationRun.progress_data).length > 0 && (
          <div className="card-elevated p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h3>
            <pre className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
              {JSON.stringify(optimizationRun.progress_data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default OptimizationRunDetail;