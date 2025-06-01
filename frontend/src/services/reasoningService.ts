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
  async getReasoningFactors(promptLabId: string, draftId: number): Promise<DraftReasoningFactors> {
    const response = await api.get(`/prompt-labs/${promptLabId}/drafts/${draftId}/reasoning-factors/`);
    return response.data;
  }

  /**
   * Bulk accept all reasoning factors for a draft
   */
  async bulkAcceptReasons(promptLabId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    const response = await api.post(`/prompt-labs/${promptLabId}/drafts/${draftId}/bulk-accept-reasons/`, {
      reason: reason || 'Bulk accepted all reasoning factors'
    });
    return response.data;
  }

  /**
   * Bulk reject all reasoning factors for a draft
   */
  async bulkRejectReasons(promptLabId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    const response = await api.post(`/prompt-labs/${promptLabId}/drafts/${draftId}/bulk-reject-reasons/`, {
      reason: reason || 'Bulk rejected all reasoning factors'
    });
    return response.data;
  }

  /**
   * Bulk rate selected reasoning factors
   */
  async bulkRateReasons(promptLabId: string, draftId: number, rateRequest: BulkRateRequest): Promise<BulkRateResponse> {
    const response = await api.post(`/prompt-labs/${promptLabId}/drafts/${draftId}/bulk-rate-reasons/`, rateRequest);
    return response.data;
  }

  /**
   * Quick rate a single reasoning factor (thumbs up/down)
   */
  async quickRateReason(promptLabId: string, reasonId: number, rateRequest: QuickRateRequest): Promise<QuickRateResponse> {
    const response = await api.post(`/prompt-labs/${promptLabId}/reasons/${reasonId}/quick-rate/`, rateRequest);
    return response.data;
  }

  // Legacy methods for backwards compatibility
  
  /**
   * @deprecated Use getReasoningFactors instead. This method will be removed in a future version.
   */
  async getReasoningFactorsForSession(sessionId: string, draftId: number): Promise<DraftReasoningFactors> {
    return this.getReasoningFactors(sessionId, draftId);
  }

  /**
   * @deprecated Use bulkAcceptReasons instead. This method will be removed in a future version.
   */
  async bulkAcceptReasonsForSession(sessionId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    return this.bulkAcceptReasons(sessionId, draftId, reason);
  }

  /**
   * @deprecated Use bulkRejectReasons instead. This method will be removed in a future version.
   */
  async bulkRejectReasonsForSession(sessionId: string, draftId: number, reason?: string): Promise<BulkRateResponse> {
    return this.bulkRejectReasons(sessionId, draftId, reason);
  }

  /**
   * @deprecated Use bulkRateReasons instead. This method will be removed in a future version.
   */
  async bulkRateReasonsForSession(sessionId: string, draftId: number, rateRequest: BulkRateRequest): Promise<BulkRateResponse> {
    return this.bulkRateReasons(sessionId, draftId, rateRequest);
  }

  /**
   * @deprecated Use quickRateReason instead. This method will be removed in a future version.
   */
  async quickRateReasonForSession(sessionId: string, reasonId: number, rateRequest: QuickRateRequest): Promise<QuickRateResponse> {
    return this.quickRateReason(sessionId, reasonId, rateRequest);
  }
}

export const reasoningService = new ReasoningService();