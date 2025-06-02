/**
 * Evaluation Dataset Detail Component
 * Shows dataset details, cases, and allows case management
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import { promptLabService } from '../services/promptLabService';
import { API_BASE_URL } from '../services/api';
import CaseWithOutputSelection from './CaseWithOutputSelection';
import type { EvaluationDataset, EvaluationCase, CasePreview } from '../types/evaluation';

const EvaluationDatasetDetail: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cases' | 'auto-synthesize' | 'curated-generation' | 'import-data'>('cases');
  const [isEditingName, setIsEditingName] = useState(false);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [selectedCases, setSelectedCases] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (datasetId) {
      loadDataset();
      loadCases();
    }
  }, [datasetId]);

  const loadDataset = async () => {
    try {
      const data = await evaluationService.getDataset(Number(datasetId));
      setDataset(data);
      setEditedName(data.name);
      setEditedDescription(data.description);
    } catch (err) {
      setError('Failed to load dataset');
      console.error('Error loading dataset:', err);
    }
  };

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await evaluationService.getCases(Number(datasetId));
      setCases(data);
      setError(null);
    } catch (err) {
      setError('Failed to load cases');
      console.error('Error loading cases:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCase = async (caseId: number) => {
    if (!window.confirm('Are you sure you want to delete this case?')) {
      return;
    }

    try {
      await evaluationService.deleteCase(Number(datasetId), caseId);
      await loadCases();
    } catch (err) {
      setError('Failed to delete case');
      console.error('Error deleting case:', err);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedCases.size === 0) return;
    
    if (!window.confirm(`Are you sure you want to delete ${selectedCases.size} cases?`)) {
      return;
    }

    try {
      await Promise.all(
        Array.from(selectedCases).map(caseId =>
          evaluationService.deleteCase(Number(datasetId), caseId)
        )
      );
      setSelectedCases(new Set());
      await loadCases();
    } catch (err) {
      setError('Failed to delete cases');
      console.error('Error deleting cases:', err);
    }
  };

  const toggleCaseSelection = (caseId: number) => {
    const newSelection = new Set(selectedCases);
    if (newSelection.has(caseId)) {
      newSelection.delete(caseId);
    } else {
      newSelection.add(caseId);
    }
    setSelectedCases(newSelection);
  };

  const selectAllCases = () => {
    if (selectedCases.size === cases.length) {
      setSelectedCases(new Set());
    } else {
      setSelectedCases(new Set(cases.map(c => c.id)));
    }
  };

  const handleSaveName = async () => {
    if (!dataset || editedName.trim() === dataset.name) {
      setIsEditingName(false);
      setEditedName(dataset?.name || '');
      return;
    }

    try {
      await evaluationService.updateDataset(dataset.id, { name: editedName.trim() });
      await loadDataset();
      setIsEditingName(false);
    } catch (err) {
      setError('Failed to update dataset name');
      console.error('Error updating dataset name:', err);
      setEditedName(dataset.name);
      setIsEditingName(false);
    }
  };

  const handleSaveDescription = async () => {
    if (!dataset || editedDescription.trim() === dataset.description) {
      setIsEditingDescription(false);
      setEditedDescription(dataset?.description || '');
      return;
    }

    try {
      await evaluationService.updateDataset(dataset.id, { description: editedDescription.trim() });
      await loadDataset();
      setIsEditingDescription(false);
    } catch (err) {
      setError('Failed to update dataset description');
      console.error('Error updating dataset description:', err);
      setEditedDescription(dataset.description);
      setIsEditingDescription(false);
    }
  };

  const handleCancelNameEdit = () => {
    setIsEditingName(false);
    setEditedName(dataset?.name || '');
  };

  const handleCancelDescriptionEdit = () => {
    setIsEditingDescription(false);
    setEditedDescription(dataset?.description || '');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="mx-auto max-w-7xl px-4">
          <p className="text-red-600">Dataset not found</p>
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
            onClick={() => {
              if (dataset?.prompt_lab_id) {
                navigate(`/prompt-labs/${dataset.prompt_lab_id}?tab=evaluations`);
              } else {
                navigate('/evaluation/datasets');
              }
            }}
            className="mb-4 text-sm text-gray-600 hover:text-gray-900 flex items-center"
          >
            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {dataset?.prompt_lab_id ? 'Back to Prompt Lab' : 'Back to Datasets'}
          </button>
          
          <div className="flex items-start justify-between">
            <div className="flex-1 max-w-4xl">
              {/* Title with inline editing */}
              <div className="flex items-center group">
                {isEditingName ? (
                  <div className="flex items-center space-x-2 w-full">
                    <input
                      type="text"
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      className="text-3xl font-bold text-gray-900 border-0 border-b-2 border-purple-500 focus:outline-none focus:border-purple-600 bg-transparent flex-1"
                      autoFocus
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') handleSaveName();
                        if (e.key === 'Escape') handleCancelNameEdit();
                      }}
                    />
                    <button
                      onClick={handleSaveName}
                      className="text-green-600 hover:text-green-700"
                      title="Save"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <button
                      onClick={handleCancelNameEdit}
                      className="text-gray-400 hover:text-gray-600"
                      title="Cancel"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <>
                    <h1 className="text-3xl font-bold text-gray-900">{dataset.name}</h1>
                    <button
                      onClick={() => setIsEditingName(true)}
                      className="ml-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity"
                      title="Edit name"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  </>
                )}
              </div>

              {/* Description with inline editing */}
              <div className="mt-2 flex items-start group">
                {isEditingDescription ? (
                  <div className="flex items-start space-x-2 w-full">
                    <textarea
                      value={editedDescription}
                      onChange={(e) => setEditedDescription(e.target.value)}
                      className="text-gray-600 border border-gray-300 rounded-md focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 flex-1 p-2"
                      rows={3}
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.metaKey) handleSaveDescription();
                        if (e.key === 'Escape') handleCancelDescriptionEdit();
                      }}
                    />
                    <div className="flex flex-col space-y-1 pt-2">
                      <button
                        onClick={handleSaveDescription}
                        className="text-green-600 hover:text-green-700"
                        title="Save"
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                      <button
                        onClick={handleCancelDescriptionEdit}
                        className="text-gray-400 hover:text-gray-600"
                        title="Cancel"
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-gray-600 flex-1">{dataset.description}</p>
                    <button
                      onClick={() => setIsEditingDescription(true)}
                      className="ml-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity"
                      title="Edit description"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  </>
                )}
              </div>
              
              {/* Parameters */}
              {dataset.parameters && dataset.parameters.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {dataset.parameters.map((param) => (
                    <span
                      key={param}
                      className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800"
                      title={dataset.parameter_descriptions?.[param] || param}
                    >
                      {param}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => navigate(`/evaluation/datasets/${datasetId}/runs`)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                View Run History
              </button>
              <button
                onClick={() => navigate(`/evaluation/datasets/${datasetId}/run`)}
                className="btn-primary"
              >
                Run Evaluation
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('cases')}
              className={`${
                activeTab === 'cases'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Cases ({cases.length})
            </button>
            <button
              onClick={() => setActiveTab('auto-synthesize')}
              className={`${
                activeTab === 'auto-synthesize'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Auto Synthesize
            </button>
            <button
              onClick={() => setActiveTab('curated-generation')}
              className={`${
                activeTab === 'curated-generation'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Curated Generation
            </button>
            <button
              onClick={() => setActiveTab('import-data')}
              className={`${
                activeTab === 'import-data'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Import Data
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'cases' && (
          <CasesTab
            cases={cases}
            selectedCases={selectedCases}
            onToggleSelection={toggleCaseSelection}
            onSelectAll={selectAllCases}
            onDeleteCase={handleDeleteCase}
            onDeleteSelected={handleDeleteSelected}
            onCaseUpdated={loadCases}
            dataset={dataset}
          />
        )}

        {activeTab === 'auto-synthesize' && (
          <QuickGenerateTab
            datasetId={Number(datasetId)}
            dataset={dataset}
            parameters={dataset.parameters}
            onCasesAdded={loadCases}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'curated-generation' && (
          <CuratedGenerationTab
            datasetId={Number(datasetId)}
            dataset={dataset}
            parameters={dataset.parameters}
            onCasesAdded={loadCases}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'import-data' && (
          <ImportDataTab
            datasetId={Number(datasetId)}
            dataset={dataset}
            onCasesAdded={loadCases}
            setActiveTab={setActiveTab}
          />
        )}
      </div>
    </div>
  );
};

// Cases Tab Component
interface CasesTabProps {
  cases: EvaluationCase[];
  selectedCases: Set<number>;
  onToggleSelection: (caseId: number) => void;
  onSelectAll: () => void;
  onDeleteCase: (caseId: number) => void;
  onDeleteSelected: () => void;
  onCaseUpdated: () => void;
  dataset: EvaluationDataset;
}

const CasesTab: React.FC<CasesTabProps> = ({
  cases,
  selectedCases,
  onToggleSelection,
  onSelectAll,
  onDeleteCase,
  onDeleteSelected,
  onCaseUpdated,
  dataset,
}) => {
  const [editingCase, setEditingCase] = useState<number | null>(null);

  return (
    <div>
      {/* Actions Bar */}
      {cases.length > 0 && selectedCases.size > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onDeleteSelected}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Delete {selectedCases.size} selected
            </button>
          </div>
        </div>
      )}

      {/* Cases List */}
      {cases.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No cases yet. Generate some cases to get started!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {cases.map((testCase) => (
            <div
              key={testCase.id}
              className="card-elevated p-4"
            >
              <div className="flex items-start">
                <input
                  type="checkbox"
                  checked={selectedCases.has(testCase.id)}
                  onChange={() => onToggleSelection(testCase.id)}
                  className="mt-1 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                
                <div className="ml-4 flex-1">
                  {editingCase === testCase.id ? (
                    <CaseEditor
                      testCase={testCase}
                      onSave={async (updates: Partial<EvaluationCase>) => {
                        try {
                          await evaluationService.updateCase(dataset.id, testCase.id, updates);
                          setEditingCase(null);
                          onCaseUpdated();
                        } catch (err) {
                          console.error('Error saving case:', err);
                          throw err;
                        }
                      }}
                      onCancel={() => setEditingCase(null)}
                    />
                  ) : (
                    <CaseDisplay 
                      testCase={testCase}
                      dataset={dataset}
                    />
                  )}
                </div>
                
                <div className="ml-4 flex space-x-2">
                  <button
                    onClick={() => setEditingCase(editingCase === testCase.id ? null : testCase.id)}
                    className="text-gray-400 hover:text-gray-600"
                    title={editingCase === testCase.id ? "Cancel edit" : "Edit case"}
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onDeleteCase(testCase.id)}
                    className="text-gray-400 hover:text-red-600"
                    title="Delete case"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Preview Case Display Component
interface PreviewCaseDisplayProps {
  preview: CasePreview;
  sessionContext: {
    prompt_lab_name?: string;
    prompt_content?: string;
    prompt_parameters?: string[];
    generation_method?: string;
  };
}

const PreviewCaseDisplay: React.FC<PreviewCaseDisplayProps> = ({ preview, sessionContext }) => {
  const [showFullPrompt, setShowFullPrompt] = useState(false);

  // Handle both session-based and template-based preview formats
  const inputText = preview.input_text || preview.generated_input;
  const outputText = preview.expected_output || preview.generated_output;
  const parameters = preview.parameters || {};
  const hasParameters = Object.keys(parameters).length > 0;

  return (
    <>
      {/* Input Parameters - Main Display */}
      {hasParameters && (
        <div className="mb-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(parameters).map(([key, value]) => (
                  <tr key={key} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {key.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      {String(value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Expected Output */}
      <div className="mb-4">
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-900 whitespace-pre-wrap">{outputText}</p>
        </div>
      </div>

      {/* View Full Prompt Toggle */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowFullPrompt(!showFullPrompt)}
          className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
        >
          {showFullPrompt ? 'Hide Full Prompt' : 'View Full Prompt'}
        </button>
      </div>

      {/* Full Prompt Content */}
      {showFullPrompt && (
        <div className="mt-4 space-y-4 border-t border-gray-200 pt-4">
          {sessionContext.generation_method === 'prompt_lab_prompt' && sessionContext.prompt_lab_name && (
            <div className="mb-4">
              <span className="text-sm text-purple-600 font-medium">From Prompt Lab: {sessionContext.prompt_lab_name}</span>
            </div>
          )}
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Complete Prompt (With Substitutions)</h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{inputText}</pre>
            </div>
          </div>
          
          {(sessionContext.prompt_content || preview.template) && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Original Template</h4>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <pre className="text-sm text-blue-900 whitespace-pre-wrap font-mono">
                  {sessionContext.prompt_content || preview.template}
                </pre>
              </div>
            </div>
          )}
          
          {/* Show bottom hide button if content is large */}
          {((inputText && inputText.length > 1024) || 
            ((sessionContext?.prompt_content || preview?.template) && (sessionContext?.prompt_content || preview?.template)!.length > 1024)) && (
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowFullPrompt(false)}
                className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
              >
                Hide Full Prompt
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
};

// Case Display Component
interface CaseDisplayProps {
  testCase: EvaluationCase;
  dataset: EvaluationDataset;
}

const CaseDisplay: React.FC<CaseDisplayProps> = ({ testCase, dataset }) => {
  const [showFullPrompt, setShowFullPrompt] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [activePromptData, setActivePromptData] = useState<{ content: string | null; parameters: string[] | null } | null>(null);
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  const [comparison, setComparison] = useState<{ templatesMatch: boolean; parametersMatch: boolean; caseTemplate: string } | null>(null);

  // Extract parameters from context or try to parse from input_text
  const parameters = testCase.context || {};
  const hasParameters = Object.keys(parameters).length > 0;

  // Load active prompt for comparison
  useEffect(() => {
    if (dataset.prompt_lab_id) {
      setLoadingPrompt(true);
      promptLabService.getPromptLab(dataset.prompt_lab_id)
        .then(data => {
          if (data.active_prompt?.content) {
            // Extract parameters from the active prompt
            const paramMatches = data.active_prompt.content.match(/\{\{(\w+)\}\}/g);
            const activeParams = paramMatches ? paramMatches.map(match => match.replace(/\{\{|\}\}/g, '')) : [];
            setActivePromptData({
              content: data.active_prompt.content,
              parameters: activeParams
            });
          }
        })
        .catch(err => console.error('Failed to load active prompt:', err))
        .finally(() => setLoadingPrompt(false));
    }
  }, [dataset.prompt_lab_id]);

  // Initialize comparison when active prompt data is loaded
  useEffect(() => {
    if (activePromptData && !comparison) {
      setComparison(comparePrompts());
    }
  }, [activePromptData]);

  // Compare prompts and parameters
  const comparePrompts = () => {
    if (!activePromptData?.content || !testCase.input_text) return null;

    // Extract the template from the case by reverse-engineering parameter substitution
    let caseTemplate = testCase.input_text;
    
    // Sort parameters by value length (longest first) to avoid partial replacements
    const sortedParams = Object.entries(parameters).sort((a, b) => 
      String(b[1]).length - String(a[1]).length
    );
    
    sortedParams.forEach(([key, value]) => {
      const valueStr = String(value);
      
      // Skip if the value is already a template placeholder that matches this key
      if (valueStr === `{{${key}}}`) {
        return;
      }
      
      // Skip if the value contains any template placeholders to avoid double-wrapping
      if (/\{\{[^}]+\}\}/.test(valueStr)) {
        return;
      }
      
      // Create a regex that matches the exact value
      const regex = new RegExp(valueStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
      caseTemplate = caseTemplate.replace(regex, `{{${key}}}`);
    });

    // Compare base templates
    const templatesMatch = caseTemplate.trim() === activePromptData.content.trim();

    // Compare parameters (exclude metadata parameters that aren't part of the prompt template)
    const metadataParams = ['promoted_from_draft', 'selected_variation_index', 'used_custom_output'];
    const caseParams = Object.keys(parameters)
      .filter(param => !metadataParams.includes(param))
      .sort();
    const activeParams = activePromptData.parameters?.sort() || [];
    const parametersMatch = JSON.stringify(caseParams) === JSON.stringify(activeParams);

    return { templatesMatch, parametersMatch, caseTemplate };
  };

  // Generate line-by-line diff
  const generateDiff = (oldText: string, newText: string) => {
    const oldLines = oldText.split('\n');
    const newLines = newText.split('\n');
    
    // Simple LCS-based diff algorithm
    const lcs = (arr1: string[], arr2: string[]): number[][] => {
      const m = arr1.length;
      const n = arr2.length;
      const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
      
      for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
          if (arr1[i - 1] === arr2[j - 1]) {
            dp[i][j] = dp[i - 1][j - 1] + 1;
          } else {
            dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
          }
        }
      }
      
      return dp;
    };
    
    const dp = lcs(oldLines, newLines);
    let i = oldLines.length;
    let j = newLines.length;
    
    const result: Array<{ type: 'unchanged' | 'added' | 'removed'; content: string }> = [];
    
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
        result.unshift({ type: 'unchanged', content: oldLines[i - 1] });
        i--;
        j--;
      } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
        result.unshift({ type: 'added', content: newLines[j - 1] });
        j--;
      } else if (i > 0) {
        result.unshift({ type: 'removed', content: oldLines[i - 1] });
        i--;
      }
    }
    
    return result;
  };

  // Handle Show Diff click
  const handleShowDiff = () => {
    if (!showDiff) {
      // Generate fresh comparison when showing diff
      const newComparison = comparePrompts();
      setComparison(newComparison);
    }
    setShowDiff(!showDiff);
  };

  return (
    <>
      {/* Prompt Comparison Warning */}
      {activePromptData && !loadingPrompt && (() => {
        const comp = comparePrompts();
        return comp && (!comp.templatesMatch || !comp.parametersMatch);
      })() && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-2">
              <svg className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="text-sm">
                <p className="font-medium text-yellow-800">Case uses outdated prompt</p>
                <ul className="mt-1 text-yellow-700 space-y-0.5">
                  {comparison && !comparison.templatesMatch && (
                    <li>• Prompt template has changed</li>
                  )}
                  {comparison && !comparison.parametersMatch && (
                    <li>• Parameters have changed (was: {Object.keys(parameters).filter(param => !['promoted_from_draft', 'selected_variation_index', 'used_custom_output'].includes(param)).join(', ')}, now: {activePromptData.parameters?.join(', ') || 'none'})</li>
                  )}
                </ul>
              </div>
            </div>
            {comparison && !comparison.templatesMatch && (
              <button
                onClick={handleShowDiff}
                className="text-sm text-yellow-700 hover:text-yellow-900 hover:bg-yellow-100 px-2 py-1 rounded transition-colors"
              >
                {showDiff ? 'Hide Diff' : 'Show Diff'}
              </button>
            )}
          </div>
          
          {/* Diff Display */}
          {showDiff && comparison && !comparison.templatesMatch && (
            <div className="mt-3 pt-3 border-t border-yellow-200">
              <div className="bg-white rounded border border-gray-200 overflow-hidden">
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
                  <h5 className="text-xs font-medium text-gray-700">Template Differences</h5>
                </div>
                <div className="font-mono text-xs">
                  {generateDiff(comparison.caseTemplate, activePromptData.content || '').map((line, index) => (
                    <div
                      key={index}
                      className={`px-3 py-0.5 ${
                        line.type === 'removed' 
                          ? 'bg-red-50 text-red-800' 
                          : line.type === 'added' 
                          ? 'bg-green-50 text-green-800' 
                          : 'bg-white text-gray-700'
                      }`}
                    >
                      <span className={`inline-block w-4 text-center ${
                        line.type === 'removed' 
                          ? 'text-red-600' 
                          : line.type === 'added' 
                          ? 'text-green-600' 
                          : 'text-gray-400'
                      }`}>
                        {line.type === 'removed' ? '-' : line.type === 'added' ? '+' : ' '}
                      </span>
                      <span className="ml-2">{line.content || '\u00A0'}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Input Parameters - Main Display */}
      {hasParameters && (
        <div className="mb-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(parameters).map(([key, value]) => (
                  <tr key={key} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {key.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      {String(value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Expected Output */}
      <div className="mb-4">
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-900 whitespace-pre-wrap">{testCase.expected_output}</p>
        </div>
      </div>

      {/* View Full Prompt Toggle */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowFullPrompt(!showFullPrompt)}
          className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
        >
          {showFullPrompt ? 'Hide Full Prompt' : 'View Full Prompt'}
        </button>
      </div>

      {/* Full Prompt Content */}
      {showFullPrompt && (
        <div className="mt-4 space-y-4 border-t border-gray-200 pt-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Complete Prompt</h4>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{testCase.input_text}</pre>
            </div>
          </div>
          
          {/* Show bottom hide button if content is large */}
          {testCase.input_text && testCase.input_text.length > 1024 && (
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowFullPrompt(false)}
                className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
              >
                Hide Full Prompt
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
};

// Case Editor Component
interface CaseEditorProps {
  testCase: EvaluationCase;
  onSave: (updates: Partial<EvaluationCase>) => Promise<void>;
  onCancel: () => void;
}

const CaseEditor: React.FC<CaseEditorProps> = ({ testCase, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    parameters: testCase.context || {},
    expected_output: testCase.expected_output,
  });

  const handleParameterChange = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    }));
  };

  const handleSubmit = async () => {
    try {
      await onSave({
        expected_output: formData.expected_output,
        context: formData.parameters,
      });
    } catch (err) {
      console.error('Error saving case:', err);
    }
  };

  return (
    <div className="space-y-4">
      {/* Individual Parameter Fields */}
      {Object.entries(formData.parameters).map(([key, value]) => (
        <div key={key}>
          <label className="block text-sm font-medium text-purple-700 mb-1 uppercase tracking-wider text-xs">
            {key.replace(/_/g, ' ')}
          </label>
          <textarea
            ref={(textarea) => {
              if (textarea) {
                setTimeout(() => {
                  textarea.style.height = 'auto';
                  textarea.style.height = Math.min(textarea.scrollHeight, window.innerHeight) + 'px';
                }, 0);
              }
            }}
            value={String(value)}
            onChange={(e) => handleParameterChange(key, e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 resize-none overflow-hidden"
            style={{
              height: 'auto',
              minHeight: '2.5rem',
              maxHeight: '100vh'
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, window.innerHeight) + 'px';
            }}
            placeholder={`Enter ${key.replace(/_/g, ' ')}`}
          />
        </div>
      ))}
      
      {/* Expected Output */}
      <div className="mt-8">
        <div className="border-t-2 border-gray-300 mb-4"></div>
        <textarea
          ref={(textarea) => {
            if (textarea) {
              setTimeout(() => {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, window.innerHeight) + 'px';
              }, 0);
            }
          }}
          value={formData.expected_output}
          onChange={(e) => setFormData({ ...formData, expected_output: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 resize-none overflow-hidden"
          style={{
            height: 'auto',
            minHeight: '3rem',
            maxHeight: '100vh'
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, window.innerHeight) + 'px';
          }}
          placeholder="Enter expected output"
        />
      </div>
      
      <div className="flex justify-end space-x-2">
        <button
          onClick={onCancel}
          className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          className="rounded-md bg-purple-600 px-3 py-1 text-sm font-medium text-white hover:bg-purple-700"
        >
          Save
        </button>
      </div>
    </div>
  );
};

// Generate Cases Tab Component
interface GenerateCasesTabProps {
  datasetId: number;
  dataset: EvaluationDataset;
  parameters: string[];
  onCasesAdded: () => void;
  setActiveTab: (tab: 'cases' | 'auto-synthesize' | 'curated-generation' | 'import-data') => void;
}

const GenerateCasesTab: React.FC<GenerateCasesTabProps> = ({ datasetId, dataset, parameters, onCasesAdded, setActiveTab }) => {
  const [template, setTemplate] = useState('');
  const [count, setCount] = useState(5);
  const [previews, setPreviews] = useState<CasePreview[]>([]);
  const [selectedPreviews, setSelectedPreviews] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useSessionPrompt, setUseSessionPrompt] = useState(true);
  const [generateOutputVariations, setGenerateOutputVariations] = useState(false);
  const [variationsCount, setVariationsCount] = useState(3);
  const [persistImmediately, setPersistImmediately] = useState(true);
  const [maxTokens, setMaxTokens] = useState(500);
  const [casesWithVariations, setCasesWithVariations] = useState<Map<string, any>>(new Map());
  const [sessionContext, setSessionContext] = useState<{
    prompt_lab_name?: string;
    prompt_content?: string;
    prompt_parameters?: string[];
    generation_method?: string;
    supports_variations?: boolean;
  }>({});

  const handleGenerate = async () => {
    if (!useSessionPrompt && !template.trim()) {
      setError('Please enter a template or enable session prompt generation');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const result = await evaluationService.generateCases(
        datasetId, 
        template, 
        count, 
        useSessionPrompt, 
        generateOutputVariations, 
        variationsCount,
        persistImmediately,
        maxTokens
      );
      setPreviews(result.previews);
      
      // Handle immediate persistence feedback
      if (persistImmediately && result.persisted_count && result.persisted_count > 0) {
        // Cases were immediately persisted, refresh the cases list and switch tabs
        onCasesAdded(); // This will reload the cases
        setActiveTab('cases'); // Switch to cases tab to show the persisted cases
        
        // Show success feedback
        setError(`✅ Successfully generated and saved ${result.persisted_count} case${result.persisted_count !== 1 ? 's' : ''} to the dataset!`);
        
        // Clear the previews since cases are now persisted
        setPreviews([]);
        setSelectedPreviews(new Set());
        setCasesWithVariations(new Map());
        setTemplate('');
        
        // Clear success message after a delay
        setTimeout(() => setError(null), 5000);
        
        return; // Don't process variations when immediately persisted
      }
      
      // Initialize cases with variations if they exist
      if (generateOutputVariations) {
        const variationsMap = new Map();
        result.previews.forEach(preview => {
          if (preview.output_variations && preview.output_variations.length > 0) {
            variationsMap.set(preview.preview_id, {
              ...preview,
              selected_output_index: null,
              custom_output: null
            });
          }
        });
        setCasesWithVariations(variationsMap);
        setSelectedPreviews(new Set()); // Don't auto-select when variations are available
      } else {
        setCasesWithVariations(new Map());
        setSelectedPreviews(new Set(result.previews.map(p => p.preview_id)));
      }
      
      setSessionContext({
        prompt_lab_name: result.prompt_lab_name || (result as any).session_name,
        prompt_content: result.prompt_content,
        prompt_parameters: result.prompt_parameters,
        generation_method: result.generation_method,
        supports_variations: result.supports_variations
      });
    } catch (err) {
      setError('Failed to generate cases');
      console.error('Error generating cases:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleAddSelected = async () => {
    if (generateOutputVariations && casesWithVariations.size > 0) {
      // Handle cases with output variations
      const validCases = Array.from(casesWithVariations.values()).filter(caseData => {
        return (caseData.selected_output_index !== null) || 
               (caseData.custom_output && caseData.custom_output.trim() !== '');
      });
      
      if (validCases.length === 0) {
        setError('Please select outputs for at least one case');
        return;
      }

      try {
        await evaluationService.addSelectedCasesWithVariations(datasetId, validCases);
        onCasesAdded();
        setPreviews([]);
        setCasesWithVariations(new Map());
        setSelectedPreviews(new Set());
        setTemplate('');
      } catch (err) {
        setError('Failed to add cases with variations');
        console.error('Error adding cases with variations:', err);
      }
    } else {
      // Handle legacy cases without variations
      if (selectedPreviews.size === 0) return;

      try {
        await evaluationService.addSelectedCases(
          datasetId,
          Array.from(selectedPreviews)
        );
        onCasesAdded();
        setPreviews([]);
        setSelectedPreviews(new Set());
        setTemplate('');
      } catch (err) {
        setError('Failed to add cases');
        console.error('Error adding cases:', err);
      }
    }
  };

  const handleCaseUpdate = (updatedCase: any) => {
    setCasesWithVariations(prev => {
      const newMap = new Map(prev);
      newMap.set(updatedCase.preview_id, updatedCase);
      return newMap;
    });
  };

  return (
    <div className="space-y-6">
      {/* Session Context Information */}
      {dataset.prompt_lab_id && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-purple-900">Prompt Lab-Associated Dataset</h4>
              <p className="text-sm text-purple-700 mt-1">
                This dataset is associated with a prompt lab. You can generate cases using the prompt lab's active prompt.
              </p>
            </div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useSessionPrompt}
                onChange={(e) => setUseSessionPrompt(e.target.checked)}
                className="rounded border-purple-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm font-medium text-purple-900">Use Prompt Lab Prompt</span>
            </label>
          </div>
          
          {sessionContext.generation_method === 'prompt_lab_prompt' && (
            <div className="mt-4 space-y-3">
              <div>
                <h5 className="text-xs font-medium text-purple-800 uppercase tracking-wider">Prompt Lab</h5>
                <p className="text-sm text-purple-700">{sessionContext.prompt_lab_name}</p>
              </div>
              
              {sessionContext.prompt_parameters && sessionContext.prompt_parameters.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-purple-800 uppercase tracking-wider">Prompt Parameters</h5>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {sessionContext.prompt_parameters.map((param) => (
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
              
              {sessionContext.prompt_content && (
                <div>
                  <h5 className="text-xs font-medium text-purple-800 uppercase tracking-wider">Prompt Template</h5>
                  <pre className="text-xs text-purple-700 bg-purple-100 p-2 rounded mt-1 whitespace-pre-wrap">
                    {sessionContext.prompt_content}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Template Input */}
      <div style={{ display: useSessionPrompt ? 'none' : 'block' }}>
        <label className="block text-sm font-medium text-gray-700">
          Case Template
        </label>
        <p className="mt-1 text-sm text-gray-500">
          Use {'{parameter}'} syntax to include parameters in your template
        </p>
        <textarea
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          rows={6}
          className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
          placeholder={`Customer {customer_name} is asking about {issue_type}. They are {emotion} and need {resolution_type}.`}
        />
        
        {/* Available Parameters */}
        {parameters.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">Available parameters:</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {parameters.map((param) => (
                <code
                  key={param}
                  className="text-xs bg-gray-100 px-2 py-1 rounded cursor-pointer hover:bg-gray-200"
                  onClick={() => {
                    const cursorPos = (document.activeElement as HTMLTextAreaElement)?.selectionStart || template.length;
                    const newTemplate = template.slice(0, cursorPos) + `{${param}}` + template.slice(cursorPos);
                    setTemplate(newTemplate);
                  }}
                >
                  {'{' + param + '}'}
                </code>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Count Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Number of Cases
        </label>
        <select
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
          className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        >
          {[1, 5, 10, 20, 50].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {/* Max Tokens Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Max Tokens for Generated Outputs
        </label>
        <p className="mt-1 text-sm text-gray-500">
          Controls the maximum length of AI-generated expected outputs
        </p>
        <select
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        >
          <option value={200}>200 tokens (short)</option>
          <option value={350}>350 tokens (medium)</option>
          <option value={500}>500 tokens (long)</option>
          <option value={750}>750 tokens (detailed)</option>
          <option value={1000}>1000 tokens (comprehensive)</option>
        </select>
      </div>

      {/* Immediate Persistence Toggle */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Save Mode</h4>
            <p className="text-sm text-gray-600 mt-1">
              {persistImmediately 
                ? 'Cases will be saved immediately upon generation'
                : 'Cases will be generated for preview first, then you can select which ones to save'
              }
            </p>
          </div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={persistImmediately}
              onChange={(e) => {
                const newValue = e.target.checked;
                setPersistImmediately(newValue);
                // If switching to immediate persistence, disable output variations for simplicity
                if (newValue) {
                  setGenerateOutputVariations(false);
                }
              }}
              className="rounded border-gray-300 text-green-600 focus:ring-green-500"
            />
            <span className="text-sm font-medium text-gray-900">Save Immediately</span>
          </label>
        </div>
      </div>

      {/* Output Variations Toggle or Info */}
      {(useSessionPrompt || sessionContext.supports_variations) && (
        persistImmediately ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-gray-700">Output Variations</h4>
                <p className="text-sm text-gray-500 mt-1">
                  Output variations are disabled when "Save Immediately" is enabled. Turn off immediate saving to use variations.
                </p>
              </div>
            </div>
          </div>
        ) : (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-blue-900">Output Variations</h4>
              <p className="text-sm text-blue-700 mt-1">
                Generate multiple output styles (formal, friendly, detailed, etc.) for each case to choose from.
              </p>
            </div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={generateOutputVariations}
                onChange={(e) => setGenerateOutputVariations(e.target.checked)}
                className="rounded border-blue-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-blue-900">Enable Variations</span>
            </label>
          </div>
          
          {generateOutputVariations && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-blue-800">
                Number of Variations per Case
              </label>
              <select
                value={variationsCount}
                onChange={(e) => setVariationsCount(Number(e.target.value))}
                className="mt-1 block w-32 rounded-md border-blue-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {[2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
              <p className="text-xs text-blue-600 mt-1">
                Each case will have {variationsCount} different output styles to choose from.
              </p>
            </div>
          )}
        </div>
        )
      )}

      {/* Generate Button */}
      <div>
        <button
          onClick={handleGenerate}
          disabled={generating || (!useSessionPrompt && !template.trim())}
          className="btn-primary flex items-center space-x-2"
        >
          {generating && (
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          <span>
            {generating ? 'Generating...' : (
              persistImmediately 
                ? `Generate & Save ${count} Case${count !== 1 ? 's' : ''}${useSessionPrompt ? ' from Session Prompt' : ' from Template'}`
                : useSessionPrompt ? 'Generate Cases from Session Prompt' : 'Generate Cases from Template'
            )}
          </span>
        </button>
        
        {generating && (
          <div className="mt-3">
            <div className="flex items-center space-x-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <p className="text-sm text-purple-600 font-medium">
                Generating {count} evaluation case{count !== 1 ? 's' : ''}...
              </p>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
            </div>
          </div>
        )}
        
        {!generating && (
          <p className="text-sm text-gray-600 mt-2">
            {persistImmediately 
              ? `Cases will be generated and immediately saved to the dataset${useSessionPrompt ? ' using the active prompt from the associated session' : ''}.`
              : useSessionPrompt 
                ? 'Cases will be generated using the active prompt from the associated session.'
                : 'Cases will be generated for preview first, then you can select which ones to save.'
            }
          </p>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Previews */}
      {previews.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Generated Cases</h3>
            {generateOutputVariations && casesWithVariations.size > 0 ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  {Array.from(casesWithVariations.values()).filter(caseData => 
                    (caseData.selected_output_index !== null) || 
                    (caseData.custom_output && caseData.custom_output.trim() !== '')
                  ).length} of {casesWithVariations.size} cases ready
                </span>
                <button
                  onClick={handleAddSelected}
                  disabled={Array.from(casesWithVariations.values()).filter(caseData => 
                    (caseData.selected_output_index !== null) || 
                    (caseData.custom_output && caseData.custom_output.trim() !== '')
                  ).length === 0}
                  className="btn-primary"
                >
                  Add Selected Cases
                </button>
              </div>
            ) : (
              <button
                onClick={handleAddSelected}
                disabled={selectedPreviews.size === 0}
                className="btn-primary"
              >
                Add {selectedPreviews.size} Selected Cases
              </button>
            )}
          </div>

          <div className="space-y-6">
            {previews.map((preview, index) => {
              const hasVariations = preview.output_variations && preview.output_variations.length > 0;
              
              if (generateOutputVariations && hasVariations) {
                // Use CaseWithOutputSelection for cases with variations
                const caseData = casesWithVariations.get(preview.preview_id) || {
                  ...preview,
                  selected_output_index: null,
                  custom_output: null
                };
                
                return (
                  <CaseWithOutputSelection
                    key={preview.preview_id}
                    caseData={caseData}
                    onCaseUpdate={handleCaseUpdate}
                    caseNumber={index + 1}
                  />
                );
              } else {
                // Use traditional checkbox selection for simple cases
                return (
                  <div key={preview.preview_id} className="card-elevated p-4">
                    <div className="flex items-start">
                      <input
                        type="checkbox"
                        checked={selectedPreviews.has(preview.preview_id)}
                        onChange={(e) => {
                          const newSelection = new Set(selectedPreviews);
                          if (e.target.checked) {
                            newSelection.add(preview.preview_id);
                          } else {
                            newSelection.delete(preview.preview_id);
                          }
                          setSelectedPreviews(newSelection);
                        }}
                        className="mt-1 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                      
                      <div className="ml-4 flex-1">
                        <PreviewCaseDisplay 
                          preview={preview}
                          sessionContext={sessionContext}
                        />
                      </div>
                      
                      <div className="ml-4 flex space-x-2">
                        <button
                          onClick={async () => {
                            try {
                              const newPreview = await evaluationService.regenerateCase(
                                datasetId,
                                preview.preview_id
                              );
                              setPreviews(previews.map(p =>
                                p.preview_id === preview.preview_id ? newPreview : p
                              ));
                            } catch (err) {
                              console.error('Error regenerating case:', err);
                            }
                          }}
                          className="text-gray-400 hover:text-gray-600"
                          title="Regenerate"
                        >
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              }
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// Auto Synthesize Tab Component - Machine-only generation with immediate persistence
const QuickGenerateTab: React.FC<GenerateCasesTabProps> = ({ datasetId, dataset, parameters, onCasesAdded, setActiveTab }) => {
  const [template, setTemplate] = useState('');
  const [count, setCount] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useSessionPrompt, setUseSessionPrompt] = useState(true);
  const [maxTokens, setMaxTokens] = useState(500);
  const [sessionContext, setSessionContext] = useState<{
    prompt_lab_name?: string;
    prompt_content?: string;
    prompt_parameters?: string[];
    generation_method?: string;
  }>({});

  const handleGenerate = async () => {
    if (!useSessionPrompt && !template.trim()) {
      setError('Please enter a template or enable session prompt generation');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const result = await evaluationService.generateCases(
        datasetId, 
        template, 
        count, 
        useSessionPrompt, 
        false, // No output variations for auto synthesize
        3,
        true, // Always persist immediately for auto synthesize
        maxTokens
      );
      
      // Cases were immediately persisted
      onCasesAdded(); // This will reload the cases
      setActiveTab('cases'); // Switch to cases tab to show the persisted cases
      
      // Show success feedback
      setError(`✅ Successfully generated and saved ${result.persisted_count || count} case${(result.persisted_count || count) !== 1 ? 's' : ''} to the dataset!`);
      
      // Clear the template
      setTemplate('');
      
      // Clear success message after a delay
      setTimeout(() => setError(null), 5000);
      
      setSessionContext({
        prompt_lab_name: result.prompt_lab_name || (result as any).session_name,
        prompt_content: result.prompt_content,
        prompt_parameters: result.prompt_parameters,
        generation_method: result.generation_method
      });
    } catch (err) {
      setError('Failed to generate cases');
      console.error('Error generating cases:', err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900">Quick Generation Mode</h4>
            <p className="text-sm text-blue-700 mt-1">
              Generate evaluation cases quickly with machine-generated outputs. Cases are automatically saved to the dataset immediately upon generation.
            </p>
          </div>
        </div>
      </div>

      {/* Session Context Information */}
      {dataset.prompt_lab_id && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-purple-900">Prompt Lab-Associated Dataset</h4>
              <p className="text-sm text-purple-700 mt-1">
                This dataset is associated with a prompt lab. You can generate cases using the prompt lab's active prompt.
              </p>
            </div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useSessionPrompt}
                onChange={(e) => setUseSessionPrompt(e.target.checked)}
                className="rounded border-purple-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="text-sm font-medium text-purple-900">Use Prompt Lab Prompt</span>
            </label>
          </div>
          
          {sessionContext.generation_method === 'prompt_lab_prompt' && (
            <div className="mt-4 space-y-3">
              <div>
                <h5 className="text-xs font-medium text-purple-800 uppercase tracking-wider">Prompt Lab</h5>
                <p className="text-sm text-purple-700">{sessionContext.prompt_lab_name}</p>
              </div>
              
              {sessionContext.prompt_parameters && sessionContext.prompt_parameters.length > 0 && (
                <div>
                  <h5 className="text-xs font-medium text-purple-800 uppercase tracking-wider">Prompt Parameters</h5>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {sessionContext.prompt_parameters.map((param) => (
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
          )}
        </div>
      )}

      {/* Template Input */}
      <div style={{ display: useSessionPrompt ? 'none' : 'block' }}>
        <label className="block text-sm font-medium text-gray-700">
          Case Template
        </label>
        <p className="mt-1 text-sm text-gray-500">
          Use {'{parameter}'} syntax to include parameters in your template
        </p>
        <textarea
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          rows={6}
          className="mt-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
          placeholder={`Customer {customer_name} is asking about {issue_type}. They are {emotion} and need {resolution_type}.`}
        />
        
        {/* Available Parameters */}
        {parameters.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">Available parameters:</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {parameters.map((param) => (
                <code
                  key={param}
                  className="text-xs bg-gray-100 px-2 py-1 rounded cursor-pointer hover:bg-gray-200"
                  onClick={() => {
                    const cursorPos = (document.activeElement as HTMLTextAreaElement)?.selectionStart || template.length;
                    const newTemplate = template.slice(0, cursorPos) + `{${param}}` + template.slice(cursorPos);
                    setTemplate(newTemplate);
                  }}
                >
                  {'{' + param + '}'}
                </code>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Count Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Number of Cases
        </label>
        <select
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
          className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        >
          {[1, 5, 10, 20, 50].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {/* Max Tokens Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Max Tokens for Generated Outputs
        </label>
        <p className="mt-1 text-sm text-gray-500">
          Controls the maximum length of AI-generated expected outputs
        </p>
        <select
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        >
          <option value={200}>200 tokens (short)</option>
          <option value={350}>350 tokens (medium)</option>
          <option value={500}>500 tokens (long)</option>
          <option value={750}>750 tokens (detailed)</option>
          <option value={1000}>1000 tokens (comprehensive)</option>
        </select>
      </div>

      {/* Generate Button */}
      <div>
        <button
          onClick={handleGenerate}
          disabled={generating || (!useSessionPrompt && !template.trim())}
          className="btn-primary flex items-center space-x-2"
        >
          {generating && (
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          <span>
            {generating ? 'Generating...' : `Generate & Save ${count} Case${count !== 1 ? 's' : ''}`}
          </span>
        </button>
        
        {generating && (
          <div className="mt-3">
            <div className="flex items-center space-x-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <p className="text-sm text-purple-600 font-medium">
                Generating {count} evaluation case{count !== 1 ? 's' : ''}...
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className={`rounded-md p-4 ${error.startsWith('✅') ? 'bg-green-50' : 'bg-red-50'}`}>
          <p className={`text-sm ${error.startsWith('✅') ? 'text-green-800' : 'text-red-800'}`}>{error}</p>
        </div>
      )}
    </div>
  );
};

// Curated Generation Tab Component - One-at-a-time draft curation
const CuratedGenerationTab: React.FC<GenerateCasesTabProps> = ({ datasetId, dataset, parameters, onCasesAdded, setActiveTab }) => {
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [curating, setCurating] = useState(false);
  const [triggeringGeneration, setTriggeringGeneration] = useState(false);

  useEffect(() => {
    loadDrafts();
  }, [datasetId]);

  const loadDrafts = async () => {
    try {
      setLoading(true);
      const data = await evaluationService.getDrafts(datasetId);
      setDrafts(data);
      setError(null);
      
      // If no drafts are ready and none are generating, trigger generation
      const readyDrafts = data.filter(draft => draft.status === 'ready');
      const generatingDrafts = data.filter(draft => draft.status === 'generating');
      
      if (readyDrafts.length === 0 && generatingDrafts.length === 0) {
        // Automatically trigger generation when no drafts exist
        triggerDraftGeneration();
      }
    } catch (err) {
      setError('Failed to load draft cases');
      console.error('Error loading drafts:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerDraftGeneration = async () => {
    try {
      setTriggeringGeneration(true);
      await evaluationService.triggerDraftGeneration(datasetId);
      // Reload drafts after triggering generation
      setTimeout(() => loadDrafts(), 1500); // Small delay to allow backend to process
    } catch (triggerErr) {
      console.error('Error triggering draft generation:', triggerErr);
      setError('Failed to trigger draft generation. Please try again.');
    } finally {
      setTriggeringGeneration(false);
    }
  };

  const handlePromoteDraft = async (draftId: number, selectedOutputIndex?: number, customOutput?: string) => {
    try {
      setCurating(true);
      await evaluationService.promoteDraft(datasetId, draftId, selectedOutputIndex, customOutput);
      onCasesAdded(); // Refresh the cases tab
      await loadDrafts(); // Refresh drafts (should trigger background generation of new drafts)
      setError(null);
    } catch (err) {
      setError('Failed to promote draft case');
      console.error('Error promoting draft:', err);
    } finally {
      setCurating(false);
    }
  };

  const handleDiscardDraft = async (draftId: number, reason?: string) => {
    try {
      setCurating(true);
      await evaluationService.discardDraft(datasetId, draftId, reason);
      await loadDrafts(); // Refresh drafts (should trigger background generation of new drafts)
      setError(null);
    } catch (err) {
      setError('Failed to discard draft case');
      console.error('Error discarding draft:', err);
    } finally {
      setCurating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <span className="ml-3 text-gray-600">Loading draft cases...</span>
        </div>
      </div>
    );
  }

  const readyDrafts = drafts.filter(draft => draft.status === 'ready');
  const generatingDrafts = drafts.filter(draft => draft.status === 'generating');

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg className="h-5 w-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-purple-900">Curated Generation</h4>
            <p className="text-sm text-purple-700 mt-1">
              Review and curate draft cases one at a time. Each draft includes multiple output variations that you can edit and promote directly to cases.
            </p>
          </div>
        </div>
      </div>


      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Draft Cases */}
      {readyDrafts.length > 0 ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              Draft Cases Ready for Curation
            </h3>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-500">
                {readyDrafts.length} ready to curate
              </span>
            </div>
          </div>
          
          {/* Show only the first draft */}
          <DraftCaseCard
            key={readyDrafts[0].id}
            draft={readyDrafts[0]}
            index={0}
            onPromote={handlePromoteDraft}
            onDiscard={handleDiscardDraft}
            curating={curating}
          />
        </div>
      ) : (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No draft cases ready</h3>
          <p className="mt-1 text-sm text-gray-500">
            {generatingDrafts.length > 0 
              ? 'Draft cases are being generated in the background. Check back in a moment.'
              : 'Draft cases will be generated automatically for this dataset.'
            }
          </p>
          
          {/* Manual generation button */}
          {generatingDrafts.length === 0 && (
            <div className="mt-6">
              <button
                onClick={triggerDraftGeneration}
                disabled={triggeringGeneration}
                className="btn-primary flex items-center justify-center space-x-2 mx-auto"
              >
                {triggeringGeneration && (
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                <span>
                  {triggeringGeneration ? 'Generating Draft Cases...' : 'Generate Draft Cases'}
                </span>
              </button>
              <p className="mt-2 text-xs text-gray-500">
                This will create new draft cases for you to curate
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};


// Draft Case Card Component
interface DraftCaseCardProps {
  draft: any;
  index: number;
  onPromote: (draftId: number, selectedOutputIndex?: number, customOutput?: string) => void;
  onDiscard: (draftId: number, reason?: string) => void;
  curating: boolean;
}

const DraftCaseCard: React.FC<DraftCaseCardProps> = ({ draft, index, onPromote, onDiscard, curating }) => {
  const [editingOutputs, setEditingOutputs] = useState<Record<number, string>>({});
  const [discardReason, setDiscardReason] = useState('');
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  const handlePromoteOutput = (outputIndex: number, customText?: string) => {
    if (customText !== undefined) {
      onPromote(draft.id, undefined, customText.trim());
    } else {
      onPromote(draft.id, outputIndex);
    }
  };

  const handleEditOutput = (outputIndex: number) => {
    const currentText = draft.output_variations?.[outputIndex]?.text || '';
    setEditingOutputs(prev => ({
      ...prev,
      [outputIndex]: currentText
    }));
  };

  const handleSaveEditedOutput = (outputIndex: number) => {
    const editedText = editingOutputs[outputIndex];
    if (editedText && editedText.trim()) {
      handlePromoteOutput(outputIndex, editedText.trim());
    }
  };

  const handleCancelEdit = (outputIndex: number) => {
    setEditingOutputs(prev => {
      const newState = { ...prev };
      delete newState[outputIndex];
      return newState;
    });
  };

  const handleDiscard = () => {
    onDiscard(draft.id, discardReason.trim() || 'Not suitable');
    setShowDiscardModal(false);
    setDiscardReason('');
  };

  return (
    <div className="card-elevated p-6">
      <div className="flex items-start justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900">
          Draft Case #{index + 1}
        </h4>
        <div className="flex items-center space-x-2">
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
            Draft
          </span>
        </div>
      </div>

      {/* Input Parameters */}
      <div className="mb-6">
        <h5 className="text-sm font-medium text-gray-700 mb-2">Input Parameters</h5>
        {draft.parameters && Object.keys(draft.parameters).length > 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(draft.parameters).map(([key, value]) => (
                  <tr key={key} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {key.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      {String(value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-gray-50 p-4 rounded-lg border">
            <p className="text-sm text-gray-500 italic">No parameters for this case</p>
          </div>
        )}
      </div>

      {/* Output Options */}
      <div className="mb-6">
        <h5 className="text-sm font-medium text-gray-700 mb-3">Output Variations</h5>
        
        {/* Generated Outputs */}
        <div className="space-y-4">
          {draft.output_variations?.map((output: any, outputIndex: number) => (
            <div
              key={outputIndex}
              className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-700">
                    Option {outputIndex + 1}
                  </span>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {output.style}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditOutput(outputIndex)}
                    disabled={curating || editingOutputs[outputIndex] !== undefined}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded transition-colors disabled:opacity-50"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => {
                      if (editingOutputs[outputIndex] !== undefined) {
                        handleSaveEditedOutput(outputIndex);
                      } else {
                        handlePromoteOutput(outputIndex);
                      }
                    }}
                    disabled={curating || (editingOutputs[outputIndex] !== undefined && !editingOutputs[outputIndex]?.trim())}
                    className="text-xs text-white bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded transition-colors disabled:opacity-50"
                  >
                    {curating ? 'Promoting...' : 'Promote to Case'}
                  </button>
                </div>
              </div>
              
              {editingOutputs[outputIndex] !== undefined ? (
                // Edit mode
                <div className="space-y-3">
                  <textarea
                    ref={(textarea) => {
                      if (textarea) {
                        // Auto-resize on mount
                        setTimeout(() => {
                          textarea.style.height = 'auto';
                          textarea.style.height = textarea.scrollHeight + 'px';
                        }, 0);
                      }
                    }}
                    value={editingOutputs[outputIndex]}
                    onChange={(e) => setEditingOutputs(prev => ({
                      ...prev,
                      [outputIndex]: e.target.value
                    }))}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 resize-none overflow-hidden"
                    placeholder="Edit the output text..."
                    style={{
                      height: 'auto',
                      minHeight: '3rem'
                    }}
                    onInput={(e) => {
                      const target = e.target as HTMLTextAreaElement;
                      target.style.height = 'auto';
                      target.style.height = target.scrollHeight + 'px';
                    }}
                    autoFocus
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={() => handleCancelEdit(outputIndex)}
                      className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // Display mode
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{output.text}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <button
          onClick={() => setShowDiscardModal(true)}
          disabled={curating}
          className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
        >
          Discard Draft
        </button>
      </div>

      {/* Discard Modal */}
      {showDiscardModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowDiscardModal(false)}></div>
            
            <div className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Discard Draft Case</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reason (optional)
                </label>
                <textarea
                  value={discardReason}
                  onChange={(e) => setDiscardReason(e.target.value)}
                  placeholder="Why is this draft not suitable?"
                  rows={3}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500"
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDiscardModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDiscard}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
                >
                  Discard Draft
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Import Data Tab Component
interface ImportDataTabProps {
  datasetId: number;
  dataset: EvaluationDataset;
  onCasesAdded: () => void;
  setActiveTab: (tab: 'cases' | 'auto-synthesize' | 'curated-generation' | 'import-data') => void;
}

const ImportDataTab: React.FC<ImportDataTabProps> = ({ datasetId, dataset, onCasesAdded, setActiveTab }) => {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file to import');
      return;
    }

    try {
      setImporting(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/evaluations/datasets/${datasetId}/import/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to import file');
      }

      const result = await response.json();
      setSuccess(`Successfully imported ${result.imported_count} cases`);
      setFile(null);
      onCasesAdded(); // Refresh the cases list
      
      // Clear success message after delay and switch to cases tab
      setTimeout(() => {
        setSuccess(null);
        setActiveTab('cases');
      }, 3000);

    } catch (err) {
      setError('Failed to import data. Please check your file format.');
      console.error('Import error:', err);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900">Import Evaluation Cases</h4>
            <p className="text-sm text-blue-700 mt-1">
              Upload a JSONL file to import evaluation cases. Use parameter key-value pairs that will be substituted into your prompt template.
            </p>
          </div>
        </div>
      </div>

      {/* File Format Example */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h5 className="text-sm font-medium text-gray-900 mb-2">Expected File Format (JSONL)</h5>
        <pre className="text-xs text-gray-700 bg-white p-3 rounded border overflow-x-auto">
{`{"parameters": {"user_name": "John Smith", "issue_type": "return policy", "product": "laptop"}, "expected_output": "Hi John Smith, our return policy allows returns within 30 days of purchase for laptops."}
{"parameters": {"user_name": "Sarah Johnson", "issue_type": "order tracking", "order_id": "ORD-12345"}, "expected_output": "Hello Sarah Johnson, you can track order ORD-12345 using the link in your confirmation email."}
{"parameters": {"user_name": "Mike Chen", "issue_type": "cancellation", "order_id": "ORD-67890"}, "expected_output": "Hi Mike Chen, I can help you cancel order ORD-67890 within 2 hours of placement."}`}
        </pre>
        <p className="text-xs text-gray-600 mt-2">
          <strong>New format (recommended):</strong> Use 'parameters' object with key-value pairs that will be substituted into your prompt template.<br/>
          <strong>Legacy format:</strong> You can still use 'input'/'expected' or 'input_text'/'expected_output' field names.
        </p>
      </div>

      {/* File Upload */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select JSONL File
          </label>
          <input
            type="file"
            accept=".jsonl,.json"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
          />
        </div>

        {file && (
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-sm text-gray-700">
              <span className="font-medium">Selected file:</span> {file.name}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Size: {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
        )}
      </div>

      {/* Import Button */}
      <div>
        <button
          onClick={handleImport}
          disabled={!file || importing}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {importing && (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          <span>
            {importing ? 'Importing...' : 'Import Cases'}
          </span>
        </button>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="rounded-md bg-green-50 p-4">
          <p className="text-sm text-green-800">{success}</p>
        </div>
      )}

      {/* Tips */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h5 className="text-sm font-medium text-yellow-800 mb-2">Import Tips</h5>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>• Files must be in JSONL format (one JSON object per line)</li>
          <li>• <strong>Recommended:</strong> Use 'parameters' object with key-value pairs + 'expected_output' field</li>
          <li>• Parameters will be substituted into your active prompt template (e.g., {{user_name}} → "John Smith")</li>
          <li>• <strong>Legacy support:</strong> Direct 'input'/'input_text' and 'expected'/'expected_output' fields still work</li>
          <li>• Maximum file size: 10MB</li>
        </ul>
      </div>
    </div>
  );
};

export default EvaluationDatasetDetail;