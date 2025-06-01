export interface SystemPrompt {
  id: number;
  prompt_lab: string;
  content: string;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  parameters: string[];
  performance_score: number | null;
}

export interface PromptLab {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  optimization_iterations: number;
  total_emails_processed: number;
  total_feedback_collected: number;
  active_prompt?: {
    id: string | null;
    version: number | null;
    content: string | null;
    parameters?: string[];
  };
  recent_emails?: Array<{
    id: number;
    subject: string;
    created_at: string;
    scenario_type: string;
  }>;
  prompts?: SystemPrompt[];
}

export interface PromptLabListResponse {
  prompt_labs: PromptLab[];
  count: number;
}

export interface PromptLabStats {
  prompt_lab_id: string;
  prompt_lab_name: string;
  created_at: string;
  updated_at: string;
  optimization_iterations: number;
  prompts: {
    total_versions: number;
    current_version: number;
    current_performance_score: number | null;
  };
  emails: {
    total_processed: number;
    synthetic_generated: number;
    real_emails: number;
  };
  drafts: {
    total_generated: number;
    average_per_email: number;
  };
  feedback: {
    total_collected: number;
    by_action: {
      accept: number;
      reject: number;
      edit: number;
      ignore: number;
    };
    feedback_rate: number;
  };
  preferences_count: number;
}

export interface CreatePromptLabRequest {
  name: string;
  description?: string;
  initial_prompt?: string;
}

export interface UpdatePromptLabRequest {
  name?: string;
  description?: string;
}

export interface DuplicatePromptLabRequest {
  name: string;
  description?: string;
  copy_emails?: boolean;
}