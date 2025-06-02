/**
 * Tests for diff generation logic
 */
import { describe, it, expect } from 'vitest';

// Simulate the diff generation logic from EvaluationDatasetDetail.tsx
function generateDiff(oldText: string, newText: string) {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  // Simple LCS-based diff algorithm
  const lcs = (arr1: string[], arr2: string[]): number[][] => {
    const m = arr1.length;
    const n = arr2.length;
    const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
    
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (arr1[i - 1] === arr2[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1] + 1;
        } else {
          dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        }
      }
    }
    
    return dp;
  };
  
  const dp = lcs(oldLines, newLines);
  let i = oldLines.length;
  let j = newLines.length;
  
  const result: Array<{ type: 'unchanged' | 'added' | 'removed'; content: string }> = [];
  
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      result.unshift({ type: 'unchanged', content: oldLines[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({ type: 'added', content: newLines[j - 1] });
      j--;
    } else if (i > 0) {
      result.unshift({ type: 'removed', content: oldLines[i - 1] });
      i--;
    }
  }
  
  return result;
}

describe('Diff Generation', () => {
  it('should identify unchanged lines', () => {
    const oldText = 'Line 1\nLine 2\nLine 3';
    const newText = 'Line 1\nLine 2\nLine 3';
    
    const diff = generateDiff(oldText, newText);
    
    expect(diff).toHaveLength(3);
    expect(diff.every(line => line.type === 'unchanged')).toBe(true);
  });
  
  it('should identify added lines', () => {
    const oldText = 'Line 1\nLine 3';
    const newText = 'Line 1\nLine 2\nLine 3';
    
    const diff = generateDiff(oldText, newText);
    
    expect(diff).toHaveLength(3);
    expect(diff[0]).toEqual({ type: 'unchanged', content: 'Line 1' });
    expect(diff[1]).toEqual({ type: 'added', content: 'Line 2' });
    expect(diff[2]).toEqual({ type: 'unchanged', content: 'Line 3' });
  });
  
  it('should identify removed lines', () => {
    const oldText = 'Line 1\nLine 2\nLine 3';
    const newText = 'Line 1\nLine 3';
    
    const diff = generateDiff(oldText, newText);
    
    expect(diff).toHaveLength(3);
    expect(diff[0]).toEqual({ type: 'unchanged', content: 'Line 1' });
    expect(diff[1]).toEqual({ type: 'removed', content: 'Line 2' });
    expect(diff[2]).toEqual({ type: 'unchanged', content: 'Line 3' });
  });
  
  it('should handle complete replacement', () => {
    const oldText = 'Old line 1\nOld line 2';
    const newText = 'New line 1\nNew line 2';
    
    const diff = generateDiff(oldText, newText);
    
    expect(diff).toHaveLength(4);
    expect(diff[0]).toEqual({ type: 'removed', content: 'Old line 1' });
    expect(diff[1]).toEqual({ type: 'removed', content: 'Old line 2' });
    expect(diff[2]).toEqual({ type: 'added', content: 'New line 1' });
    expect(diff[3]).toEqual({ type: 'added', content: 'New line 2' });
  });
  
  it('should handle empty strings', () => {
    const diff1 = generateDiff('', 'New content');
    expect(diff1.filter(d => d.type === 'added')).toHaveLength(1);
    expect(diff1).toEqual(expect.arrayContaining([
      { type: 'added', content: 'New content' }
    ]));
    
    const diff2 = generateDiff('Old content', '');
    expect(diff2.filter(d => d.type === 'removed')).toHaveLength(1);
    expect(diff2).toEqual(expect.arrayContaining([
      { type: 'removed', content: 'Old content' }
    ]));
    
    const diff3 = generateDiff('', '');
    const nonEmptyDiff3 = diff3.filter(d => d.content !== '');
    expect(nonEmptyDiff3).toHaveLength(0);
  });
  
  it('should handle multi-line changes', () => {
    const oldText = `Line 1
Line 2
Line 3
Line 4`;
    
    const newText = `Line 1
Modified Line 2
Line 3
Line 4
Line 5`;
    
    const diff = generateDiff(oldText, newText);
    
    const removed = diff.filter(d => d.type === 'removed');
    const added = diff.filter(d => d.type === 'added');
    const unchanged = diff.filter(d => d.type === 'unchanged');
    
    expect(removed).toHaveLength(1);
    expect(removed[0].content).toBe('Line 2');
    
    expect(added).toHaveLength(2);
    expect(added[0].content).toBe('Modified Line 2');
    expect(added[1].content).toBe('Line 5');
    
    expect(unchanged).toHaveLength(3);
  });
});

describe('Triple Brace Diff Scenarios', () => {
  it('should correctly show triple brace differences', () => {
    const oldText = `<email_content>
{{{EMAIL_CONTENT}}}
</email_content>`;
    
    const newText = `<email_content>
{{EMAIL_CONTENT}}
</email_content>`;
    
    const diff = generateDiff(oldText, newText);
    
    // Check that we have the expected content changes
    const unchanged = diff.filter(d => d.type === 'unchanged');
    const removed = diff.filter(d => d.type === 'removed');
    const added = diff.filter(d => d.type === 'added');
    
    expect(unchanged).toHaveLength(2); // Opening and closing tags
    expect(removed).toHaveLength(1);
    expect(added).toHaveLength(1);
    
    expect(removed[0].content).toBe('{{{EMAIL_CONTENT}}}');
    expect(added[0].content).toBe('{{EMAIL_CONTENT}}');
  });
  
  it('should handle multiple parameter changes', () => {
    const oldText = `Parameters:
{{{PARAM1}}}
{{{PARAM2}}}
{{{PARAM3}}}`;
    
    const newText = `Parameters:
{{PARAM1}}
{{PARAM2}}
{{PARAM3}}`;
    
    const diff = generateDiff(oldText, newText);
    
    const removed = diff.filter(d => d.type === 'removed');
    const added = diff.filter(d => d.type === 'added');
    
    expect(removed).toHaveLength(3);
    expect(added).toHaveLength(3);
    
    removed.forEach(line => {
      expect(line.content).toMatch(/^\{\{\{PARAM\d\}\}\}$/);
    });
    
    added.forEach(line => {
      expect(line.content).toMatch(/^\{\{PARAM\d\}\}$/);
    });
  });
  
  it('should preserve whitespace in diff', () => {
    const oldText = '  Indented line\n    More indented';
    const newText = 'Indented line\n  Less indented';
    
    const diff = generateDiff(oldText, newText);
    
    expect(diff[0]).toEqual({ type: 'removed', content: '  Indented line' });
    expect(diff[1]).toEqual({ type: 'removed', content: '    More indented' });
    expect(diff[2]).toEqual({ type: 'added', content: 'Indented line' });
    expect(diff[3]).toEqual({ type: 'added', content: '  Less indented' });
  });
});