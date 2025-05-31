import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

const mockSession: Session = {
  id: 'test-session-id',
  name: 'Test Session',
  description: 'A test session for prompt editing',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  is_active: true,
  optimization_iterations: 0,
  total_emails_processed: 0,
  total_feedback_collected: 0,
  active_prompt: {
    id: 'prompt-1',
    version: 1,
    content: 'Test initial prompt'
  },
  recent_emails: []
};

const mockSessionWithoutPrompt: Session = {
  ...mockSession,
  id: 'test-session-no-prompt',
  name: 'Session Without Prompt',
  active_prompt: {
    id: null,
    version: null,
    content: null
  }
};

const renderSessionDetail = (session = mockSession) => {
  vi.mocked(sessionService.getSession).mockResolvedValue(session);
  
  return render(
    <BrowserRouter>
      <SessionDetail />
    </BrowserRouter>
  );
};

describe('SessionDetail Prompt Update', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Session with existing prompt', () => {
    it('displays existing prompt content', async () => {
      renderSessionDetail();

      await waitFor(() => {
        expect(screen.getByText('Test initial prompt')).toBeInTheDocument();
      });

      expect(screen.getByText('Active Prompt • Version 1')).toBeInTheDocument();
      expect(screen.getByText('Edit Prompt')).toBeInTheDocument();
    });

    it('opens prompt editor when Edit Prompt is clicked', async () => {
      renderSessionDetail();

      await waitFor(() => {
        expect(screen.getByText('Edit Prompt')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Edit Prompt'));

      await waitFor(() => {
        expect(screen.getByText('Edit System Prompt')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Test initial prompt')).toBeInTheDocument();
      });
    });

    it('successfully updates prompt and reflects changes', async () => {
      const updatedSession = {
        ...mockSession,
        active_prompt: {
          id: 'prompt-1',
          version: 1,
          content: 'Updated prompt content'
        }
      };

      vi.mocked(sessionService.updateSessionPrompt).mockResolvedValue(updatedSession);
      vi.mocked(sessionService.getSession)
        .mockResolvedValueOnce(mockSession)
        .mockResolvedValueOnce(updatedSession);

      renderSessionDetail();

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Edit Prompt')).toBeInTheDocument();
      });

      // Open editor
      fireEvent.click(screen.getByText('Edit Prompt'));

      await waitFor(() => {
        expect(screen.getByDisplayValue('Test initial prompt')).toBeInTheDocument();
      });

      // Update prompt content
      const textarea = screen.getByDisplayValue('Test initial prompt');
      fireEvent.change(textarea, { target: { value: 'Updated prompt content' } });

      // Save changes
      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(sessionService.updateSessionPrompt).toHaveBeenCalledWith(
          'test-session-id',
          'Updated prompt content'
        );
      });

      // Wait for reload and verify updated content
      await waitFor(() => {
        expect(screen.getByText('Updated prompt content')).toBeInTheDocument();
      });
    });

    it('handles prompt update errors gracefully', async () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = vi.fn();

      vi.mocked(sessionService.updateSessionPrompt).mockRejectedValue(
        new Error('Failed to update prompt')
      );

      renderSessionDetail();

      await waitFor(() => {
        expect(screen.getByText('Edit Prompt')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Edit Prompt'));

      await waitFor(() => {
        expect(screen.getByDisplayValue('Test initial prompt')).toBeInTheDocument();
      });

      const textarea = screen.getByDisplayValue('Test initial prompt');
      fireEvent.change(textarea, { target: { value: 'Updated content' } });
      fireEvent.click(screen.getByText('Save Changes'));

      await waitFor(() => {
        expect(sessionService.updateSessionPrompt).toHaveBeenCalled();
        // Should display error state or message
      });

      // Restore console.error
      console.error = originalError;
    });
  });

  describe('Session without prompt', () => {
    it('displays empty prompt state with creation options', async () => {
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        expect(screen.getByText('No System Prompt Set')).toBeInTheDocument();
      });

      expect(screen.getByText('Generate with Claude')).toBeInTheDocument();
      expect(screen.getByText('Write Manually')).toBeInTheDocument();
      expect(screen.getByText('Use your session description "A test session for prompt editing" as inspiration.')).toBeInTheDocument();
    });

    it('opens prompt editor when Write Manually is clicked', async () => {
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        expect(screen.getByText('Write Manually')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Write Manually'));

      await waitFor(() => {
        expect(screen.getByText('Create System Prompt')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter your system prompt here...')).toBeInTheDocument();
      });
    });

    it('shows Anthropic Console link for Generate with Claude', async () => {
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        const claudeLink = screen.getByText('Generate with Claude').closest('a');
        expect(claudeLink).toHaveAttribute('href', 'https://console.anthropic.com/dashboard');
        expect(claudeLink).toHaveAttribute('target', '_blank');
        expect(claudeLink).toHaveAttribute('rel', 'noopener noreferrer');
      });
    });

    it('creates new prompt successfully', async () => {
      // Get the mocked useParams and update it
      const { useParams } = await import('react-router-dom');
      vi.mocked(useParams).mockReturnValue({ id: 'test-session-no-prompt' });
      
      const sessionWithNewPrompt = {
        ...mockSessionWithoutPrompt,
        active_prompt: {
          id: 'new-prompt-1',
          version: 1,
          content: 'Newly created prompt'
        }
      };

      vi.mocked(sessionService.updateSessionPrompt).mockResolvedValue(sessionWithNewPrompt);
      vi.mocked(sessionService.getSession)
        .mockResolvedValueOnce(mockSessionWithoutPrompt)  // Initial load
        .mockResolvedValueOnce(sessionWithNewPrompt);     // After update
      
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        expect(screen.getByText('Write Manually')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Write Manually'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Enter your system prompt here...')).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText('Enter your system prompt here...');
      fireEvent.change(textarea, { target: { value: 'Newly created prompt' } });
      fireEvent.click(screen.getByText('Create Prompt'));

      await waitFor(() => {
        expect(sessionService.updateSessionPrompt).toHaveBeenCalledWith(
          'test-session-no-prompt',
          'Newly created prompt'
        );
      });

      await waitFor(() => {
        expect(screen.getByText('Newly created prompt')).toBeInTheDocument();
      });
    });
  });

  describe('PromptEditor functionality', () => {
    it('generates contextual suggestions based on session info', async () => {
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Write Manually'));
      });

      await waitFor(() => {
        expect(screen.getByText('Generate suggestion based on context')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Generate suggestion based on context'));

      await waitFor(() => {
        const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
        // Check that the textarea has content and includes session information
        const textareaValue = textarea.value;
        expect(textareaValue.length).toBeGreaterThan(0);
        expect(textareaValue).toContain('Session Without Prompt');
        expect(textareaValue).toContain('test session');
      });
    });

    it('shows character count and validation', async () => {
      renderSessionDetail();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit Prompt'));
      });

      await waitFor(() => {
        const characterCount = screen.getByText(/\d+ characters/);
        expect(characterCount).toBeInTheDocument();
      });
    });

    it('cancels editing without saving changes', async () => {
      renderSessionDetail();

      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit Prompt'));
      });

      await waitFor(() => {
        const textarea = screen.getByDisplayValue('Test initial prompt');
        fireEvent.change(textarea, { target: { value: 'Changed content' } });
      });

      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByText('Edit System Prompt')).not.toBeInTheDocument();
        expect(sessionService.updateSessionPrompt).not.toHaveBeenCalled();
      });
    });

    it('prevents saving empty prompts', async () => {
      renderSessionDetail(mockSessionWithoutPrompt);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Write Manually'));
      });

      await waitFor(() => {
        const saveButton = screen.getByText('Create Prompt');
        expect(saveButton).toBeDisabled();
      });
    });
  });

  describe('Session header and navigation', () => {
    it('displays session information in header', async () => {
      renderSessionDetail();

      await waitFor(() => {
        expect(screen.getByText('Test Session')).toBeInTheDocument();
        expect(screen.getByText('A test session for prompt editing')).toBeInTheDocument();
        expect(screen.getAllByText('Active').length).toBeGreaterThan(0);
      });
    });

    it('provides back navigation to sessions list', async () => {
      renderSessionDetail();

      await waitFor(() => {
        const backLink = screen.getByText('Back to Sessions').closest('a');
        expect(backLink).toHaveAttribute('href', '/');
      });
    });
  });
});