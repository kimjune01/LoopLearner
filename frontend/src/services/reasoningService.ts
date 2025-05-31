import { api } from './api';
import type { 
  DraftReasoningFactors, 
  BulkRateRequest, 
  BulkRateResponse, 
  QuickRateRequest, 
  QuickRateResponse 
} from '../types/reasoning';

export class ReasoningService {
  /**
   * Get reasoning factors for a specific draft
   */
  async getReasoningFactors(sessionId: string, draftId: number): Promise<DraftReasoningFactors> {
    const response = await api.get(`/sessions/${sessionId}/drafts/${draftId}/reasoning-factors/`);
    return response.data;
  }

  /**
   * Bulk accept all reasoning factors for a draft
   */
  async bulkAcceptReasons(sessionId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    const response = await api.post(`/sessions/${sessionId}/drafts/${draftId}/bulk-accept-reasons/`, {
      reason: reason || 'Bulk accepted all reasoning factors'
    });
    return response.data;
  }

  /**
   * Bulk reject all reasoning factors for a draft
   */
  async bulkRejectReasons(sessionId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    const response = await api.post(`/sessions/${sessionId}/drafts/${draftId}/bulk-reject-reasons/`, {
      reason: reason || 'Bulk rejected all reasoning factors'
    });
    return response.data;
  }

  /**
   * Bulk rate selected reasoning factors
   */
  async bulkRateReasons(sessionId: string, draftId: number, rateRequest: BulkRateRequest): Promise<BulkRateResponse> {
    const response = await api.post(`/sessions/${sessionId}/drafts/${draftId}/bulk-rate-reasons/`, rateRequest);
    return response.data;
  }

  /**
   * Quick rate a single reasoning factor (thumbs up/down)
   */
  async quickRateReason(sessionId: string, reasonId: number, rateRequest: QuickRateRequest): Promise<QuickRateResponse> {
    const response = await api.post(`/sessions/${sessionId}/reasons/${reasonId}/quick-rate/`, rateRequest);
    return response.data;
  }
}

export const reasoningService = new ReasoningService();