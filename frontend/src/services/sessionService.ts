import { api } from './api';
import type { 
  Session, 
  SessionListResponse, 
  SessionStats, 
  CreateSessionRequest, 
  UpdateSessionRequest, 
  DuplicateSessionRequest 
} from '../types/session';

export const sessionService = {
  // List all sessions with optional filtering and sorting
  async getAllSessions(params?: {
    search?: string;
    sort_by?: 'created_at' | 'updated_at' | 'name';
    order?: 'asc' | 'desc';
    status?: string;
  }): Promise<SessionListResponse> {
    const response = await api.get('/api/sessions/', { params });
    return response.data;
  },

  // Create a new session
  async createSession(data: CreateSessionRequest): Promise<Session> {
    const response = await api.post('/api/sessions/', data);
    return response.data;
  },

  // Get session details
  async getSession(sessionId: string): Promise<Session & { 
    active_prompt: { id: string | null; version: number | null; content: string | null };
    recent_emails: Array<{ id: number; subject: string; created_at: string; scenario_type: string }>;
  }> {
    const response = await api.get(`/api/sessions/${sessionId}/`);
    return response.data;
  },

  // Update session
  async updateSession(sessionId: string, data: UpdateSessionRequest): Promise<Session> {
    const response = await api.put(`/api/sessions/${sessionId}/`, data);
    return response.data;
  },

  // Delete session (soft delete)
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await api.delete(`/api/sessions/${sessionId}/`);
    return response.data;
  },

  // Export session data
  async exportSession(sessionId: string): Promise<any> {
    const response = await api.get(`/api/sessions/${sessionId}/export/`);
    return response.data;
  },

  // Duplicate session
  async duplicateSession(sessionId: string, data: DuplicateSessionRequest): Promise<Session> {
    const response = await api.post(`/api/sessions/${sessionId}/duplicate/`, data);
    return response.data;
  },

  // Get session statistics
  async getSessionStats(sessionId: string): Promise<SessionStats> {
    const response = await api.get(`/api/sessions/${sessionId}/stats/`);
    return response.data;
  },

  // Session-scoped email generation
  async generateSyntheticEmail(sessionId: string, data: { scenario_type?: string }): Promise<any> {
    const response = await api.post(`/api/sessions/${sessionId}/generate-synthetic-email/`, data);
    return response.data;
  },

  // Session-scoped draft generation
  async generateDrafts(sessionId: string, emailId: number, data: { num_drafts?: number }): Promise<any> {
    const response = await api.post(`/api/sessions/${sessionId}/emails/${emailId}/generate-drafts/`, data);
    return response.data;
  },

  // Update session prompt
  async updateSessionPrompt(sessionId: string, prompt: string): Promise<Session> {
    const response = await api.put(`/api/sessions/${sessionId}/`, { initial_prompt: prompt });
    return response.data;
  }
};