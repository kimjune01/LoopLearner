import type { EmailMessage, EmailDraft } from '../types/email';

export class EmailService {
  /**
   * Generate a fake email for testing
   */
  async generateFakeEmail(_scenarioType: string): Promise<EmailMessage> {
    // TODO: Implement API call
    throw new Error('EmailService.generateFakeEmail not implemented');
  }

  /**
   * Generate draft responses for an email
   */
  async generateDrafts(_emailId: string): Promise<EmailDraft[]> {
    // TODO: Implement API call
    throw new Error('EmailService.generateDrafts not implemented');
  }

  /**
   * Submit user feedback for an email/draft
   */
  async submitFeedback(_emailId: string, _draftId: string, _feedback: any): Promise<void> {
    // TODO: Implement API call
    throw new Error('EmailService.submitFeedback not implemented');
  }
}

export const emailService = new EmailService();