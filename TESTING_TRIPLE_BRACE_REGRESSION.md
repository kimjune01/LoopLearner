# Triple Curly Brace Regression Testing

This document describes the comprehensive test suite created to prevent regression of the triple curly brace issue that was fixed in the evaluation system.

## Issue Background

The triple curly brace issue occurred when:
1. Evaluation cases were stored with parameter values wrapped in single curly braces (e.g., `<email_content>{value}</email_content>`)
2. Frontend template reconstruction would replace the value with `{{PARAM}}`, creating `<email_content>{{{PARAM}}}</email_content>`
3. This caused incorrect diff displays showing `{{{PARAM}}}` vs `{{PARAM}}`

## Root Cause

The issue was in the backend's `evaluation_case_generator.py` where parameter substitution was incorrectly using f-string formatting that led to content being wrapped in extra braces.

## Test Coverage

### Backend Tests

#### `tests/test_template_substitution.py`
- **TestTemplateSubstitution**: Core parameter substitution functionality
  - `test_parameter_substitution_no_triple_braces`: Ensures no triple braces are created
  - `test_parameter_substitution_with_special_characters`: Handles regex special chars
  - `test_parameter_substitution_with_newlines`: Multi-line content support
  - `test_xml_wrapped_content_no_single_braces`: XML tag content handling
  - `test_case_generation_no_triple_braces`: End-to-end case generation
  - `test_edge_case_parameter_value_with_braces`: Values containing braces
  - `test_parameter_names_case_sensitive`: Case sensitivity verification

- **TestPromptParameterExtraction**: Parameter extraction from prompts
  - `test_extract_parameters_double_braces`: Only double braces extracted
  - `test_extract_parameters_no_duplicates`: Duplicate parameter handling

- **TestEvaluationCaseStorage**: Case storage verification
  - `test_case_stores_substituted_content`: Correct content storage
  - `test_case_context_preserves_parameter_values`: Parameter preservation

- **TestRegressionPrevention**: Specific regression prevention
  - `test_no_f_string_formatting_issues`: String concatenation approach
  - `test_xml_content_regression`: The exact XML scenario that failed

#### `tests/test_triple_brace_integration.py`
- **TestTripleBraceIntegration**: End-to-end integration tests
  - `test_end_to_end_no_triple_braces`: Complete generation to reconstruction flow
  - `test_actual_problematic_case_structure`: Real-world problematic case structure
  - `test_xml_tag_content_no_extra_braces`: XML content verification
  - `test_complex_content_with_special_chars`: Complex content handling
  - `test_diff_generation_with_fixed_cases`: Diff generation verification

- **TestRegressionScenarios**: Specific regression scenarios
  - `test_single_curly_brace_wrapping_scenario`: The exact bug scenario
  - `test_parameter_extraction_prevents_triple_braces`: Parameter extraction correctness

### Frontend Tests

#### `src/test/templateReconstruction.test.tsx`
- **Template Reconstruction**: Frontend reconstruction logic
  - Tests that no triple braces are created during reconstruction
  - XML-wrapped content handling
  - Skip logic for existing template placeholders
  - Special character and multi-line value handling
  - Parameter processing order (longest first)
  - Case sensitivity

- **Triple Brace Regression Tests**: Specific regression scenarios
  - Single-brace wrapped content (the original issue)
  - Correct handling when content has no extra braces

- **Edge Cases**: Boundary condition testing
  - Empty parameters and values
  - Whitespace-only values

#### `src/test/diffGeneration.test.tsx`
- **Diff Generation**: Line-by-line diff algorithm
  - Unchanged, added, and removed line identification
  - Multi-line change handling
  - Empty string handling

- **Triple Brace Diff Scenarios**: Diff-specific tests
  - Triple brace differences display
  - Multiple parameter changes
  - Whitespace preservation

## Test Commands

### Backend Tests
```bash
cd backend
uv run pytest tests/test_template_substitution.py -v
uv run pytest tests/test_triple_brace_integration.py -v
```

### Frontend Tests
```bash
cd frontend
pnpm test:run templateReconstruction.test.tsx
pnpm test:run diffGeneration.test.tsx
```

### All Tests
```bash
# Backend
cd backend && uv run pytest tests/test_template_substitution.py tests/test_triple_brace_integration.py

# Frontend  
cd frontend && pnpm test:run templateReconstruction.test.tsx diffGeneration.test.tsx
```

## Key Test Scenarios

### 1. Parameter Substitution
```python
# Test that this doesn't create triple braces
template = "{{EMAIL_CONTENT}}"
parameters = {'EMAIL_CONTENT': 'Test content'}
result = substitute_parameters(template, parameters)
# Should be: "Test content"
# Should NOT be: "{Test content}"
```

### 2. Template Reconstruction
```typescript
// Test that reconstruction doesn't create triple braces
inputText = "<email_content>\nTest content\n</email_content>"
parameters = {EMAIL_CONTENT: 'Test content'}
result = reconstructTemplate(inputText, parameters)
// Should be: "<email_content>\n{{EMAIL_CONTENT}}\n</email_content>"
// Should NOT be: "<email_content>\n{{{EMAIL_CONTENT}}}\n</email_content>"
```

### 3. XML Content Handling
```python
# Test that XML tags don't wrap content in extra braces
template = "<email_content>\n{{EMAIL_CONTENT}}\n</email_content>"
parameters = {'EMAIL_CONTENT': 'Dear Team, Hello'}
result = substitute_parameters(template, parameters)
# Should contain: "<email_content>\nDear Team, Hello\n</email_content>"
# Should NOT contain: "<email_content>\n{Dear Team, Hello}\n</email_content>"
```

## Monitoring for Regressions

These tests should be run:
1. **Before any changes** to parameter substitution logic
2. **Before any changes** to template reconstruction logic
3. **As part of CI/CD pipeline** for every commit
4. **When adding new case generation features**

## Warning Signs of Regression

If you see any of these in tests or production:
- `{{{PARAMETER_NAME}}}` in generated content
- Cases with single braces around parameter values: `{value}`
- Diff displays showing triple vs double braces
- Template reconstruction creating malformed placeholders

Run the full test suite immediately to identify the regression source.