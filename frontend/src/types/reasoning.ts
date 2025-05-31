export interface ReasoningFactor {
  id: number;
  text: string;
  confidence: number;
  rating_stats: {
    likes: number;
    dislikes: number;
    total_ratings: number;
  };
}

export interface DraftReasoningFactors {
  draft_id: number;
  reasoning_factors: ReasoningFactor[];
}

export interface ReasonRating {
  [reasonId: string]: boolean; // true for like, false for dislike
}

export interface BulkRateRequest {
  action: 'accept' | 'reject' | 'edit' | 'ignore';
  reason: string;
  reason_ratings: ReasonRating;
  edited_content?: string;
}

export interface QuickRateRequest {
  liked: boolean;
  create_feedback?: boolean;
}

export interface BulkRateResponse {
  feedback_id: number;
  action: string;
  reasons_rated: number;
  draft_id: number;
}

export interface QuickRateResponse {
  success: boolean;
  reason_id: number;
  liked: boolean;
  feedback_created?: boolean;
}