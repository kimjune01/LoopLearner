export interface EmailMessage {
  id: string;
  subject: string;
  body: string;
  sender: string;
  timestamp: string;
}

export interface DraftReason {
  text: string;
  confidence: number;
}

export interface EmailDraft {
  id: string;
  content: string;
  reasons: DraftReason[];
}

export interface FeedbackAction {
  action: 'accept' | 'reject' | 'edit' | 'ignore';
  reason?: string;
  edited_content?: string;
}

export interface UserFeedback {
  email_id: string;
  draft_id: string;
  action: FeedbackAction;
  reason_ratings: Record<string, boolean>;
  timestamp: string;
}