/**
 * Types for Evaluation Datasets and Cases
 */

export interface EvaluationDataset {
  id: number;
  name: string;
  description: string;
  parameters: string[];
  parameter_descriptions: Record<string, string>;
  created_at: string;
  updated_at: string;
  case_count?: number;
  last_run?: string;
  average_score?: number;
}

export interface EvaluationCase {
  id: number;
  dataset: number;
  input_text: string;
  expected_output: string;
  context: Record<string, any>;
  created_at: string;
}

export interface EvaluationRun {
  id: number;
  dataset: number;
  prompt: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface EvaluationResult {
  id: number;
  run: number;
  case: number;
  generated_output: string;
  similarity_score: number;
  passed: boolean;
  details: Record<string, any>;
}

export interface DatasetCompatibility {
  is_compatible: boolean;
  missing_parameters: string[];
  extra_parameters: string[];
  compatibility_score: number;
  migration_possible: boolean;
  migration_suggestions: string[];
}

export interface CasePreview {
  preview_id: string;
  template: string;
  parameters: Record<string, string>;
  generated_input: string;
  generated_output: string;
  dataset_id: number;
}

export interface DatasetImportData {
  name: string;
  description: string;
  parameters: string[];
  parameter_descriptions: Record<string, string>;
  cases: Array<{
    input_text: string;
    expected_output: string;
    context?: Record<string, any>;
  }>;
}