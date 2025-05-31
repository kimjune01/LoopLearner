/**
 * Evaluation Dataset List Component
 * Displays all evaluation datasets with search, filter, and actions
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { evaluationService } from '../services/evaluationService';
import type { EvaluationDataset } from '../types/evaluation';

const EvaluationDatasetList: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await evaluationService.getDatasets();
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
          <h1 className="text-3xl font-bold text-gray-900">Evaluation Datasets</h1>
          <p className="mt-2 text-gray-600">
            Manage test datasets for evaluating prompt performance
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Actions Bar */}
        <div className="mb-6 flex items-center justify-between">
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
            onClose={() => setShowCreateModal(false)}
            onCreated={() => {
              setShowCreateModal(false);
              loadDatasets();
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
  onClose: () => void;
  onCreated: () => void;
}

const CreateDatasetModal: React.FC<CreateDatasetModalProps> = ({ onClose, onCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parameters: [] as string[],
    parameter_descriptions: {} as Record<string, string>,
  });
  const [newParam, setNewParam] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddParameter = () => {
    if (newParam && !formData.parameters.includes(newParam)) {
      setFormData({
        ...formData,
        parameters: [...formData.parameters, newParam],
      });
      setNewParam('');
    }
  };

  const handleRemoveParameter = (param: string) => {
    setFormData({
      ...formData,
      parameters: formData.parameters.filter(p => p !== param),
      parameter_descriptions: Object.fromEntries(
        Object.entries(formData.parameter_descriptions).filter(([key]) => key !== param)
      ),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.description) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      await evaluationService.createDataset(formData);
      onCreated();
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
        
        <div className="relative w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          <h3 className="text-lg font-medium text-gray-900">Create Evaluation Dataset</h3>
          
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                placeholder="Customer Support Evaluation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                placeholder="Test cases for evaluating customer support email responses"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Parameters
              </label>
              <div className="mt-1 flex space-x-2">
                <input
                  type="text"
                  value={newParam}
                  onChange={(e) => setNewParam(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddParameter())}
                  className="block flex-1 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                  placeholder="customer_name"
                />
                <button
                  type="button"
                  onClick={handleAddParameter}
                  className="rounded-md bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700"
                >
                  Add
                </button>
              </div>
              
              {formData.parameters.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {formData.parameters.map((param) => (
                    <span
                      key={param}
                      className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800"
                    >
                      {param}
                      <button
                        type="button"
                        onClick={() => handleRemoveParameter(param)}
                        className="ml-2 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3">
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