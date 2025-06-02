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
  async getDatasets(promptLabId?: string, filterByParams?: boolean): Promise<EvaluationDataset[]> {
    const url = new URL(`${EVALUATION_API_URL}/datasets/`);
    if (promptLabId) {
      url.searchParams.append('prompt_lab_id', promptLabId);
    }
    if (filterByParams !== undefined) {
      url.searchParams.append('filter_by_params', filterByParams.toString());
    }
    
    const response = await fetch(url.toString());
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
  async generateCases(datasetId: number, template: string, count: number = 5, usePromptLabPrompt: boolean = false, generateOutputVariations: boolean = false, variationsCount: number = 3, persistImmediately: boolean = false, maxTokens: number = 500): Promise<{ previews: CasePreview[], persisted_count?: number, generation_method: string, prompt_lab_name?: string, prompt_content?: string, prompt_parameters?: string[], supports_variations?: boolean }> {
    const requestBody: any = { 
      template, 
      count, 
      use_prompt_lab_prompt: usePromptLabPrompt,
      persist_immediately: persistImmediately,
      max_tokens: maxTokens
    };
    
    if (generateOutputVariations) {
      requestBody.generate_output_variations = true;
      requestBody.variations_count = variationsCount;
    }
    
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/generate-cases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    if (!response.ok) {
      throw new Error('Failed to generate cases');
    }
    const data = await response.json();
    return {
      previews: data.previews || data.generated_cases || [],
      persisted_count: data.persisted_count || 0,
      generation_method: data.generation_method || 'template',
      prompt_lab_name: data.prompt_lab_name,
      prompt_content: data.prompt_content,
      prompt_parameters: data.prompt_parameters || [],
      supports_variations: data.supports_variations || false
    };
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

  async addSelectedCasesWithVariations(datasetId: number, casesData: Array<{
    preview_id: string;
    input_text: string;
    parameters: Record<string, any>;
    selected_output_index?: number | null;
    custom_output?: string | null;
    output_variations?: Array<{ index: number; text: string; style: string }>;
  }>): Promise<{ added_count: number; added_cases?: any[] }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/add-selected-cases/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ cases: casesData }),
    });
    if (!response.ok) {
      throw new Error('Failed to add selected cases with variations');
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
  async checkCompatibility(datasetId: number, promptLabId: string): Promise<DatasetCompatibility> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/compatibility/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt_lab_id: promptLabId }),
    });
    if (!response.ok) {
      throw new Error('Failed to check compatibility');
    }
    return response.json();
  },

  async migrateDataset(datasetId: number, promptLabId: string): Promise<{ migrated: boolean; new_dataset_id?: number }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/migrate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt_lab_id: promptLabId }),
    });
    if (!response.ok) {
      throw new Error('Failed to migrate dataset');
    }
    return response.json();
  },

  // Evaluation runs
  async runEvaluation(datasetId: number, promptId: number): Promise<EvaluationRun> {
    const response = await fetch(`${EVALUATION_API_URL}/run/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ dataset_id: datasetId, prompt_id: promptId }),
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
    const response = await fetch(`${API_BASE_URL}/evaluations/runs/${runId}/results/`);
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation results');
    }
    const data = await response.json();
    return data.results || [];
  },

  async getDetailedEvaluationResults(runId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/evaluations/runs/${runId}/results/`);
    if (!response.ok) {
      throw new Error('Failed to fetch detailed evaluation results');
    }
    return response.json();
  },

  async deleteEvaluationRun(runId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/evaluations/runs/${runId}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete evaluation run');
    }
  },

  async deleteAllEvaluationRuns(datasetId: number): Promise<{ deleted_count: number }> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/runs/delete-all/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete all evaluation runs');
    }
    return response.json();
  },

  // Draft case operations
  async getDrafts(datasetId: number): Promise<any[]> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/drafts/`);
    if (!response.ok) {
      throw new Error('Failed to fetch draft cases');
    }
    const data = await response.json();
    return data.drafts || [];
  },

  async promoteDraft(datasetId: number, draftId: number, selectedOutputIndex?: number, customOutput?: string): Promise<any> {
    const requestBody: any = {};
    if (selectedOutputIndex !== undefined) {
      requestBody.selected_output_index = selectedOutputIndex;
    }
    if (customOutput) {
      requestBody.custom_output = customOutput;
    }

    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/drafts/${draftId}/promote/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    if (!response.ok) {
      throw new Error('Failed to promote draft case');
    }
    return response.json();
  },

  async discardDraft(datasetId: number, draftId: number, reason?: string): Promise<void> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/drafts/${draftId}/discard/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ reason: reason || 'Not suitable' }),
    });
    if (!response.ok) {
      throw new Error('Failed to discard draft case');
    }
  },

  async getDraftStatus(): Promise<any> {
    const response = await fetch(`${EVALUATION_API_URL}/drafts/status/`);
    if (!response.ok) {
      throw new Error('Failed to fetch draft status');
    }
    return response.json();
  },

  async triggerDraftGeneration(datasetId: number): Promise<any> {
    const response = await fetch(`${EVALUATION_API_URL}/datasets/${datasetId}/drafts/generate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to trigger draft generation');
    }
    return response.json();
  },
};