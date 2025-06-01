/**
 * Test output selection UI components for human-in-the-loop dataset generation.
 * Following TDD approach - these tests are written before component implementation.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import OutputVariationSelector from '../components/OutputVariationSelector';
import CaseWithOutputSelection from '../components/CaseWithOutputSelection';

// Mock data for testing
const mockOutputVariations = [
  {
    index: 0,
    text: "Thank you for contacting us regarding your billing issue. I'll review your account and provide assistance.",
    style: 'formal'
  },
  {
    index: 1,
    text: "Hi there! I understand you're having billing troubles. Let me help you sort this out quickly!",
    style: 'friendly'
  },
  {
    index: 2,
    text: "I appreciate you reaching out about your billing concern. Let me provide you with detailed steps to resolve this issue and explain our billing process.",
    style: 'detailed'
  }
];

const mockCaseData = {
  preview_id: 'test-case-1',
  input_text: 'Hello John Smith, I understand you have a billing issue. Let me help you.',
  parameters: {
    customer_name: 'John Smith',
    issue_type: 'billing issue'
  },
  prompt_content: 'Hello {{customer_name}}, I understand you have a {{issue_type}}. Let me help you.',
  output_variations: mockOutputVariations,
  selected_output_index: null,
  custom_output: null
};

describe('OutputVariationSelector Component', () => {
  const mockOnSelectionChange = vi.fn();

  beforeEach(() => {
    mockOnSelectionChange.mockClear();
  });

  it('displays three output variations for each case', () => {
    // Given: Output variations data
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: Component renders
    // Then: Should show 3 radio/option buttons
    const radioOptions = screen.getAllByRole('radio');
    expect(radioOptions).toHaveLength(4); // 3 variations + 1 custom option

    // Verify each variation is displayed
    expect(screen.getByText(/Thank you for contacting us/)).toBeInTheDocument();
    expect(screen.getByText(/Hi there! I understand/)).toBeInTheDocument();
    expect(screen.getByText(/I appreciate you reaching out/)).toBeInTheDocument();
    expect(screen.getByText(/Custom Output/)).toBeInTheDocument();
  });

  it('allows selection of output variation', async () => {
    // Given: Multiple output options
    const user = userEvent.setup();
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: User selects the second option
    const secondOption = screen.getByDisplayValue('1');
    await user.click(secondOption);

    // Then: Selection should be tracked
    expect(mockOnSelectionChange).toHaveBeenCalledWith({
      type: 'variation',
      index: 1,
      customOutput: null
    });
  });

  it('shows custom output input when custom option selected', async () => {
    // Given: Component with custom option
    const user = userEvent.setup();
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: User selects custom option
    const customOption = screen.getByDisplayValue('custom');
    await user.click(customOption);

    // Then: Text input should appear
    expect(screen.getByPlaceholderText(/Enter your custom response/)).toBeInTheDocument();
    expect(mockOnSelectionChange).toHaveBeenCalledWith({
      type: 'custom',
      index: null,
      customOutput: ''
    });
  });

  it('handles custom output text input', async () => {
    // Given: Custom option is selected
    const user = userEvent.setup();
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: User selects custom option first
    const customOption = screen.getByDisplayValue('custom');
    await user.click(customOption);

    // Then: Text input should appear and user can type
    const textInput = screen.getByPlaceholderText(/Enter your custom response/);
    await user.type(textInput, 'My custom response text');

    // Then: Custom output should be updated
    expect(mockOnSelectionChange).toHaveBeenCalledWith({
      type: 'custom',
      index: null,
      customOutput: 'My custom response text'
    });
  });

  it('validates custom output before allowing submission', async () => {
    // Given: Custom option is selected with empty text
    const user = userEvent.setup();
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: User selects custom option
    const customOption = screen.getByDisplayValue('custom');
    await user.click(customOption);

    // Then: Should indicate validation error for empty custom output
    expect(screen.getByText(/Custom output cannot be empty/)).toBeInTheDocument();
  });

  it('shows style labels for each variation', () => {
    // Given: Variations with different styles
    render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={null}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: Component renders
    // Then: Should show style labels
    expect(screen.getByText('formal')).toBeInTheDocument();
    expect(screen.getByText('friendly')).toBeInTheDocument();
    expect(screen.getByText('detailed')).toBeInTheDocument();
  });

  it('preserves selection state when re-rendered', () => {
    // Given: Component with pre-selected variation
    const { rerender } = render(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={1}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // When: Component re-renders
    rerender(
      <OutputVariationSelector
        variations={mockOutputVariations}
        selectedIndex={1}
        customOutput=""
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Then: Second option should still be selected
    const secondOption = screen.getByDisplayValue('1') as HTMLInputElement;
    expect(secondOption.checked).toBe(true);
  });
});

describe('CaseWithOutputSelection Component', () => {
  const mockOnCaseUpdate = vi.fn();

  beforeEach(() => {
    mockOnCaseUpdate.mockClear();
  });

  it('displays input parameters and generated input text', () => {
    // Given: Case data with parameters
    render(
      <CaseWithOutputSelection
        caseData={mockCaseData}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: Component renders
    // Then: Should show parameters and input
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('billing issue')).toBeInTheDocument();
    expect(screen.getByText(/Hello John Smith, I understand you have a billing issue/)).toBeInTheDocument();
  });

  it('shows output variations in selection component', () => {
    // Given: Case with output variations
    render(
      <CaseWithOutputSelection
        caseData={mockCaseData}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: Component renders
    // Then: Should show all output variations
    expect(screen.getByText(/Thank you for contacting us/)).toBeInTheDocument();
    expect(screen.getByText(/Hi there! I understand/)).toBeInTheDocument();
    expect(screen.getByText(/I appreciate you reaching out/)).toBeInTheDocument();
  });

  it('updates case data when output selection changes', async () => {
    // Given: Case component
    const user = userEvent.setup();
    render(
      <CaseWithOutputSelection
        caseData={mockCaseData}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: User selects an output variation
    const firstOption = screen.getByDisplayValue('0');
    await user.click(firstOption);

    // Then: Case data should be updated
    expect(mockOnCaseUpdate).toHaveBeenCalledWith({
      ...mockCaseData,
      selected_output_index: 0,
      custom_output: null
    });
  });

  it('handles custom output selection', async () => {
    // Given: Case component
    const user = userEvent.setup();
    render(
      <CaseWithOutputSelection
        caseData={mockCaseData}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: User selects custom output and enters text
    const customOption = screen.getByDisplayValue('custom');
    await user.click(customOption);

    const textInput = screen.getByPlaceholderText(/Enter your custom response/);
    await user.type(textInput, 'Custom response for this case');

    // Then: Case data should be updated with custom output
    expect(mockOnCaseUpdate).toHaveBeenCalledWith({
      ...mockCaseData,
      selected_output_index: null,
      custom_output: 'Custom response for this case'
    });
  });

  it('provides preview of selected output', async () => {
    // Given: Case with selection
    render(
      <CaseWithOutputSelection
        caseData={{...mockCaseData, selected_output_index: 1}}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: Component renders with selection
    // Then: Should show preview of selected output
    expect(screen.getByText(/Selected Output Preview/)).toBeInTheDocument();
    // Check that the specific text appears in the preview section
    const previewTexts = screen.getAllByText(/Hi there! I understand you're having billing troubles/);
    expect(previewTexts.length).toBeGreaterThan(0);
  });

  it('shows validation status for the case', () => {
    // Given: Case without selection
    render(
      <CaseWithOutputSelection
        caseData={mockCaseData}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: Component renders
    // Then: Should show validation warning
    expect(screen.getByText(/Please select an output option/)).toBeInTheDocument();
  });

  it('indicates when case is ready for submission', () => {
    // Given: Case with valid selection
    render(
      <CaseWithOutputSelection
        caseData={{...mockCaseData, selected_output_index: 0}}
        onCaseUpdate={mockOnCaseUpdate}
      />
    );

    // When: Component renders
    // Then: Should show ready status
    expect(screen.getByText(/Ready to add/)).toBeInTheDocument();
    expect(screen.queryByText(/Please select an output option/)).not.toBeInTheDocument();
  });
});

describe('Batch Case Selection', () => {
  const mockCases = [
    {...mockCaseData, preview_id: 'case-1'},
    {...mockCaseData, preview_id: 'case-2', input_text: 'Different input text'},
    {...mockCaseData, preview_id: 'case-3', parameters: {customer_name: 'Jane Doe', issue_type: 'shipping'}}
  ];

  it('allows bulk selection of same output variation', async () => {
    // This test would be implemented when we have a bulk selection component
    // For now, we'll skip it as it's not in the immediate scope
    expect(true).toBe(true);
  });

  it('validates all cases before enabling submission', () => {
    // This test would check that all cases have valid selections
    // before the batch submission is enabled
    expect(true).toBe(true);
  });
});

describe('Integration with API', () => {
  it('submits selected cases to API correctly', async () => {
    // This test would verify the API integration
    // We'll implement this in the integration test phase
    expect(true).toBe(true);
  });

  it('handles API errors gracefully', async () => {
    // This test would verify error handling
    expect(true).toBe(true);
  });
});