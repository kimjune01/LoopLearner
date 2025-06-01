/**
 * Evaluation Dataset Detail Component
 * Shows dataset details, cases, and allows case management
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import CaseWithOutputSelection from './CaseWithOutputSelection';
import type { EvaluationDataset, EvaluationCase, CasePreview } from '../types/evaluation';

const EvaluationDatasetDetail: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cases' | 'quick-generate' | 'curated-generation'>('cases');
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
            onClick={() => navigate('/evaluation/datasets')}
            className="mb-4 text-sm text-gray-600 hover:text-gray-900 flex items-center"
          >
            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Datasets
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
              
              {/* Prompt Lab Link */}
              {dataset.prompt_lab_id && (
                <div className="mt-3 flex items-center space-x-2">
                  <svg className="h-4 w-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <span className="text-sm text-gray-600">Associated with prompt lab:</span>
                  <button
                    onClick={() => navigate(`/prompt-labs/${dataset.prompt_lab_id}`)}
                    className="text-sm font-medium text-purple-600 hover:text-purple-800 hover:underline"
                  >
                    View Prompt Lab →
                  </button>
                </div>
              )}
              
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
              onClick={() => setActiveTab('quick-generate')}
              className={`${
                activeTab === 'quick-generate'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Quick Generate
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

        {activeTab === 'quick-generate' && (
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
      {cases.length > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={selectedCases.size === cases.length}
                onChange={onSelectAll}
                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span className="ml-2 text-sm text-gray-700">Select all</span>
            </label>
            
            {selectedCases.size > 0 && (
              <button
                onClick={onDeleteSelected}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Delete {selectedCases.size} selected
              </button>
            )}
          </div>
          
          <p className="text-sm text-gray-500">
            {cases.length} {cases.length === 1 ? 'case' : 'cases'}
          </p>
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
                      onSave={async () => {
                        // TODO: Implement save logic with updates
                        setEditingCase(null);
                        onCaseUpdated();
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
                    onClick={() => setEditingCase(testCase.id)}
                    className="text-gray-400 hover:text-gray-600"
                    title="Edit case"
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
          <h4 className="text-sm font-medium text-gray-900 mb-3">Input Parameters</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(parameters).map(([key, value]) => (
              <div
                key={key}
                className="bg-blue-50 border border-blue-200 rounded-lg p-3"
              >
                <span className="text-xs font-medium text-blue-800 uppercase tracking-wider block mb-1">
                  {key.replace(/_/g, ' ')}
                </span>
                <p className="text-sm text-blue-900 font-medium">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expected Output */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Expected Output</h4>
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-900 whitespace-pre-wrap">{outputText}</p>
        </div>
      </div>

      {/* View Full Prompt Button */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowFullPrompt(true)}
          className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
        >
          View Full Prompt
        </button>
      </div>

      {/* Full Prompt Modal */}
      {showFullPrompt && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowFullPrompt(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Full Prompt with Parameter Substitutions</h3>
                <button
                  onClick={() => setShowFullPrompt(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-120px)]">
              {sessionContext.generation_method === 'prompt_lab_prompt' && sessionContext.prompt_lab_name && (
                <div className="mb-4">
                  <span className="text-sm text-purple-600 font-medium">From Prompt Lab: {sessionContext.prompt_lab_name}</span>
                </div>
              )}
              
              <div className="space-y-4">
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
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowFullPrompt(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
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

  // Extract parameters from context or try to parse from input_text
  const parameters = testCase.context || {};
  const hasParameters = Object.keys(parameters).length > 0;

  return (
    <>
      {/* Input Parameters - Main Display */}
      {hasParameters && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Input Parameters</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(parameters).map(([key, value]) => (
              <div
                key={key}
                className="bg-blue-50 border border-blue-200 rounded-lg p-3"
              >
                <span className="text-xs font-medium text-blue-800 uppercase tracking-wider block mb-1">
                  {key.replace(/_/g, ' ')}
                </span>
                <p className="text-sm text-blue-900 font-medium">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expected Output */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Expected Output</h4>
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-900 whitespace-pre-wrap">{testCase.expected_output}</p>
        </div>
      </div>

      {/* View Full Prompt Button */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowFullPrompt(true)}
          className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
        >
          View Full Prompt
        </button>
      </div>

      {/* Full Prompt Modal */}
      {showFullPrompt && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowFullPrompt(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Full Prompt with Parameter Substitutions</h3>
                <button
                  onClick={() => setShowFullPrompt(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Complete Prompt</h4>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{testCase.input_text}</pre>
                  </div>
                </div>
                
                {dataset.prompt_lab_id && (
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="text-gray-600">From prompt lab:</span>
                    <button
                      onClick={() => {
                        setShowFullPrompt(false);
                        window.location.href = `/prompt-labs/${dataset.prompt_lab_id}`;
                      }}
                      className="text-purple-600 hover:text-purple-800 hover:underline font-medium"
                    >
                      View Prompt Lab →
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowFullPrompt(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
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
    input_text: testCase.input_text,
    expected_output: testCase.expected_output,
    context: JSON.stringify(testCase.context || {}, null, 2),
  });

  const handleSubmit = async () => {
    try {
      await onSave({
        input_text: formData.input_text,
        expected_output: formData.expected_output,
        context: JSON.parse(formData.context),
      });
    } catch (err) {
      console.error('Error saving case:', err);
    }
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-700">Input</label>
        <textarea
          value={formData.input_text}
          onChange={(e) => setFormData({ ...formData, input_text: e.target.value })}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">Expected Output</label>
        <textarea
          value={formData.expected_output}
          onChange={(e) => setFormData({ ...formData, expected_output: e.target.value })}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">Context (JSON)</label>
        <textarea
          value={formData.context}
          onChange={(e) => setFormData({ ...formData, context: e.target.value })}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
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
  setActiveTab: (tab: 'cases' | 'quick-generate' | 'curated-generation') => void;
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
        persistImmediately
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

// Quick Generate Tab Component - Machine-only generation with immediate persistence
const QuickGenerateTab: React.FC<GenerateCasesTabProps> = ({ datasetId, dataset, parameters, onCasesAdded, setActiveTab }) => {
  const [template, setTemplate] = useState('');
  const [count, setCount] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useSessionPrompt, setUseSessionPrompt] = useState(true);
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
        false, // No output variations for quick generate
        3,
        true // Always persist immediately for quick generate
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

// Curated Generation Tab Component - Human-in-the-loop generation with output variations
const CuratedGenerationTab: React.FC<GenerateCasesTabProps> = ({ datasetId, dataset, parameters, onCasesAdded, setActiveTab }) => {
  // This is essentially the original GenerateCasesTab with variations always enabled and persistence never immediate
  const [template, setTemplate] = useState('');
  const [count, setCount] = useState(5);
  const [previews, setPreviews] = useState<CasePreview[]>([]);
  const [selectedPreviews, setSelectedPreviews] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useSessionPrompt, setUseSessionPrompt] = useState(true);
  const [variationsCount, setVariationsCount] = useState(3);
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
        true, // Always enable output variations for curated generation
        variationsCount,
        false // Never persist immediately for curated generation
      );
      setPreviews(result.previews);
      
      // Initialize cases with variations
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
      setActiveTab('cases'); // Switch to cases tab after adding
    } catch (err) {
      setError('Failed to add cases with variations');
      console.error('Error adding cases with variations:', err);
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
      {/* Info Box */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg className="h-5 w-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-purple-900">Curated Generation Mode</h4>
            <p className="text-sm text-purple-700 mt-1">
              Generate evaluation cases with multiple output variations to choose from. Select the best outputs for each case or write your own custom outputs before saving.
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

      {/* Variations Count Selector */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label className="block text-sm font-medium text-blue-900">
          Number of Output Variations per Case
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
            {generating ? 'Generating...' : `Generate ${count} Case${count !== 1 ? 's' : ''} with Variations`}
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
                Generating {count} evaluation case{count !== 1 ? 's' : ''} with {variationsCount} variations each...
              </p>
            </div>
          </div>
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
          </div>

          <div className="space-y-6">
            {previews.map((preview, index) => {
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
            })}
          </div>
        </div>
      )}
    </div>
  );
};


export default EvaluationDatasetDetail;