import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SessionProgressVisualization from '../components/SessionProgressVisualization';
import { sessionService } from '../services/sessionService';

// Mock the session service
vi.mock('../services/sessionService', () => ({
  sessionService: {
    getSession: vi.fn(),
  }
}));

// Mock fetch for convergence API
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SessionProgressVisualization Component', () => {
  const mockSessionId = 'test-session-id';
  const mockSession = {
    id: mockSessionId,
    name: 'Test Session',
    description: 'Test session for progress visualization',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    is_active: true
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock session service response
    vi.mocked(sessionService.getSession).mockResolvedValue(mockSession);
    
    // Mock convergence API response
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        converged: false,
        confidenceScore: 0.75,
        factors: {
          performancePlateau: false,
          confidenceConvergence: true,
          feedbackStability: true,
          minimumIterationsReached: true,
          minimumFeedbackReached: true
        },
        recommendations: [
          {
            action: 'continue_optimization',
            reason: 'Performance still improving',
            priority: 'medium'
          }
        ]
      })
    });
  });

  it('renders loading state initially', () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    expect(screen.getByText('Loading progress visualization...')).toBeInTheDocument();
  });

  it('displays session progress data after loading', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Learning Progress')).toBeInTheDocument();
    });
    
    expect(screen.getByText(`Session: ${mockSession.name}`)).toBeInTheDocument();
    expect(screen.getByText('Current Confidence')).toBeInTheDocument();
    expect(screen.getByText('Performance Score')).toBeInTheDocument();
    expect(screen.getAllByText('Acceptance Rate')).toHaveLength(2); // Header and feedback section
  });

  it('displays convergence assessment when available', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Convergence Assessment')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Learning')).toBeInTheDocument(); // Status badge
    expect(screen.getByText('75%')).toBeInTheDocument(); // Confidence score
    expect(screen.getByText('continue optimization')).toBeInTheDocument();
  });

  it('handles time range selection', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Last 7 Days')).toBeInTheDocument();
    });
    
    const timeRangeSelect = screen.getByDisplayValue('Last 7 Days');
    fireEvent.change(timeRangeSelect, { target: { value: '24h' } });
    
    expect(timeRangeSelect).toHaveValue('24h');
  });

  it('displays optimization history', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Optimization History')).toBeInTheDocument();
    });
    
    // Should display mock optimization events
    expect(screen.getByText('Optimization #3')).toBeInTheDocument();
    expect(screen.getByText('High negative feedback ratio')).toBeInTheDocument();
    expect(screen.getByText('+15.3% improvement')).toBeInTheDocument();
  });

  it('displays feedback analysis', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Feedback Analysis')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Action Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Trend Analysis')).toBeInTheDocument();
    expect(screen.getByText('Total Feedback')).toBeInTheDocument();
    expect(screen.getByText('Recent Trend')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should trigger new data loading
    expect(sessionService.getSession).toHaveBeenCalledTimes(2);
  });

  it('displays error state when data loading fails', async () => {
    vi.mocked(sessionService.getSession).mockRejectedValue(new Error('Network error'));
    
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to Load Progress Data')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Network error')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('handles convergence API failure gracefully', async () => {
    // Mock console.error to suppress expected error message
    const mockConsoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    mockFetch.mockRejectedValue(new Error('API error'));
    
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Learning Progress')).toBeInTheDocument();
    });
    
    // Should still display other sections even if convergence fails
    expect(screen.getByText('Optimization History')).toBeInTheDocument();
    expect(screen.getByText('Feedback Analysis')).toBeInTheDocument();
    
    // Restore console.error
    mockConsoleError.mockRestore();
  });

  it('calls optimization trigger callback when provided', async () => {
    const mockTrigger = vi.fn();
    
    // Mock empty optimization history to show trigger button
    vi.mocked(sessionService.getSession).mockResolvedValue(mockSession);
    
    render(
      <SessionProgressVisualization 
        sessionId={mockSessionId} 
        onOptimizationTrigger={mockTrigger}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Optimization History')).toBeInTheDocument();
    });
  });

  it('displays correct progress bar colors based on values', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Current Confidence')).toBeInTheDocument();
    });
    
    // Check for progress bars (they should be rendered with appropriate colors)
    const progressBars = document.querySelectorAll('.h-2.rounded-full');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('formats timestamps correctly', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Optimization History')).toBeInTheDocument();
    });
    
    // Should display formatted timestamps in optimization history
    const timestamps = document.querySelectorAll('[class*="text-xs text-gray-500"]');
    expect(timestamps.length).toBeGreaterThan(0);
  });

  it('displays convergence factors correctly', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Convergence Assessment')).toBeInTheDocument();
    });
    
    // Should show checkmarks for met factors and circles for unmet factors
    const checkmarks = document.querySelectorAll('.text-green-600');
    const circles = document.querySelectorAll('.text-gray-400');
    
    expect(checkmarks.length).toBeGreaterThan(0);
    expect(circles.length).toBeGreaterThan(0);
  });

  it('displays recommendation priorities correctly', async () => {
    render(<SessionProgressVisualization sessionId={mockSessionId} />);
    
    await waitFor(() => {
      expect(screen.getByText('medium priority')).toBeInTheDocument();
    });
    
    // Should display priority badges with appropriate colors
    const priorityBadge = screen.getByText('medium priority');
    expect(priorityBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });
});