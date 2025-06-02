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
  prompt_lab_id?: string;
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
  id?: number;
  run_id?: number; // Backend sometimes returns run_id instead of id
  dataset: number;
  prompt: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
  // Additional fields for run history
  total_cases?: number;
  passed_cases?: number;
  failed_cases?: number;
  pass_rate?: number;
  avg_similarity_score?: number;
  prompt_version?: number;
  prompt_id?: number;
  duration_seconds?: number | null;
}

export interface EvaluationResult {
  id: number;
  run: number;
  case: number;
  case_id?: number;
  case_number?: number;
  input_text?: string;
  expected_output?: string;
  generated_output: string;
  similarity_score: number;
  passed: boolean;
  details: Record<string, any>;
  case_context?: any;
  performance_tier?: string;
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
  template?: string;
  parameters: Record<string, string>;
  // PromptLab-based generation fields
  input_text?: string;
  expected_output?: string;
  // Template-based generation fields  
  generated_input?: string;
  generated_output?: string;
  // Output variations
  output_variations?: Array<{
    index: number;
    text: string;
    style: string;
  }>;
  selected_output_index?: number | null;
  custom_output?: string | null;
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