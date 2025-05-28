import { api } from './api';
import { EmailMessage, EmailDraft, UserFeedback } from '../types/email';

export class EmailService {
  /**
   * Generate a fake email for testing
   */
  async generateFakeEmail(scenarioType: string = 'random'): Promise<EmailMessage> {
    // TODO: Implement API call
    throw new Error('EmailService.generateFakeEmail not implemented');
  }

  /**
   * Generate draft responses for an email
   */
  async generateDrafts(emailId: string): Promise<EmailDraft[]> {
    // TODO: Implement API call
    throw new Error('EmailService.generateDrafts not implemented');
  }

  /**
   * Submit user feedback for an email/draft
   */
  async submitFeedback(feedback: UserFeedback): Promise<void> {
    // TODO: Implement API call
    throw new Error('EmailService.submitFeedback not implemented');
  }
}

export const emailService = new EmailService();