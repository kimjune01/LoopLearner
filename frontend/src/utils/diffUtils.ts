/**
 * Text diff utilities using LCS (Longest Common Subsequence) algorithm
 * Extracted from EvaluationDatasetDetail.tsx for reuse across components
 */

export interface DiffLine {
  type: 'unchanged' | 'added' | 'removed';
  content: string;
}

/**
 * Generate line-by-line diff using LCS algorithm
 * @param oldText Original text
 * @param newText Modified text
 * @returns Array of diff lines with type and content
 */
export function generateDiff(oldText: string, newText: string): DiffLine[] {
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
  
  const result: DiffLine[] = [];
  
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

/**
 * Get CSS classes for diff line styling
 * @param type The type of diff line
 * @returns Object with CSS classes for the line and prefix
 */
export function getDiffLineClasses(type: DiffLine['type']) {
  const lineClasses = {
    removed: 'bg-red-50 text-red-800 border-l-4 border-red-300',
    added: 'bg-green-50 text-green-800 border-l-4 border-green-300',
    unchanged: 'bg-white text-gray-700'
  };
  
  const prefixClasses = {
    removed: 'text-red-600',
    added: 'text-green-600', 
    unchanged: 'text-gray-400'
  };
  
  const prefixSymbols = {
    removed: '-',
    added: '+',
    unchanged: ' '
  };
  
  return {
    lineClass: lineClasses[type],
    prefixClass: prefixClasses[type],
    prefixSymbol: prefixSymbols[type]
  };
}

/**
 * Get diff statistics for summary display
 * @param diffLines Array of diff lines from generateDiff
 * @returns Object with counts of additions, deletions, and changes
 */
export function getDiffStats(diffLines: DiffLine[]) {
  const additions = diffLines.filter(line => line.type === 'added').length;
  const deletions = diffLines.filter(line => line.type === 'removed').length;
  const unchanged = diffLines.filter(line => line.type === 'unchanged').length;
  
  return {
    additions,
    deletions,
    unchanged,
    total: diffLines.length,
    hasChanges: additions > 0 || deletions > 0
  };
}