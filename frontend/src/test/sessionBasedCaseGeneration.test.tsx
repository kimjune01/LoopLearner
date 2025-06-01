/**
 * Tests for session-based case generation functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { evaluationService } from '../services/evaluationService'
import type { EvaluationDataset } from '../types/evaluation'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Session-based Case Generation', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should generate cases using session prompt', async () => {
    const mockResponse = {
      previews: [
        {
          preview_id: 'test-id-1',
          input_text: 'Hello John Smith, thank you for contacting us about billing issue.',
          expected_output: 'I understand your concern about the billing issue...',
          parameters: {
            customer_name: 'John Smith',
            issue_type: 'billing issue',
            emotion: 'frustrated',
            resolution_request: 'refund'
          }
        }
      ],
      generation_method: 'session_prompt',
      session_name: 'Customer Service Session',
      prompt_content: 'Hello {{customer_name}}, thank you for contacting us about {{issue_type}}.',
      prompt_parameters: ['customer_name', 'issue_type', 'emotion', 'resolution_request']
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const result = await evaluationService.generateCases(1, '', 3, true, false, 3, false)

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/evaluations/datasets/1/generate-cases/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template: '',
          count: 3,
          use_session_prompt: true,
          persist_immediately: false
        })
      }
    )

    expect(result.generation_method).toBe('session_prompt')
    expect(result.session_name).toBe('Customer Service Session')
    expect(result.prompt_parameters).toEqual(['customer_name', 'issue_type', 'emotion', 'resolution_request'])
    expect(result.previews).toHaveLength(1)
    expect(result.previews[0].parameters.customer_name).toBe('John Smith')
  })

  it('should generate cases using template fallback', async () => {
    const mockResponse = {
      previews: [
        {
          preview_id: 'test-id-1',
          generated_input: 'Customer John Smith has a problem with billing',
          generated_output: 'I will help you with your billing problem.',
          parameters: {
            customer_name: 'John Smith',
            issue_type: 'billing'
          }
        }
      ],
      generation_method: 'template',
      template: 'Customer {{customer_name}} has a problem with {{issue_type}}'
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const result = await evaluationService.generateCases(
      1, 
      'Customer {{customer_name}} has a problem with {{issue_type}}', 
      3, 
      false
    )

    expect(result.generation_method).toBe('template')
    expect(result.previews).toHaveLength(1)
    expect(result.session_name).toBeUndefined()
    expect(result.prompt_content).toBeUndefined()
  })

  it('should handle session-associated datasets', () => {
    const sessionDataset: EvaluationDataset = {
      id: 1,
      name: 'Customer Service Cases',
      description: 'Generated from session prompt',
      parameters: ['customer_name', 'issue_type'],
      parameter_descriptions: {},
      created_at: '2025-05-31T00:00:00Z',
      updated_at: '2025-05-31T00:00:00Z',
      session_id: 'session-123',
      case_count: 0
    }

    // Verify type compatibility
    expect(sessionDataset.session_id).toBe('session-123')
    expect(sessionDataset.parameters).toEqual(['customer_name', 'issue_type'])
  })

  it('should handle global datasets without session', () => {
    const globalDataset: EvaluationDataset = {
      id: 2,
      name: 'Global Dataset',
      description: 'Not associated with any session',
      parameters: ['test_param'],
      parameter_descriptions: {},
      created_at: '2025-05-31T00:00:00Z',
      updated_at: '2025-05-31T00:00:00Z',
      case_count: 0
    }

    // Verify type compatibility
    expect(globalDataset.session_id).toBeUndefined()
    expect(globalDataset.parameters).toEqual(['test_param'])
  })

  it('should filter datasets by session parameters', async () => {
    const mockResponse = {
      datasets: [
        {
          id: 1,
          name: 'Matching Dataset',
          parameters: ['customer_name', 'issue_type'],
          session_id: 'session-123'
        },
        {
          id: 2,
          name: 'Global Compatible Dataset',
          parameters: ['customer_name', 'issue_type', 'priority']
        }
      ]
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const datasets = await evaluationService.getDatasets('session-123', true)

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/evaluations/datasets/?session_id=session-123&filter_by_params=true'
    )

    expect(datasets).toHaveLength(2)
    expect(datasets[0].name).toBe('Matching Dataset')
    expect(datasets[1].name).toBe('Global Compatible Dataset')
  })
})