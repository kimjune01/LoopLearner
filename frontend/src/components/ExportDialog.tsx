/**
 * Export Dialog Component
 * Provides comprehensive export options for prompt labs, datasets, and system data
 */

import React, { useState } from 'react';
import { exportService } from '../services/exportService';
import type { ExportOptions } from '../services/exportService';
import type { PromptLab } from '../types/promptLab';
import type { EvaluationDataset } from '../types/evaluation';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  exportType: 'promptLab' | 'dataset' | 'system';
  promptLab?: PromptLab;
  dataset?: EvaluationDataset;
}

const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  exportType,
  promptLab,
  dataset
}) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'json',
    includeMetadata: true,
    includePrompts: true,
    includeEmails: true,
    includeFeedback: true,
    includeReasonings: true,
    includePreferences: true
  });
  const [dateRange, setDateRange] = useState({
    enabled: false,
    start: '',
    end: ''
  });
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleExport = async () => {
    try {
      setExporting(true);
      setError(null);

      const options: ExportOptions = {
        ...exportOptions,
        ...(dateRange.enabled && dateRange.start && dateRange.end ? {
          dateRange: {
            start: dateRange.start,
            end: dateRange.end
          }
        } : {})
      };

      switch (exportType) {
        case 'promptLab':
          if (!promptLab) throw new Error('Prompt lab data required');
          await exportService.exportPromptLab(promptLab.id, options);
          break;
        
        case 'dataset':
          if (!dataset) throw new Error('Dataset data required');
          await exportService.exportEvaluationDataset(dataset, options.format as 'json' | 'csv');
          break;
        
        case 'system':
          await exportService.exportSystemState(options.format as 'json' | 'txt');
          break;
        
        default:
          throw new Error('Invalid export type');
      }

      onClose();
    } catch (err) {
      console.error('Export error:', err);
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const getTitle = () => {
    switch (exportType) {
      case 'promptLab':
        return `Export Prompt Lab: ${promptLab?.name || 'Unknown'}`;
      case 'dataset':
        return `Export Dataset: ${dataset?.name || 'Unknown'}`;
      case 'system':
        return 'Export System State';
      default:
        return 'Export Data';
    }
  };

  const getDescription = () => {
    switch (exportType) {
      case 'promptLab':
        return 'Export complete prompt lab data including prompts, emails, feedback, and preferences.';
      case 'dataset':
        return 'Export evaluation dataset structure and test cases.';
      case 'system':
        return 'Export complete system state for backup or migration purposes.';
      default:
        return 'Export data from Loop Learner.';
    }
  };

  const getFormatOptions = () => {
    switch (exportType) {
      case 'promptLab':
        return ['json', 'csv', 'txt', 'md'];
      case 'dataset':
        return ['json', 'csv'];
      case 'system':
        return ['json', 'txt'];
      default:
        return ['json'];
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        
        <div className="relative w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
          {/* Header */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {getTitle()}
            </h3>
            <p className="mt-1 text-sm text-gray-600">{getDescription()}</p>
          </div>

          {/* Export Options */}
          <div className="space-y-6">
            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <div className="grid grid-cols-2 gap-2">
                {getFormatOptions().map((format) => (
                  <button
                    key={format}
                    onClick={() => setExportOptions({ ...exportOptions, format: format as any })}
                    className={`p-3 text-left border rounded-lg transition-colors ${
                      exportOptions.format === format
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="font-medium text-sm uppercase">{format}</div>
                    <div className="text-xs text-gray-500">
                      {format === 'json' && 'Structured data'}
                      {format === 'csv' && 'Spreadsheet format'}
                      {format === 'txt' && 'Plain text'}
                      {format === 'md' && 'Markdown format'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Content Options (Prompt Lab only) */}
            {exportType === 'promptLab' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Include in Export
                </label>
                <div className="space-y-2">
                  {[
                    { key: 'includePrompts', label: 'System Prompts', description: 'All prompt versions and performance data' },
                    { key: 'includeEmails', label: 'Emails & Drafts', description: 'Generated emails and AI responses' },
                    { key: 'includeFeedback', label: 'User Feedback', description: 'User ratings and comments' },
                    { key: 'includeReasonings', label: 'Reasoning Factors', description: 'AI reasoning explanations' },
                    { key: 'includePreferences', label: 'User Preferences', description: 'Learned user preferences' },
                    { key: 'includeMetadata', label: 'Export Metadata', description: 'Export timestamp and options' }
                  ].map(({ key, label, description }) => (
                    <label key={key} className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={(exportOptions as any)[key]}
                        onChange={(e) => setExportOptions({
                          ...exportOptions,
                          [key]: e.target.checked
                        })}
                        className="mt-1 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">{label}</div>
                        <div className="text-xs text-gray-500">{description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Date Range Filter (Prompt Lab only) */}
            {exportType === 'promptLab' && (
              <div>
                <label className="flex items-center space-x-2 cursor-pointer mb-3">
                  <input
                    type="checkbox"
                    checked={dateRange.enabled}
                    onChange={(e) => setDateRange({ ...dateRange, enabled: e.target.checked })}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Filter by Date Range</span>
                </label>
                
                {dateRange.enabled && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Start Date</label>
                      <input
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                        className="w-full text-sm border-gray-300 rounded-md focus:border-purple-500 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">End Date</label>
                      <input
                        type="date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                        className="w-full text-sm border-gray-300 rounded-md focus:border-purple-500 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="rounded-md bg-red-50 p-3 border border-red-200">
                <div className="flex items-center">
                  <svg className="w-4 h-4 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm text-red-800">{error}</span>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mt-8 flex justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={exporting}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              {exporting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Export Data
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;