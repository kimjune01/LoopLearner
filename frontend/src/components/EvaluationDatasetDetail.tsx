/**
 * Evaluation Dataset Detail Component
 * Shows dataset details, cases, and allows case management
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import type { EvaluationDataset, EvaluationCase, CasePreview } from '../types/evaluation';

const EvaluationDatasetDetail: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();
  
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cases' | 'generate' | 'settings'>('cases');
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
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{dataset.name}</h1>
              <p className="mt-2 text-gray-600">{dataset.description}</p>
              
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
              onClick={() => setActiveTab('generate')}
              className={`${
                activeTab === 'generate'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Generate Cases
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`${
                activeTab === 'settings'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
            >
              Settings
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
          />
        )}

        {activeTab === 'generate' && (
          <GenerateCasesTab
            datasetId={Number(datasetId)}
            parameters={dataset.parameters}
            onCasesAdded={loadCases}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsTab
            dataset={dataset}
            onUpdated={loadDataset}
            onDeleted={() => navigate('/evaluation/datasets')}
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
}

const CasesTab: React.FC<CasesTabProps> = ({
  cases,
  selectedCases,
  onToggleSelection,
  onSelectAll,
  onDeleteCase,
  onDeleteSelected,
  onCaseUpdated,
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
                    <>
                      <div className="mb-2">
                        <h4 className="text-sm font-medium text-gray-900">Input:</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{testCase.input_text}</p>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">Expected Output:</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{testCase.expected_output}</p>
                      </div>
                      
                      {testCase.context && Object.keys(testCase.context).length > 0 && (
                        <div className="mt-2">
                          <h4 className="text-sm font-medium text-gray-900">Context:</h4>
                          <pre className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            {JSON.stringify(testCase.context, null, 2)}
                          </pre>
                        </div>
                      )}
                    </>
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
  parameters: string[];
  onCasesAdded: () => void;
}

const GenerateCasesTab: React.FC<GenerateCasesTabProps> = ({ datasetId, parameters, onCasesAdded }) => {
  const [template, setTemplate] = useState('');
  const [count, setCount] = useState(5);
  const [previews, setPreviews] = useState<CasePreview[]>([]);
  const [selectedPreviews, setSelectedPreviews] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!template.trim()) {
      setError('Please enter a template');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const data = await evaluationService.generateCases(datasetId, template, count);
      setPreviews(data);
      setSelectedPreviews(new Set(data.map(p => p.preview_id)));
    } catch (err) {
      setError('Failed to generate cases');
      console.error('Error generating cases:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleAddSelected = async () => {
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
  };

  return (
    <div className="space-y-6">
      {/* Template Input */}
      <div>
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
          disabled={generating || !template.trim()}
          className="btn-primary"
        >
          {generating ? 'Generating...' : 'Generate Cases'}
        </button>
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
            <button
              onClick={handleAddSelected}
              disabled={selectedPreviews.size === 0}
              className="btn-primary"
            >
              Add {selectedPreviews.size} Selected Cases
            </button>
          </div>

          <div className="space-y-4">
            {previews.map((preview) => (
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
                    <div className="mb-2">
                      <h4 className="text-sm font-medium text-gray-900">Input:</h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{preview.generated_input}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Expected Output:</h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{preview.generated_output}</p>
                    </div>
                    
                    {/* Show parameters used */}
                    {Object.keys(preview.parameters).length > 0 && (
                      <div className="mt-2">
                        <h4 className="text-sm font-medium text-gray-900">Parameters:</h4>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {Object.entries(preview.parameters).map(([key, value]) => (
                            <span
                              key={key}
                              className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded"
                            >
                              {key}: {value}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
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
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Settings Tab Component
interface SettingsTabProps {
  dataset: EvaluationDataset;
  onUpdated: () => void;
  onDeleted: () => void;
}

const SettingsTab: React.FC<SettingsTabProps> = ({ dataset, onUpdated, onDeleted }) => {
  const [formData, setFormData] = useState({
    name: dataset.name,
    description: dataset.description,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await evaluationService.updateDataset(dataset.id, formData);
      onUpdated();
    } catch (err) {
      setError('Failed to update dataset');
      console.error('Error updating dataset:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this dataset? This cannot be undone.')) {
      return;
    }

    try {
      await evaluationService.deleteDataset(dataset.id);
      onDeleted();
    } catch (err) {
      setError('Failed to delete dataset');
      console.error('Error deleting dataset:', err);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700">Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        />
      </div>

      <div className="flex items-center justify-between pt-6">
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>

        <button
          onClick={handleDelete}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Delete Dataset
        </button>
      </div>
    </div>
  );
};

export default EvaluationDatasetDetail;