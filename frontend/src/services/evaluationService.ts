/**
 * Evaluation Dataset API Service
 */

import { API_BASE_URL } from './api';
import type { 
  EvaluationDataset, 
  EvaluationCase, 
  EvaluationRun,
  EvaluationResult,
  DatasetCompatibility,
  CasePreview,
  DatasetImportData
} from '../types/evaluation';

const EVALUATION_API_URL = `${API_BASE_URL}/evaluations`;

export const evaluationService = {
  // Dataset operations
  async getDatasets(): Promise<EvaluationDataset[]> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation datasets');
    }
    const data = await response.json();
    return data.datasets || [];
  },

  async getDataset(datasetId: number): Promise<EvaluationDataset> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/`);
    if (!response.ok) {
      throw new Error('Failed to fetch dataset details');
    }
    return response.json();
  },

  async createDataset(dataset: Partial<EvaluationDataset>): Promise<EvaluationDataset> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dataset),
    });
    if (!response.ok) {
      throw new Error('Failed to create dataset');
    }
    return response.json();
  },

  async updateDataset(datasetId: number, updates: Partial<EvaluationDataset>): Promise<EvaluationDataset> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update dataset');
    }
    return response.json();
  },

  async deleteDataset(datasetId: number): Promise<void> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete dataset');
    }
  },

  // Case operations
  async getCases(datasetId: number): Promise<EvaluationCase[]> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/cases/`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation cases');
    }
    const data = await response.json();
    return data.cases || [];
  },

  async createCase(datasetId: number, caseData: Partial<EvaluationCase>): Promise<EvaluationCase> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/cases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(caseData),
    });
    if (!response.ok) {
      throw new Error('Failed to create case');
    }
    return response.json();
  },

  async updateCase(datasetId: number, caseId: number, updates: Partial<EvaluationCase>): Promise<EvaluationCase> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/cases/${caseId}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update case');
    }
    return response.json();
  },

  async deleteCase(datasetId: number, caseId: number): Promise<void> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/cases/${caseId}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete case');
    }
  },

  // Case generation
  async generateCases(datasetId: number, template: string, count: number = 5): Promise<CasePreview[]> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/generate-cases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ template, count }),
    });
    if (!response.ok) {
      throw new Error('Failed to generate cases');
    }
    const data = await response.json();
    return data.previews || [];
  },

  async addSelectedCases(datasetId: number, previewIds: string[]): Promise<{ added_count: number }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/add-selected-cases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ preview_ids: previewIds }),
    });
    if (!response.ok) {
      throw new Error('Failed to add selected cases');
    }
    return response.json();
  },

  async regenerateCase(datasetId: number, previewId: string): Promise<CasePreview> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/regenerate-case/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ preview_id: previewId }),
    });
    if (!response.ok) {
      throw new Error('Failed to regenerate case');
    }
    const data = await response.json();
    return data.preview;
  },

  async editCaseParameters(previewId: string, parameters: Record<string, string>): Promise<CasePreview> {
    const response = await fetch(`${EVALUATION_API_URL}/cases/preview/${previewId}/parameters/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ parameters }),
    });
    if (!response.ok) {
      throw new Error('Failed to edit case parameters');
    }
    const data = await response.json();
    return data.preview;
  },

  async regenerateCaseOutput(previewId: string): Promise<CasePreview> {
    const response = await fetch(`${EVALUATION_API_URL}/cases/preview/${previewId}/regenerate-output/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to regenerate case output');
    }
    const data = await response.json();
    return data.preview;
  },

  // Import/Export
  async importDataset(datasetId: number, importData: DatasetImportData): Promise<{ imported_count: number }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/import/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(importData),
    });
    if (!response.ok) {
      throw new Error('Failed to import dataset');
    }
    return response.json();
  },

  async exportDataset(datasetId: number): Promise<DatasetImportData> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/export/`);
    if (!response.ok) {
      throw new Error('Failed to export dataset');
    }
    return response.json();
  },

  // Compatibility checking
  async checkCompatibility(datasetId: number, sessionId: string): Promise<DatasetCompatibility> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/compatibility/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!response.ok) {
      throw new Error('Failed to check compatibility');
    }
    return response.json();
  },

  async migrateDataset(datasetId: number, sessionId: string): Promise<{ migrated: boolean; new_dataset_id?: number }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/migrate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!response.ok) {
      throw new Error('Failed to migrate dataset');
    }
    return response.json();
  },

  // Evaluation runs
  async runEvaluation(datasetId: number, promptId: number): Promise<EvaluationRun> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/run/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt_id: promptId }),
    });
    if (!response.ok) {
      throw new Error('Failed to start evaluation run');
    }
    return response.json();
  },

  async getEvaluationRuns(datasetId: number): Promise<EvaluationRun[]> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/runs/`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation runs');
    }
    const data = await response.json();
    return data.runs || [];
  },

  async getEvaluationResults(runId: number): Promise<EvaluationResult[]> {
    const response = await fetch(`${EVALUATION_API_URL}/runs/${runId}/results/`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation results');
    }
    const data = await response.json();
    return data.results || [];
  },
};