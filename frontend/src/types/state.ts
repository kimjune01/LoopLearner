export interface SystemPrompt {
  content: string;
  version: number;
  created_at: string;
}

export interface EvaluationSnapshot {
  id: string;
  email_id: string;
  expected_outcome: string;
  prompt_version: number;
  performance_score: number;
  created_at: string;
}

export interface UserPreference {
  key: string;
  value: string;
  description: string;
  created_at: string;
}

export interface SystemState {
  current_prompt: SystemPrompt;
  user_preferences: UserPreference[];
  evaluation_snapshots: EvaluationSnapshot[];
  optimization_history: Record<string, any>[];
  confidence_score: number;
  last_updated: string;
}