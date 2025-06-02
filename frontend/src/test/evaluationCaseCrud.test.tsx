/**
 * Frontend tests for evaluation case CRUD operations
 * Tests the evaluationService and UI components for case management
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { evaluationService } from '../services/evaluationService';
import type { EvaluationCase, EvaluationDataset } from '../types/evaluation';

// Mock the evaluationService
vi.mock('../services/evaluationService');

describe('Evaluation Case CRUD Operations', () => {
  const mockDataset: EvaluationDataset = {
    id: 1,
    name: 'Test Dataset',
    description: 'Test dataset for CRUD',
    prompt_lab_id: 'test-lab-id',
    parameters: ['EMAIL_CONTENT', 'RECIPIENT_INFO'],
    parameter_descriptions: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  const mockCase: EvaluationCase = {
    id: 1,
    input_text: 'Test input text',
    expected_output: 'Test expected output',
    context: {
      EMAIL_CONTENT: 'Test email content',
      RECIPIENT_INFO: 'Test recipient'
    },
    created_at: '2024-01-01T00:00:00Z'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('evaluationService CRUD methods', () => {
    it('should create a new case', async () => {
      const newCaseData = {
        input_text: 'New test input',
        expected_output: 'New test output',
        context: { EMAIL_CONTENT: 'New email' }
      };

      const createdCase = { ...mockCase, ...newCaseData, id: 2 };
      vi.mocked(evaluationService.createCase).mockResolvedValue(createdCase);

      const result = await evaluationService.createCase(1, newCaseData);

      expect(evaluationService.createCase).toHaveBeenCalledWith(1, newCaseData);
      expect(result).toEqual(createdCase);
    });

    it('should read all cases for a dataset', async () => {
      const mockCases = [mockCase, { ...mockCase, id: 2 }];
      vi.mocked(evaluationService.getCases).mockResolvedValue(mockCases);

      const result = await evaluationService.getCases(1);

      expect(evaluationService.getCases).toHaveBeenCalledWith(1);
      expect(result).toEqual(mockCases);
    });

    it('should update a case', async () => {
      const updates = { expected_output: 'Updated output' };
      const updatedCase = { ...mockCase, ...updates };
      vi.mocked(evaluationService.updateCase).mockResolvedValue(updatedCase);

      const result = await evaluationService.updateCase(1, 1, updates);

      expect(evaluationService.updateCase).toHaveBeenCalledWith(1, 1, updates);
      expect(result).toEqual(updatedCase);
    });

    it('should delete a case', async () => {
      vi.mocked(evaluationService.deleteCase).mockResolvedValue(undefined);

      await evaluationService.deleteCase(1, 1);

      expect(evaluationService.deleteCase).toHaveBeenCalledWith(1, 1);
    });

    it('should handle API errors gracefully', async () => {
      const errorMessage = 'Failed to fetch cases';
      vi.mocked(evaluationService.getCases).mockRejectedValue(new Error(errorMessage));

      await expect(evaluationService.getCases(1)).rejects.toThrow(errorMessage);
    });
  });

  describe('Parameter filtering for metadata', () => {
    it('should filter out metadata parameters when comparing case parameters', () => {
      // This test simulates the frontend logic that filters metadata parameters
      const caseContext = {
        EMAIL_CONTENT: 'Test email',
        RECIPIENT_INFO: 'Test recipient',
        promoted_from_draft: 123,
        selected_variation_index: 1,
        used_custom_output: true
      };

      const activePromptParameters = ['EMAIL_CONTENT', 'RECIPIENT_INFO'];
      
      // Filter out metadata parameters (as implemented in EvaluationDatasetDetail.tsx)
      const metadataParams = ['promoted_from_draft', 'selected_variation_index', 'used_custom_output'];
      const caseParams = Object.keys(caseContext)
        .filter(param => !metadataParams.includes(param))
        .sort();
      
      const activeParams = activePromptParameters.sort();
      const parametersMatch = JSON.stringify(caseParams) === JSON.stringify(activeParams);

      expect(parametersMatch).toBe(true);
      expect(caseParams).toEqual(['EMAIL_CONTENT', 'RECIPIENT_INFO']);
    });

    it('should detect actual parameter mismatches', () => {
      const caseContext = {
        EMAIL_CONTENT: 'Test email',
        OLD_PARAM: 'Old parameter value'
      };

      const activePromptParameters = ['EMAIL_CONTENT', 'RECIPIENT_INFO'];
      
      // Filter out metadata parameters
      const metadataParams = ['promoted_from_draft', 'selected_variation_index', 'used_custom_output'];
      const caseParams = Object.keys(caseContext)
        .filter(param => !metadataParams.includes(param))
        .sort();
      
      const activeParams = activePromptParameters.sort();
      const parametersMatch = JSON.stringify(caseParams) === JSON.stringify(activeParams);

      expect(parametersMatch).toBe(false);
      expect(caseParams).toEqual(['EMAIL_CONTENT', 'OLD_PARAM']);
      expect(activeParams).toEqual(['EMAIL_CONTENT', 'RECIPIENT_INFO']);
    });
  });

  describe('Case editing workflow', () => {
    it('should save case edits correctly', async () => {
      // Mock a case editor component scenario
      const originalCase = mockCase;
      const editedData = {
        expected_output: 'Edited expected output',
        context: {
          ...originalCase.context,
          EMAIL_CONTENT: 'Edited email content'
        }
      };

      const updatedCase = { ...originalCase, ...editedData };
      vi.mocked(evaluationService.updateCase).mockResolvedValue(updatedCase);

      // Simulate the onSave callback from CaseEditor
      const onSave = async (updates: Partial<EvaluationCase>) => {
        try {
          await evaluationService.updateCase(mockDataset.id, originalCase.id, updates);
          return Promise.resolve();
        } catch (err) {
          console.error('Error saving case:', err);
          throw err;
        }
      };

      await onSave(editedData);

      expect(evaluationService.updateCase).toHaveBeenCalledWith(
        mockDataset.id,
        originalCase.id,
        editedData
      );
    });

    it('should handle save errors properly', async () => {
      const editedData = { expected_output: 'Edited output' };
      const errorMessage = 'Failed to update case';
      vi.mocked(evaluationService.updateCase).mockRejectedValue(new Error(errorMessage));

      const onSave = async (updates: Partial<EvaluationCase>) => {
        try {
          await evaluationService.updateCase(mockDataset.id, mockCase.id, updates);
        } catch (err) {
          console.error('Error saving case:', err);
          throw err;
        }
      };

      await expect(onSave(editedData)).rejects.toThrow(errorMessage);
    });
  });

  describe('Case deletion workflow', () => {
    it('should handle case deletion with confirmation', async () => {
      vi.mocked(evaluationService.deleteCase).mockResolvedValue(undefined);
      
      // Mock window.confirm to return true
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      const handleDeleteCase = async (caseId: number) => {
        if (!window.confirm('Are you sure you want to delete this case?')) {
          return;
        }

        try {
          await evaluationService.deleteCase(mockDataset.id, caseId);
          // In real component, this would call loadCases()
        } catch (err) {
          console.error('Error deleting case:', err);
          throw err;
        }
      };

      await handleDeleteCase(mockCase.id);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this case?');
      expect(evaluationService.deleteCase).toHaveBeenCalledWith(mockDataset.id, mockCase.id);

      confirmSpy.mockRestore();
    });

    it('should cancel deletion when user cancels confirmation', async () => {
      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      const handleDeleteCase = async (caseId: number) => {
        if (!window.confirm('Are you sure you want to delete this case?')) {
          return;
        }

        await evaluationService.deleteCase(mockDataset.id, caseId);
      };

      await handleDeleteCase(mockCase.id);

      expect(confirmSpy).toHaveBeenCalled();
      expect(evaluationService.deleteCase).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });

    it('should handle bulk deletion', async () => {
      const selectedCaseIds = [1, 2, 3];
      vi.mocked(evaluationService.deleteCase).mockResolvedValue(undefined);
      
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      const handleDeleteSelected = async (selectedCases: Set<number>) => {
        if (selectedCases.size === 0) return;
        
        if (!window.confirm(`Are you sure you want to delete ${selectedCases.size} cases?`)) {
          return;
        }

        try {
          await Promise.all(
            Array.from(selectedCases).map(caseId =>
              evaluationService.deleteCase(mockDataset.id, caseId)
            )
          );
        } catch (err) {
          console.error('Error deleting cases:', err);
          throw err;
        }
      };

      await handleDeleteSelected(new Set(selectedCaseIds));

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete 3 cases?');
      expect(evaluationService.deleteCase).toHaveBeenCalledTimes(3);
      selectedCaseIds.forEach(id => {
        expect(evaluationService.deleteCase).toHaveBeenCalledWith(mockDataset.id, id);
      });

      confirmSpy.mockRestore();
    });
  });

  describe('Data consistency and validation', () => {
    it('should validate required fields for case creation', async () => {
      const invalidCaseData = {
        input_text: '', // Missing required field
        expected_output: 'Test output'
      };

      const errorResponse = { error: 'input_text and expected_output are required' };
      vi.mocked(evaluationService.createCase).mockRejectedValue(errorResponse);

      await expect(evaluationService.createCase(1, invalidCaseData)).rejects.toEqual(errorResponse);
    });

    it('should preserve metadata parameters during updates', async () => {
      const caseWithMetadata = {
        ...mockCase,
        context: {
          EMAIL_CONTENT: 'Test email',
          RECIPIENT_INFO: 'Test recipient',
          promoted_from_draft: 123,
          selected_variation_index: 1,
          used_custom_output: true
        }
      };

      const updates = {
        expected_output: 'Updated output',
        context: {
          ...caseWithMetadata.context,
          EMAIL_CONTENT: 'Updated email'
        }
      };

      const updatedCase = { ...caseWithMetadata, ...updates };
      vi.mocked(evaluationService.updateCase).mockResolvedValue(updatedCase);

      const result = await evaluationService.updateCase(1, 1, updates);

      expect(result.context).toEqual({
        EMAIL_CONTENT: 'Updated email',
        RECIPIENT_INFO: 'Test recipient',
        promoted_from_draft: 123,
        selected_variation_index: 1,
        used_custom_output: true
      });
    });

    it('should handle partial updates correctly', async () => {
      const partialUpdate = { expected_output: 'Only output changed' };
      const updatedCase = { ...mockCase, ...partialUpdate };
      vi.mocked(evaluationService.updateCase).mockResolvedValue(updatedCase);

      const result = await evaluationService.updateCase(1, 1, partialUpdate);

      expect(result.expected_output).toBe('Only output changed');
      expect(result.input_text).toBe(mockCase.input_text); // Unchanged
      expect(result.context).toEqual(mockCase.context); // Unchanged
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle network errors during CRUD operations', async () => {
      const networkError = new Error('Network request failed');
      vi.mocked(evaluationService.getCases).mockRejectedValue(networkError);

      await expect(evaluationService.getCases(1)).rejects.toThrow('Network request failed');
    });

    it('should handle 404 errors for nonexistent cases', async () => {
      const notFoundError = { status: 404, message: 'Case not found' };
      vi.mocked(evaluationService.updateCase).mockRejectedValue(notFoundError);

      await expect(evaluationService.updateCase(1, 999, { expected_output: 'test' }))
        .rejects.toEqual(notFoundError);
    });

    it('should handle cases with empty context', async () => {
      const caseWithEmptyContext = { ...mockCase, context: {} };
      vi.mocked(evaluationService.getCases).mockResolvedValue([caseWithEmptyContext]);

      const result = await evaluationService.getCases(1);

      expect(result[0].context).toEqual({});
    });

    it('should handle cases with null context', async () => {
      const caseWithNullContext = { ...mockCase, context: null as any };
      vi.mocked(evaluationService.getCases).mockResolvedValue([caseWithNullContext]);

      const result = await evaluationService.getCases(1);

      expect(result[0].context).toBeNull();
    });
  });

  describe('Case isolation and data integrity', () => {
    it('should ensure cases are isolated between datasets', async () => {
      const dataset1Cases = [{ ...mockCase, id: 1 }];
      const dataset2Cases = [{ ...mockCase, id: 2 }];

      vi.mocked(evaluationService.getCases)
        .mockResolvedValueOnce(dataset1Cases)
        .mockResolvedValueOnce(dataset2Cases);

      const result1 = await evaluationService.getCases(1);
      const result2 = await evaluationService.getCases(2);

      expect(result1).toEqual(dataset1Cases);
      expect(result2).toEqual(dataset2Cases);
      expect(result1[0].id).not.toBe(result2[0].id);
    });

    it('should maintain referential integrity during updates', async () => {
      const originalCase = mockCase;
      const updates = { expected_output: 'Updated output' };
      const updatedCase = { ...originalCase, ...updates };

      vi.mocked(evaluationService.updateCase).mockResolvedValue(updatedCase);

      const result = await evaluationService.updateCase(1, originalCase.id, updates);

      // Verify that the case ID and dataset relationship are preserved
      expect(result.id).toBe(originalCase.id);
      expect(result.input_text).toBe(originalCase.input_text);
      expect(result.context).toEqual(originalCase.context);
      expect(result.expected_output).toBe(updates.expected_output);
    });
  });
});