import { api } from './api';
import type { 
  PromptLab, 
  PromptLabListResponse, 
  PromptLabStats, 
  CreatePromptLabRequest, 
  UpdatePromptLabRequest, 
  DuplicatePromptLabRequest 
} from '../types/promptLab';

export const promptLabService = {
  // List all prompt labs with optional filtering and sorting
  async getAllPromptLabs(params?: {
    search?: string;
    sort_by?: 'created_at' | 'updated_at' | 'name';
    order?: 'asc' | 'desc';
    status?: string;
  }): Promise<PromptLabListResponse> {
    const response = await api.get('/prompt-labs/', { params });
    return response.data;
  },

  // Simple method to get all prompt labs
  async getPromptLabs(): Promise<PromptLab[]> {
    const response = await api.get('/prompt-labs/');
    return response.data.prompt_labs || [];
  },

  // Create a new prompt lab
  async createPromptLab(data: CreatePromptLabRequest): Promise<PromptLab> {
    const response = await api.post('/prompt-labs/', data);
    return response.data;
  },

  // Get prompt lab details
  async getPromptLab(promptLabId: string): Promise<PromptLab & { 
    active_prompt: { id: string | null; version: number | null; content: string | null };
    recent_emails: Array<{ id: number; subject: string; created_at: string; scenario_type: string }>;
  }> {
    const response = await api.get(`/prompt-labs/${promptLabId}/`);
    return response.data;
  },

  // Update prompt lab
  async updatePromptLab(promptLabId: string, data: UpdatePromptLabRequest): Promise<PromptLab> {
    const response = await api.put(`/prompt-labs/${promptLabId}/`, data);
    return response.data;
  },

  // Delete prompt lab (soft delete)
  async deletePromptLab(promptLabId: string): Promise<{ message: string }> {
    const response = await api.delete(`/prompt-labs/${promptLabId}/`);
    return response.data;
  },

  // Export prompt lab data
  async exportPromptLab(promptLabId: string): Promise<any> {
    const response = await api.get(`/prompt-labs/${promptLabId}/export/`);
    return response.data;
  },

  // Duplicate prompt lab
  async duplicatePromptLab(promptLabId: string, data: DuplicatePromptLabRequest): Promise<PromptLab> {
    const response = await api.post(`/prompt-labs/${promptLabId}/duplicate/`, data);
    return response.data;
  },

  // Get prompt lab statistics
  async getPromptLabStats(promptLabId: string): Promise<PromptLabStats> {
    const response = await api.get(`/prompt-labs/${promptLabId}/stats/`);
    return response.data;
  },

  // PromptLab-scoped email generation
  async generateSyntheticEmail(promptLabId: string, data: { scenario_type?: string }): Promise<any> {
    const response = await api.post(`/prompt-labs/${promptLabId}/generate-synthetic-email/`, data);
    return response.data;
  },

  // PromptLab-scoped draft generation
  async generateDrafts(promptLabId: string, emailId: number, data: { num_drafts?: number }): Promise<any> {
    const response = await api.post(`/prompt-labs/${promptLabId}/emails/${emailId}/generate-drafts/`, data);
    return response.data;
  },

  // Update prompt lab prompt
  async updatePromptLabPrompt(promptLabId: string, prompt: string): Promise<PromptLab> {
    const response = await api.put(`/prompt-labs/${promptLabId}/`, { initial_prompt: prompt });
    return response.data;
  }
};