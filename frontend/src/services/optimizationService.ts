import { api } from './api';

export interface OptimizationStatus {
  status: string;
  progress?: number;
  current_step?: string;
}

export interface OptimizationDataset {
  id: number;
  name: string;
  description: string;
  case_count: number;
  parameters: string[];
  human_reviewed: boolean;
  quality_score: number;
}

export interface OptimizationResult {
  status: string;
  optimization_id: string;
  improvement: number;
  datasets_used: number;
  message: string;
  run_id?: string; // Add run_id for navigation
}

export interface TriggerOptimizationRequest {
  prompt_lab_id: string;
  dataset_ids: number[];
  force?: boolean;
}

export class OptimizationService {
  /**
   * Trigger dataset-based prompt optimization
   */
  async triggerOptimizationWithDatasets(request: TriggerOptimizationRequest): Promise<OptimizationResult> {
    try {
      console.log('Triggering optimization with request:', request);
      const response = await api.post('/optimization/trigger-with-dataset/', request);
      console.log('Optimization response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Optimization API error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new Error(error.response?.data?.detail || error.response?.data?.error || 'Optimization failed');
    }
  }

  /**
   * Get available datasets for optimization for a specific prompt lab
   */
  async getOptimizationDatasets(promptLabId: string): Promise<OptimizationDataset[]> {
    const response = await api.get(`/evaluations/prompt-labs/${promptLabId}/optimization-datasets/`);
    return response.data;
  }

  /**
   * Trigger prompt optimization cycle (legacy method)
   */
  async triggerOptimization(): Promise<void> {
    const response = await api.post('/optimization/trigger/');
    return response.data;
  }

  /**
   * Get current optimization status
   */
  async getOptimizationStatus(optimizationId?: string): Promise<OptimizationStatus> {
    const url = optimizationId 
      ? `/optimization/${optimizationId}/status/`
      : '/learning/progress/';
    const response = await api.get(url);
    return response.data;
  }

  /**
   * Get optimization run details
   */
  async getOptimizationRun(runId: string): Promise<any> {
    try {
      const response = await api.get(`/optimization/runs/${runId}/`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching optimization run:', error);
      throw new Error(error.response?.data?.error || 'Failed to fetch optimization run details');
    }
  }
}

export const optimizationService = new OptimizationService();