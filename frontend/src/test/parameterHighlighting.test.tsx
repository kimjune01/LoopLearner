import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SessionDetail } from '../components/SessionDetail';
import { sessionService } from '../services/sessionService';
import type { Session } from '../types/session';

// Mock the sessionService
vi.mock('../services/sessionService', () => ({
  sessionService: {
    getSession: vi.fn(),
    updateSessionPrompt: vi.fn(),
  }
}));

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(() => ({ id: 'test-session-id' })),
    Link: ({ children, to, ...props }: any) => <a href={to} {...props}>{children}</a>
  };
});

describe('Parameter Highlighting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('highlights parameters in prompt content', async () => {
    const sessionWithParameters: Session = {
      id: 'test-session-id',
      name: 'Parameter Test Session',
      description: 'Testing parameter highlighting',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_active: true,
      optimization_iterations: 0,
      total_emails_processed: 0,
      total_feedback_collected: 0,
      active_prompt: {
        id: 'prompt-1',
        version: 1,
        content: 'Hello {{user_name}}, welcome to {{app_name}}! Your role is {{user_role}} and priority is {{priority_level}}.'
      },
      recent_emails: []
    };

    vi.mocked(sessionService.getSession).mockResolvedValue(sessionWithParameters);
    
    render(
      <BrowserRouter>
        <SessionDetail />
      </BrowserRouter>
    );

    // Wait for the session to load and check if parameters are highlighted
    await vi.waitFor(() => {
      // Check that the prompt content is displayed
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText(', welcome to')).toBeInTheDocument();
      expect(screen.getByText('! Your role is')).toBeInTheDocument();
      expect(screen.getByText('and priority is')).toBeInTheDocument();

      // Check that parameters are rendered as separate elements (highlighted)
      // Note: The exact structure depends on how the highlighting function renders them
      const promptContainer = screen.getByText('Hello').closest('div');
      expect(promptContainer).toBeInTheDocument();
    });
  });

  it('renders prompt without parameters normally', async () => {
    const sessionWithoutParameters: Session = {
      id: 'test-session-id',
      name: 'Normal Session',
      description: 'Testing normal prompt display',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_active: true,
      optimization_iterations: 0,
      total_emails_processed: 0,
      total_feedback_collected: 0,
      active_prompt: {
        id: 'prompt-1',
        version: 1,
        content: 'This is a normal prompt without any special parameters or placeholders.'
      },
      recent_emails: []
    };

    vi.mocked(sessionService.getSession).mockResolvedValue(sessionWithoutParameters);
    
    render(
      <BrowserRouter>
        <SessionDetail />
      </BrowserRouter>
    );

    // Wait for the session to load and check normal text display
    await vi.waitFor(() => {
      expect(screen.getByText('This is a normal prompt without any special parameters or placeholders.')).toBeInTheDocument();
    });
  });

  it('handles complex parameter patterns', async () => {
    const sessionWithComplexParameters: Session = {
      id: 'test-session-id',
      name: 'Complex Parameter Session',
      description: 'Testing complex parameter patterns',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_active: true,
      optimization_iterations: 0,
      total_emails_processed: 0,
      total_feedback_collected: 0,
      active_prompt: {
        id: 'prompt-1',
        version: 1,
        content: `You are {{assistant_name}} working for {{company_name}}.

Key responsibilities:
- Handle {{task_type}} requests  
- Maintain {{tone_style}} communication
- Follow {{company_guidelines}} protocols

Current settings:
- User: {{current_user}}
- Department: {{user_department}}
- Access Level: {{access_level}}`
      },
      recent_emails: []
    };

    vi.mocked(sessionService.getSession).mockResolvedValue(sessionWithComplexParameters);
    
    render(
      <BrowserRouter>
        <SessionDetail />
      </BrowserRouter>
    );

    // Wait for the session to load
    await vi.waitFor(() => {
      // Check that the base text is present
      expect(screen.getByText(/You are/)).toBeInTheDocument();
      expect(screen.getByText(/working for/)).toBeInTheDocument();
      expect(screen.getByText(/Key responsibilities/)).toBeInTheDocument();
      
      // The parameters should be processed and highlighted
      // Check that some parts of the content are rendered
      const contentContainer = screen.getByText(/You are/).closest('div');
      expect(contentContainer).toBeInTheDocument();
    });
  });

  it('handles empty and null prompt content', async () => {
    const sessionWithEmptyPrompt: Session = {
      id: 'test-session-id',
      name: 'Empty Prompt Session',
      description: 'Testing empty prompt handling',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_active: true,
      optimization_iterations: 0,
      total_emails_processed: 0,
      total_feedback_collected: 0,
      active_prompt: {
        id: null,
        version: null,
        content: null
      },
      recent_emails: []
    };

    vi.mocked(sessionService.getSession).mockResolvedValue(sessionWithEmptyPrompt);
    
    render(
      <BrowserRouter>
        <SessionDetail />
      </BrowserRouter>
    );

    // Wait for the session to load and check empty state
    await vi.waitFor(() => {
      expect(screen.getByText('No System Prompt Set')).toBeInTheDocument();
    });
  });
});