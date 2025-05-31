import { api } from './api';
import type { Session } from '../types/session';
import type { EvaluationDataset } from '../types/evaluation';

export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'txt' | 'md';
  includeMetadata?: boolean;
  includePrompts?: boolean;
  includeEmails?: boolean;
  includeFeedback?: boolean;
  includeReasonings?: boolean;
  includePreferences?: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface SessionExportData {
  session: {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    optimization_iterations: number;
    total_emails_processed: number;
    total_feedback_collected: number;
  };
  prompts?: Array<{
    version: number;
    content: string;
    is_active: boolean;
    performance_score: number | null;
    created_at: string;
  }>;
  preferences?: Array<{
    key: string;
    value: string;
    description: string;
    created_at: string;
    updated_at: string;
  }>;
  emails?: Array<{
    id: number;
    subject: string;
    body: string;
    sender: string;
    scenario_type: string;
    is_synthetic: boolean;
    created_at: string;
    drafts?: Array<{
      id: number;
      content: string;
      created_at: string;
      feedback?: Array<{
        action: string;
        reason: string;
        edited_content: string;
        created_at: string;
      }>;
    }>;
  }>;
}

export class ExportService {
  /**
   * Export complete session data
   */
  async exportSession(sessionId: string, options: ExportOptions = { format: 'json' }): Promise<void> {
    try {
      // Get session data from backend
      const response = await api.get(`/sessions/${sessionId}/export/`);
      const sessionData: SessionExportData = response.data;

      // Apply filters based on options
      const filteredData = this.filterSessionData(sessionData, options);

      // Export in requested format
      await this.exportData(filteredData, `session_${sessionData.session.name}`, options);
    } catch (error) {
      console.error('Error exporting session:', error);
      throw new Error('Failed to export session data');
    }
  }

  /**
   * Export evaluation dataset
   */
  async exportEvaluationDataset(dataset: EvaluationDataset, format: 'json' | 'csv' = 'json'): Promise<void> {
    try {
      const exportData = {
        dataset: {
          id: dataset.id,
          name: dataset.name,
          description: dataset.description,
          parameters: dataset.parameters,
          parameter_descriptions: dataset.parameter_descriptions,
          case_count: dataset.case_count,
          average_score: dataset.average_score,
          created_at: dataset.created_at,
          updated_at: dataset.updated_at
        },
        export_metadata: {
          exported_at: new Date().toISOString(),
          exported_by: 'LoopLearner Frontend',
          format_version: '1.0'
        }
      };

      await this.exportData(exportData, `evaluation_dataset_${dataset.name}`, { format });
    } catch (error) {
      console.error('Error exporting evaluation dataset:', error);
      throw new Error('Failed to export evaluation dataset');
    }
  }

  /**
   * Export system state for backup/migration
   */
  async exportSystemState(format: 'json' | 'txt' = 'json'): Promise<void> {
    try {
      const response = await api.get('/system/export/');
      const systemData = response.data;

      await this.exportData(systemData, 'system_state_backup', { format });
    } catch (error) {
      console.error('Error exporting system state:', error);
      throw new Error('Failed to export system state');
    }
  }

  /**
   * Export feedback data for analysis
   */
  async exportFeedbackAnalytics(sessionId: string, format: 'csv' | 'json' = 'csv'): Promise<void> {
    try {
      // Get detailed session data
      const response = await api.get(`/sessions/${sessionId}/export/`);
      const sessionData: SessionExportData = response.data;

      // Extract feedback data for analysis
      const feedbackData: Array<{
        email_id: number;
        email_subject: string;
        draft_id: number;
        feedback_action: string;
        feedback_reason: string;
        feedback_date: string;
        reasoning_factors?: string;
        confidence_score?: number;
      }> = [];

      sessionData.emails?.forEach(email => {
        email.drafts?.forEach(draft => {
          draft.feedback?.forEach(feedback => {
            feedbackData.push({
              email_id: email.id,
              email_subject: email.subject,
              draft_id: draft.id,
              feedback_action: feedback.action,
              feedback_reason: feedback.reason,
              feedback_date: feedback.created_at,
              // Add reasoning factors and confidence if available
            });
          });
        });
      });

      await this.exportData(feedbackData, `feedback_analytics_${sessionData.session.name}`, { format });
    } catch (error) {
      console.error('Error exporting feedback analytics:', error);
      throw new Error('Failed to export feedback analytics');
    }
  }

  /**
   * Filter session data based on export options
   */
  private filterSessionData(data: SessionExportData, options: ExportOptions): Partial<SessionExportData> {
    const filtered: Partial<SessionExportData> = {
      session: data.session
    };

    if (options.includePrompts !== false) {
      filtered.prompts = data.prompts;
    }

    if (options.includeEmails !== false) {
      filtered.emails = data.emails;
    }

    if (options.includePreferences !== false) {
      filtered.preferences = data.preferences;
    }

    // Apply date range filter if specified
    if (options.dateRange) {
      const startDate = new Date(options.dateRange.start);
      const endDate = new Date(options.dateRange.end);

      if (filtered.emails) {
        filtered.emails = filtered.emails.filter(email => {
          const emailDate = new Date(email.created_at);
          return emailDate >= startDate && emailDate <= endDate;
        });
      }

      if (filtered.prompts) {
        filtered.prompts = filtered.prompts.filter(prompt => {
          const promptDate = new Date(prompt.created_at);
          return promptDate >= startDate && promptDate <= endDate;
        });
      }
    }

    return filtered;
  }

  /**
   * Export data in specified format
   */
  private async exportData(data: any, baseFilename: string, options: ExportOptions): Promise<void> {
    const filename = this.sanitizeFilename(baseFilename);
    let content: string;
    let mimeType: string;
    let extension: string;

    switch (options.format) {
      case 'json':
        content = JSON.stringify(data, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        break;

      case 'csv':
        content = this.convertToCSV(data);
        mimeType = 'text/csv';
        extension = 'csv';
        break;

      case 'xlsx':
        // For now, export as CSV since XLSX requires additional libraries
        content = this.convertToCSV(data);
        mimeType = 'text/csv';
        extension = 'csv';
        break;

      case 'txt':
        content = this.convertToText(data);
        mimeType = 'text/plain';
        extension = 'txt';
        break;

      case 'md':
        content = this.convertToMarkdown(data);
        mimeType = 'text/markdown';
        extension = 'md';
        break;

      default:
        throw new Error(`Unsupported export format: ${options.format}`);
    }

    // Add metadata if requested
    if (options.includeMetadata !== false) {
      const metadata = {
        exported_at: new Date().toISOString(),
        exported_by: 'LoopLearner Frontend',
        format: options.format,
        options: options
      };

      if (options.format === 'json') {
        const dataWithMetadata = { ...data, export_metadata: metadata };
        content = JSON.stringify(dataWithMetadata, null, 2);
      }
    }

    // Create and download file
    this.downloadFile(content, `${filename}.${extension}`, mimeType);
  }

  /**
   * Convert data to CSV format
   */
  private convertToCSV(data: any): string {
    if (Array.isArray(data)) {
      return this.arrayToCSV(data);
    }

    // For complex objects, flatten and create CSV
    const flattened = this.flattenObject(data);
    return this.objectToCSV(flattened);
  }

  /**
   * Convert array of objects to CSV
   */
  private arrayToCSV(array: any[]): string {
    if (array.length === 0) return '';

    const headers = Object.keys(array[0]);
    const csvRows = [headers.join(',')];

    for (const row of array) {
      const values = headers.map(header => {
        const value = row[header];
        const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
        // Escape quotes and wrap in quotes if contains comma
        return stringValue.includes(',') || stringValue.includes('\"') 
          ? `\"${stringValue.replace(/\"/g, '\"\"')}\"` 
          : stringValue;
      });
      csvRows.push(values.join(','));
    }

    return csvRows.join('\\n');
  }

  /**
   * Convert object to CSV (key-value pairs)
   */
  private objectToCSV(obj: any): string {
    const rows = ['Key,Value'];
    
    Object.entries(obj).forEach(([key, value]) => {
      const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
      const escapedValue = stringValue.includes(',') || stringValue.includes('\"') 
        ? `\"${stringValue.replace(/\"/g, '\"\"')}\"` 
        : stringValue;
      rows.push(`${key},${escapedValue}`);
    });

    return rows.join('\\n');
  }

  /**
   * Convert data to plain text format
   */
  private convertToText(data: any): string {
    if (typeof data === 'string') return data;
    
    let text = '';
    
    if (data.session) {
      text += `Session: ${data.session.name}\\n`;
      text += `Description: ${data.session.description || 'No description'}\\n`;
      text += `Created: ${new Date(data.session.created_at).toLocaleString()}\\n`;
      text += `Updated: ${new Date(data.session.updated_at).toLocaleString()}\\n`;
      text += `Optimization Iterations: ${data.session.optimization_iterations}\\n`;
      text += `Total Emails: ${data.session.total_emails_processed}\\n`;
      text += `Total Feedback: ${data.session.total_feedback_collected}\\n\\n`;
    }

    if (data.prompts && data.prompts.length > 0) {
      text += '=== PROMPTS ===\\n';
      data.prompts.forEach((prompt: any) => {
        text += `Version ${prompt.version} (${prompt.is_active ? 'Active' : 'Inactive'})\\n`;
        text += `Performance: ${prompt.performance_score || 'Not scored'}\\n`;
        text += `Content: ${prompt.content}\\n\\n`;
      });
    }

    if (data.preferences && data.preferences.length > 0) {
      text += '=== PREFERENCES ===\\n';
      data.preferences.forEach((pref: any) => {
        text += `${pref.key}: ${pref.value}\\n`;
        text += `Description: ${pref.description}\\n\\n`;
      });
    }

    return text;
  }

  /**
   * Convert data to Markdown format
   */
  private convertToMarkdown(data: any): string {
    let md = '';

    if (data.session) {
      md += `# ${data.session.name}\\n\\n`;
      md += `**Description:** ${data.session.description || 'No description'}\\n`;
      md += `**Created:** ${new Date(data.session.created_at).toLocaleString()}\\n`;
      md += `**Updated:** ${new Date(data.session.updated_at).toLocaleString()}\\n`;
      md += `**Optimization Iterations:** ${data.session.optimization_iterations}\\n`;
      md += `**Total Emails:** ${data.session.total_emails_processed}\\n`;
      md += `**Total Feedback:** ${data.session.total_feedback_collected}\\n\\n`;
    }

    if (data.prompts && data.prompts.length > 0) {
      md += '## Prompts\\n\\n';
      data.prompts.forEach((prompt: any) => {
        md += `### Version ${prompt.version} ${prompt.is_active ? '(Active)' : ''}\\n\\n`;
        md += `**Performance Score:** ${prompt.performance_score || 'Not scored'}\\n`;
        md += `**Created:** ${new Date(prompt.created_at).toLocaleString()}\\n\\n`;
        md += '```\\n';
        md += prompt.content;
        md += '\\n```\\n\\n';
      });
    }

    if (data.preferences && data.preferences.length > 0) {
      md += '## User Preferences\\n\\n';
      data.preferences.forEach((pref: any) => {
        md += `- **${pref.key}:** ${pref.value}\\n`;
        if (pref.description) {
          md += `  - ${pref.description}\\n`;
        }
      });
      md += '\\n';
    }

    return md;
  }

  /**
   * Flatten nested object for CSV export
   */
  private flattenObject(obj: any, prefix = ''): Record<string, any> {
    const flattened: Record<string, any> = {};

    Object.keys(obj).forEach(key => {
      const value = obj[key];
      const newKey = prefix ? `${prefix}.${key}` : key;

      if (value && typeof value === 'object' && !Array.isArray(value)) {
        Object.assign(flattened, this.flattenObject(value, newKey));
      } else {
        flattened[newKey] = value;
      }
    });

    return flattened;
  }

  /**
   * Sanitize filename for download
   */
  private sanitizeFilename(filename: string): string {
    return filename
      .replace(/[^a-z0-9_-]/gi, '_')
      .toLowerCase()
      .replace(/__+/g, '_')
      .replace(/^_|_$/g, '');
  }

  /**
   * Download file to user's device
   */
  private downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  }
}

export const exportService = new ExportService();