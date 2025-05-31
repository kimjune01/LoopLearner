import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReasoningFactors from '../components/ReasoningFactors';
import EnhancedDraftViewer from '../components/EnhancedDraftViewer';
import { reasoningService } from '../services/reasoningService';
import type { DraftReasoningFactors } from '../types/reasoning';

// Mock the reasoning service
vi.mock('../services/reasoningService', () => ({
  reasoningService: {
    getReasoningFactors: vi.fn(),
    bulkAcceptReasons: vi.fn(),
    bulkRejectReasons: vi.fn(),
    bulkRateReasons: vi.fn(),
    quickRateReason: vi.fn(),
  }
}));

describe('ReasoningFactors Component', () => {
  const mockSessionId = 'test-session-id';
  const mockDraftId = 1;
  
  const mockReasoningData: DraftReasoningFactors = {
    draft_id: mockDraftId,
    reasoning_factors: [
      {
        id: 1,
        text: 'The response is professional and courteous',
        confidence: 0.85,
        rating_stats: {
          likes: 5,
          dislikes: 1,
          total_ratings: 6
        }
      },
      {
        id: 2,
        text: 'Addresses all key points from the email',
        confidence: 0.72,
        rating_stats: {
          likes: 3,
          dislikes: 2,
          total_ratings: 5
        }
      },
      {
        id: 3,
        text: 'The tone matches the context appropriately',
        confidence: 0.90,
        rating_stats: {
          likes: 0,
          dislikes: 0,
          total_ratings: 0
        }
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders reasoning factors correctly', async () => {
    vi.mocked(reasoningService.getReasoningFactors).mockResolvedValue(mockReasoningData);

    render(
      <ReasoningFactors
        sessionId={mockSessionId}
        draftId={mockDraftId}
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Reasoning Factors (3)')).toBeInTheDocument();
    });

    // Check that all reasoning factors are displayed
    expect(screen.getByText('The response is professional and courteous')).toBeInTheDocument();
    expect(screen.getByText('Addresses all key points from the email')).toBeInTheDocument();
    expect(screen.getByText('The tone matches the context appropriately')).toBeInTheDocument();

    // Check confidence badges
    expect(screen.getByText('85% confidence')).toBeInTheDocument();
    expect(screen.getByText('72% confidence')).toBeInTheDocument();
    expect(screen.getByText('90% confidence')).toBeInTheDocument();

    // Check rating stats
    expect(screen.getByText('👍 5 · 👎 1')).toBeInTheDocument();
    expect(screen.getByText('👍 3 · 👎 2')).toBeInTheDocument();
  });

  it('handles quick rating of individual factors', async () => {
    vi.mocked(reasoningService.getReasoningFactors).mockResolvedValue(mockReasoningData);
    vi.mocked(reasoningService.quickRateReason).mockResolvedValue({
      success: true,
      reason_id: 1,
      liked: true
    });

    const onRatingSubmitted = vi.fn();

    render(
      <ReasoningFactors
        sessionId={mockSessionId}
        draftId={mockDraftId}
        onRatingSubmitted={onRatingSubmitted}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('The response is professional and courteous')).toBeInTheDocument();
    });

    // Click the thumbs up button for the first factor
    const thumbsUpButtons = screen.getAllByTitle('Like this reasoning');
    fireEvent.click(thumbsUpButtons[0]);

    await waitFor(() => {
      expect(reasoningService.quickRateReason).toHaveBeenCalledWith(
        mockSessionId,
        1,
        { liked: true, create_feedback: true }
      );
      expect(onRatingSubmitted).toHaveBeenCalled();
    });
  });

  it('handles bulk selection and rating', async () => {
    vi.mocked(reasoningService.getReasoningFactors).mockResolvedValue(mockReasoningData);
    vi.mocked(reasoningService.bulkAcceptReasons).mockResolvedValue({
      feedback_id: 123,
      action: 'bulk_accept',
      reasons_rated: 3,
      draft_id: mockDraftId
    });

    render(
      <ReasoningFactors
        sessionId={mockSessionId}
        draftId={mockDraftId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Select all (0 of 3 selected)')).toBeInTheDocument();
    });

    // Select all checkboxes
    const selectAllCheckbox = screen.getByRole('checkbox', { name: /select all/i });
    fireEvent.click(selectAllCheckbox);

    expect(screen.getByText('Select all (3 of 3 selected)')).toBeInTheDocument();

    // Click bulk accept
    const acceptAllButton = screen.getByText('Accept All (3)');
    fireEvent.click(acceptAllButton);

    await waitFor(() => {
      expect(reasoningService.bulkAcceptReasons).toHaveBeenCalledWith(
        mockSessionId,
        mockDraftId,
        'Bulk accepted selected reasoning factors'
      );
    });
  });

  it('handles error states gracefully', async () => {
    vi.mocked(reasoningService.getReasoningFactors).mockRejectedValue(new Error('Network error'));

    render(
      <ReasoningFactors
        sessionId={mockSessionId}
        draftId={mockDraftId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load reasoning factors')).toBeInTheDocument();
    });

    // Check that retry button is available
    expect(screen.getByText('Try again')).toBeInTheDocument();
  });
});

describe('EnhancedDraftViewer Integration', () => {
  const mockSessionId = 'test-session-id';
  const mockDraft = {
    id: '1',
    content: 'Thank you for your email. I will look into this matter promptly.',
    createdAt: new Date().toISOString(),
    promptVersion: 1,
    reasons: [
      { text: 'Professional tone', confidence: 0.85 },
      { text: 'Clear response', confidence: 0.75 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows reasoning factors when button is clicked', async () => {
    vi.mocked(reasoningService.getReasoningFactors).mockResolvedValue({
      draft_id: 1,
      reasoning_factors: [
        {
          id: 1,
          text: 'Professional tone',
          confidence: 0.85,
          rating_stats: { likes: 0, dislikes: 0, total_ratings: 0 }
        }
      ]
    });

    render(
      <EnhancedDraftViewer
        sessionId={mockSessionId}
        drafts={[mockDraft]}
        onDraftAction={vi.fn()}
      />
    );

    // Initially reasoning factors should not be visible
    expect(screen.queryByText('Reasoning Factors (1)')).not.toBeInTheDocument();

    // Click show reasoning button
    const showReasoningButton = screen.getByText('Show Reasoning');
    fireEvent.click(showReasoningButton);

    // Wait for reasoning factors to load and display
    await waitFor(() => {
      expect(screen.getByText('Hide Reasoning')).toBeInTheDocument();
      expect(screen.getByText('Reasoning Factors (1)')).toBeInTheDocument();
    });
  });

  it('integrates draft actions with reasoning feedback', async () => {
    const onDraftAction = vi.fn();
    const onRatingSubmitted = vi.fn();

    render(
      <EnhancedDraftViewer
        sessionId={mockSessionId}
        drafts={[mockDraft]}
        onDraftAction={onDraftAction}
        onRatingSubmitted={onRatingSubmitted}
      />
    );

    // Add a reason
    const reasonInput = screen.getByPlaceholderText('Why did you choose this action?');
    fireEvent.change(reasonInput, { target: { value: 'Great response!' } });

    // Accept the draft
    const acceptButton = screen.getByText('Accept');
    fireEvent.click(acceptButton);

    expect(onDraftAction).toHaveBeenCalledWith(
      '1',
      'accept',
      'Great response!',
      undefined
    );

    // Check that feedback provided indicator appears
    expect(screen.getByText('Feedback Provided')).toBeInTheDocument();
  });

  it('handles edit mode correctly', async () => {
    const onDraftAction = vi.fn();

    render(
      <EnhancedDraftViewer
        sessionId={mockSessionId}
        drafts={[mockDraft]}
        onDraftAction={onDraftAction}
      />
    );

    // Click edit button
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);

    // Check that edit mode is active
    const textarea = screen.getByPlaceholderText('Edit the draft response...');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue(mockDraft.content);

    // Modify the content
    fireEvent.change(textarea, { 
      target: { value: 'Updated response content' } 
    });

    // Save the edit
    const saveButton = screen.getByText('Save Edit');
    fireEvent.click(saveButton);

    expect(onDraftAction).toHaveBeenCalledWith(
      '1',
      'edit',
      'Edited response',
      'Updated response content'
    );
  });
});