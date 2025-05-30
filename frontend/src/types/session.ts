export interface Session {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  optimization_iterations: number;
  total_emails_processed: number;
  total_feedback_collected: number;
}

export interface SessionListResponse {
  sessions: Session[];
  count: number;
}

export interface SessionStats {
  session_id: string;
  session_name: string;
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

export interface CreateSessionRequest {
  name: string;
  description?: string;
  initial_prompt?: string;
}

export interface UpdateSessionRequest {
  name?: string;
  description?: string;
}

export interface DuplicateSessionRequest {
  name: string;
  description?: string;
  copy_emails?: boolean;
}