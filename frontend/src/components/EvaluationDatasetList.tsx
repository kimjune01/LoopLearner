/**
 * Evaluation Dataset List Component
 * Displays all evaluation datasets with search, filter, and actions
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import { promptLabService } from '../services/promptLabService';
import { generateDatasetNameAndDescription } from '../utils/nameGenerator';
import type { EvaluationDataset } from '../types/evaluation';
import type { PromptLab } from '../types/promptLab';

const EvaluationDatasetList: React.FC = () => {
  const navigate = useNavigate();
  const { promptLabId } = useParams<{ promptLabId: string }>();
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [promptLab, setPromptLab] = useState<PromptLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterByParams, setFilterByParams] = useState(!!promptLabId);

  useEffect(() => {
    loadDatasets();
    if (promptLabId) {
      loadPromptLab();
    }
  }, [promptLabId, filterByParams]);

  const loadPromptLab = async () => {
    if (!promptLabId) return;
    
    try {
      const promptLabData = await promptLabService.getPromptLab(promptLabId);
      setPromptLab(promptLabData);
    } catch (err) {
      console.error('Error loading prompt lab:', err);
    }
  };

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await evaluationService.getDatasets(promptLabId, filterByParams);
      setDatasets(data);
      setError(null);
    } catch (err) {
      setError('Failed to load evaluation datasets');
      console.error('Error loading datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (datasetId: number) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) {
      return;
    }

    try {
      await evaluationService.deleteDataset(datasetId);
      await loadDatasets();
    } catch (err) {
      setError('Failed to delete dataset');
      console.error('Error deleting dataset:', err);
    }
  };

  const filteredDatasets = datasets.filter(dataset =>
    dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dataset.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          {promptLabId && (
            <div className="mb-4">
              <button
                onClick={() => navigate(`/prompt-labs/${promptLabId}`)}
                className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
              >
                <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Session
              </button>
            </div>
          )}
          
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {promptLabId ? `Evaluation Datasets for Prompt Lab` : 'Evaluation Datasets'}
              </h1>
              {promptLab && (
                <h2 className="text-xl text-purple-600 font-medium mt-1">{promptLab.name}</h2>
              )}
              <p className="mt-2 text-gray-600">
                {promptLabId 
                  ? 'Datasets compatible with your session\'s prompt parameters'
                  : 'Manage test datasets for evaluating prompt performance'
                }
              </p>
              
              {promptLabId && promptLab?.active_prompt?.parameters && promptLab.active_prompt.parameters.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm text-gray-700 mb-2">Prompt lab parameters:</p>
                  <div className="flex flex-wrap gap-2">
                    {promptLab.active_prompt.parameters.map((param: string) => (
                      <span
                        key={param}
                        className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800"
                      >
                        {param}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Actions Bar */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search datasets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64 rounded-lg border border-gray-300 px-4 py-2 pl-10 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
              <svg
                className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            
            {promptLabId && (
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filterByParams}
                  onChange={(e) => setFilterByParams(e.target.checked)}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-700">Filter by parameters</span>
              </label>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>New Dataset</span>
            </button>
          </div>
        </div>

        {/* Dataset Grid */}
        {filteredDatasets.length === 0 ? (
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
            <h3 className="mt-2 text-sm font-medium text-gray-900">No datasets found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'Try adjusting your search' : 'Get started by creating a new dataset'}
            </p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredDatasets.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onDelete={() => handleDelete(dataset.id)}
                onClick={() => navigate(`/evaluation/datasets/${dataset.id}`)}
              />
            ))}
          </div>
        )}

        {/* Create Dataset Modal */}
        {showCreateModal && (
          <CreateDatasetModal
            promptLabId={promptLabId}
            promptLab={promptLab}
            onClose={() => setShowCreateModal(false)}
            onCreated={(datasetId: number) => {
              setShowCreateModal(false);
              navigate(`/evaluation/datasets/${datasetId}`);
            }}
          />
        )}
      </div>
    </div>
  );
};

// Dataset Card Component
interface DatasetCardProps {
  dataset: EvaluationDataset;
  onClick: () => void;
  onDelete: () => void;
}

const DatasetCard: React.FC<DatasetCardProps> = ({ dataset, onClick, onDelete }) => {
  const navigate = useNavigate();
  
  return (
    <div className="card-elevated group cursor-pointer" onClick={onClick}>
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600">
              {dataset.name}
            </h3>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {dataset.description}
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="ml-2 p-1 text-gray-400 hover:text-red-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center">
            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {dataset.case_count || 0} cases
          </div>
          {dataset.average_score !== undefined && (
            <div className="flex items-center">
              <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              {(dataset.average_score * 100).toFixed(1)}% avg
            </div>
          )}
          {dataset.prompt_lab_id && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/sessions/${dataset.prompt_lab_id}`);
              }}
              className="flex items-center text-purple-600 hover:text-purple-800 transition-colors"
            >
              <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              Prompt Lab
            </button>
          )}
        </div>

        {/* Parameters */}
        {dataset.parameters && dataset.parameters.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-2">
              {dataset.parameters.slice(0, 3).map((param) => (
                <span
                  key={param}
                  className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800"
                >
                  {param}
                </span>
              ))}
              {dataset.parameters.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{dataset.parameters.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Create Dataset Modal Component
interface CreateDatasetModalProps {
  promptLabId?: string;
  promptLab?: PromptLab | null;
  onClose: () => void;
  onCreated: (datasetId: number) => void;
}

const CreateDatasetModal: React.FC<CreateDatasetModalProps> = ({ promptLabId, promptLab, onClose, onCreated }) => {
  // Auto-generate initial name and description
  const initialData = generateDatasetNameAndDescription();
  
  // Get prompt lab parameters if available
  const promptLabParameters = promptLab?.active_prompt?.parameters || [];
  
  const [name, setName] = useState(initialData.name);
  const [description, setDescription] = useState(initialData.description);
  const [isEditingName, setIsEditingName] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateNewName = () => {
    const newData = generateDatasetNameAndDescription();
    setName(newData.name);
    setDescription(newData.description);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !description) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      
      const datasetData = {
        name,
        description,
        parameters: promptLabParameters,
        parameter_descriptions: {},
        prompt_lab_id: promptLabId,
      };
      
      const createdDataset = await evaluationService.createDataset(datasetData);
      onCreated(createdDataset.id);
    } catch (err) {
      setError('Failed to create dataset');
      console.error('Error creating dataset:', err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        
        <div className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Create Evaluation Dataset</h3>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Title Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Dataset Name
              </label>
              
              {isEditingName ? (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="flex-1 text-lg font-bold text-gray-900 border-0 border-b-2 border-purple-500 focus:outline-none focus:border-purple-600 bg-transparent"
                    autoFocus
                    onBlur={() => setIsEditingName(false)}
                    onKeyPress={(e) => e.key === 'Enter' && setIsEditingName(false)}
                  />
                  <button
                    type="button"
                    onClick={() => setIsEditingName(false)}
                    className="text-green-600 hover:text-green-700"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-bold text-gray-900">{name}</h4>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setIsEditingName(true)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Edit name"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={handleGenerateNewName}
                      className="text-gray-400 hover:text-gray-600"
                      title="Generate new name"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Description Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                placeholder="Describe what this dataset will be used for..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="btn-primary"
              >
                {creating ? 'Creating...' : 'Create Dataset'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EvaluationDatasetList;