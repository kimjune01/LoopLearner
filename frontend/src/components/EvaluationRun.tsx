/**
 * Evaluation Run Component
 * Allows users to run evaluations on datasets using specific prompts
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import { promptLabService } from '../services/promptLabService';
import type { EvaluationDataset, EvaluationRun as EvaluationRunType, EvaluationResult } from '../types/evaluation';
import type { PromptLab, SystemPrompt } from '../types/promptLab';

const EvaluationRun: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [promptLabs, setPromptLabs] = useState<PromptLab[]>([]);
  const [selectedPromptLab, setSelectedPromptLab] = useState<PromptLab | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<SystemPrompt | null>(null);
  const [running, setRunning] = useState(false);
  const [currentRun, setCurrentRun] = useState<EvaluationRunType | null>(null);
  const [results, setResults] = useState<EvaluationResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'setup' | 'results'>('setup');

  useEffect(() => {
    if (datasetId) {
      loadDataset();
    }
  }, [datasetId]);

  useEffect(() => {
    if (dataset?.prompt_lab_id) {
      loadPromptLabDetails(dataset.prompt_lab_id);
    }
  }, [dataset]);

  const loadDataset = async () => {
    try {
      const data = await evaluationService.getDataset(Number(datasetId));
      setDataset(data);
    } catch (err) {
      setError('Failed to load dataset');
      console.error('Error loading dataset:', err);
    }
  };

  const loadPromptLabDetails = async (promptLabId: string) => {
    try {
      const promptLabData = await promptLabService.getPromptLab(promptLabId);
      setSelectedPromptLab(promptLabData as any);
      
      // Set the active prompt
      if (promptLabData.active_prompt && promptLabData.active_prompt.id) {
        setSelectedPrompt({
          id: Number(promptLabData.active_prompt.id),
          prompt_lab: promptLabId,
          content: promptLabData.active_prompt.content || '',
          version: promptLabData.active_prompt.version || 1,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          parameters: promptLabData.active_prompt.parameters || [],
          performance_score: null
        });
      }
    } catch (err) {
      setError('Failed to load prompt lab details');
      console.error('Error loading prompt lab:', err);
    }
  };

  const handleRunEvaluation = async () => {
    if (!selectedPrompt) {
      setError('Please select a prompt to evaluate');
      return;
    }

    try {
      setRunning(true);
      setError(null);
      
      const run = await evaluationService.runEvaluation(Number(datasetId), selectedPrompt.id);
      setCurrentRun(run);
      
      // Load results if available
      if (run.id) {
        const runResults = await evaluationService.getEvaluationResults(run.id);
        setResults(runResults);
      }
      
      setViewMode('results');
    } catch (err) {
      setError('Failed to run evaluation');
      console.error('Error running evaluation:', err);
    } finally {
      setRunning(false);
    }
  };

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4">
          <p className="text-red-600">Loading dataset...</p>
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
          
          <h1 className="text-3xl font-bold text-gray-900">Run Evaluation</h1>
          <p className="mt-2 text-gray-600">Evaluate prompt performance on: {dataset.name}</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {viewMode === 'setup' && (
          <div className="space-y-6">
            {/* Prompt Lab & Prompt Info */}
            {dataset.prompt_lab_id ? (
              <div className="card-elevated p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Prompt Lab & Prompt</h2>
                
                {selectedPromptLab ? (
                  <div className="space-y-4">
                    <div>
                      <span className="text-sm font-medium text-gray-500">Prompt Lab:</span>
                      <span className="ml-2 text-sm text-gray-900">{selectedPromptLab.name}</span>
                    </div>
                    
                    {selectedPrompt ? (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Active Prompt (Version {selectedPrompt.version})
                        </label>
                        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                          <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-3">
                            {selectedPrompt.content}
                          </p>
                          {selectedPrompt.parameters && selectedPrompt.parameters.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {selectedPrompt.parameters.map((param) => (
                                <span
                                  key={param}
                                  className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800"
                                >
                                  {param}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">
                        No active prompt found in this prompt lab
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Loading prompt lab details...</p>
                )}
              </div>
            ) : (
              <div className="card-elevated p-6">
                <p className="text-sm text-gray-500">
                  This is a global dataset. Please select a prompt lab with an active prompt to run evaluation.
                </p>
              </div>
            )}

            {/* Dataset Info */}
            <div className="card-elevated p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Dataset Information</h2>
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium text-gray-500">Cases:</span>
                  <span className="ml-2 text-sm text-gray-900">{dataset.case_count}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Parameters:</span>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {dataset.parameters.map((param) => (
                      <span
                        key={param}
                        className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
                      >
                        {param}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Run Button */}
            <div className="flex justify-end">
              <button
                onClick={handleRunEvaluation}
                disabled={!selectedPrompt || running}
                className="btn-primary flex items-center space-x-2"
              >
                {running && (
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                <span>{running ? 'Running Evaluation...' : 'Run Evaluation'}</span>
              </button>
            </div>
          </div>
        )}

        {viewMode === 'results' && currentRun && (
          <div className="space-y-6">
            {/* Run Summary */}
            <div className="card-elevated p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Evaluation Results</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Overall Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {currentRun.overall_score ? (currentRun.overall_score * 100).toFixed(1) : '0'}%
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Cases Passed</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {currentRun.passed_cases || 0} / {currentRun.total_cases || 0}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Status</p>
                  <p className="text-2xl font-bold text-gray-900 capitalize">
                    {currentRun.status}
                  </p>
                </div>
              </div>

              {/* Individual Results */}
              {results.length > 0 && (
                <div>
                  <h3 className="text-md font-medium text-gray-900 mb-3">Case Results</h3>
                  <div className="space-y-3">
                    {results.map((result, index) => (
                      <div
                        key={result.case_id}
                        className={`p-4 rounded-lg border ${
                          result.passed 
                            ? 'bg-green-50 border-green-200' 
                            : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-gray-900">
                                Case #{index + 1}
                              </span>
                              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                result.passed 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {result.passed ? 'Passed' : 'Failed'}
                              </span>
                            </div>
                            
                            <div className="space-y-2 text-sm">
                              <div>
                                <span className="font-medium text-gray-700">Input:</span>
                                <p className="mt-1 text-gray-600">{result.input_text}</p>
                              </div>
                              <div>
                                <span className="font-medium text-gray-700">Expected:</span>
                                <p className="mt-1 text-gray-600">{result.expected_output}</p>
                              </div>
                              <div>
                                <span className="font-medium text-gray-700">Generated:</span>
                                <p className="mt-1 text-gray-600">{result.generated_output}</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="ml-4 text-right">
                            <p className="text-sm font-medium text-gray-500">Similarity</p>
                            <p className="text-lg font-bold text-gray-900">
                              {(result.similarity_score * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-between">
              <button
                onClick={() => setViewMode('setup')}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Run Another Evaluation
              </button>
              <button
                onClick={() => navigate(`/evaluation/datasets/${datasetId}`)}
                className="btn-primary"
              >
                Back to Dataset
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationRun;