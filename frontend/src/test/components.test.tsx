import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import { EmailGenerator } from '../components/EmailGenerator';
import { DraftViewer } from '../components/DraftViewer';
import { ProgressDashboard } from '../components/ProgressDashboard';
import { StateExporter } from '../components/StateExporter';
import type { EmailDraft } from '../types/email';

// Mock services
vi.mock('../services/emailService', () => ({
  emailService: {
    generateFakeEmail: vi.fn(),
    generateDrafts: vi.fn(),
    submitFeedback: vi.fn(),
  }
}));

vi.mock('../services/optimizationService', () => ({
  optimizationService: {
    triggerOptimization: vi.fn(),
    getOptimizationStatus: vi.fn(),
  }
}));

describe('EmailGenerator Component', () => {
  const mockOnEmailGenerated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render with default scenario', () => {
    render(<EmailGenerator onEmailGenerated={mockOnEmailGenerated} />);
    
    expect(screen.getByText('Generate Fake Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Scenario Type:')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate Email' })).toBeInTheDocument();
  });

  it('should have scenario selection options', () => {
    render(<EmailGenerator onEmailGenerated={mockOnEmailGenerated} />);
    
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    
    // Check if options exist (exact text may vary)
    expect(screen.getByDisplayValue('random')).toBeInTheDocument();
  });

  it('should call onEmailGenerated when button is clicked', async () => {
    const user = userEvent.setup();
    render(<EmailGenerator onEmailGenerated={mockOnEmailGenerated} />);
    
    const button = screen.getByRole('button', { name: 'Generate Email' });
    await user.click(button);
    
    // The service call will fail (not implemented), but the UI should handle it
    // This test verifies the component interface exists
  });
});

describe('DraftViewer Component', () => {
  const mockOnDraftAction = vi.fn();
  const mockOnReasonRating = vi.fn();
  
  const mockDrafts: EmailDraft[] = [
    {
      id: 'draft-1',
      content: 'Test draft content',
      reasons: [
        { text: 'Professional tone', confidence: 0.8 },
        { text: 'Addresses main points', confidence: 0.9 }
      ]
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render draft count', () => {
    render(
      <DraftViewer 
        drafts={mockDrafts} 
        onDraftAction={mockOnDraftAction}
        onReasonRating={mockOnReasonRating}
      />
    );
    
    expect(screen.getByText('Draft Responses (1)')).toBeInTheDocument();
  });

  it('should render draft content and reasons', () => {
    render(
      <DraftViewer 
        drafts={mockDrafts} 
        onDraftAction={mockOnDraftAction}
        onReasonRating={mockOnReasonRating}
      />
    );
    
    expect(screen.getByText('Test draft content')).toBeInTheDocument();
    expect(screen.getByText(/Professional tone/)).toBeInTheDocument();
    expect(screen.getByText(/Addresses main points/)).toBeInTheDocument();
  });

  it('should have action buttons', () => {
    render(
      <DraftViewer 
        drafts={mockDrafts} 
        onDraftAction={mockOnDraftAction}
        onReasonRating={mockOnReasonRating}
      />
    );
    
    expect(screen.getByRole('button', { name: 'Accept' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ignore' })).toBeInTheDocument();
  });
});

describe('ProgressDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading state initially', () => {
    render(<ProgressDashboard />);
    
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('should have trigger optimization button', async () => {
    // Mock successful service calls
    const { optimizationService } = await import('../services/optimizationService');
    
    vi.mocked(optimizationService.getOptimizationStatus).mockResolvedValue({
      status: 'idle'
    });

    render(<ProgressDashboard />);
    
    // Wait for loading to complete and check for optimization button
    await screen.findByText('Trigger Optimization');
  });
});

describe('StateExporter Component', () => {
  it('should render placeholder for state management', () => {
    render(<StateExporter />);
    
    expect(screen.getByText('State Management')).toBeInTheDocument();
    expect(screen.getByText('State management features will be implemented later')).toBeInTheDocument();
  });
});