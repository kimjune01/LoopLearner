import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom';
import type { PromptLab } from '../types/promptLab';
import type { EvaluationDataset } from '../types/evaluation';
import { promptLabService } from '../services/promptLabService';
import { evaluationService } from '../services/evaluationService';
import { optimizationService } from '../services/optimizationService';
import { generateDatasetNameAndDescription } from '../utils/nameGenerator';
import { PromptEditor } from './PromptEditor';
import PromptLabProgressVisualization from './PromptLabProgressVisualization';

export const PromptLabDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [promptLab, setPromptLab] = useState<PromptLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isPromptExpanded, setIsPromptExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'prompt' | 'progress' | 'evaluations'>('prompt');
  const exportMenuRef = useRef<HTMLDivElement>(null);
  
  // Evaluation state
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [datasetsLoading, setDatasetsLoading] = useState(false);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterByParams, setFilterByParams] = useState(true);
  
  // Optimization state
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
  const [optimizationLoading, setOptimizationLoading] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<string | null>(null);
  const [showOptimizationModal, setShowOptimizationModal] = useState(false);
  
  const navigate = useNavigate();

  // Function to highlight parameters in prompt content
  const highlightParameters = (text: string) => {
    const parameterRegex = /(?<!\{)\{\{([^{}]+)\}\}(?!\})/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = parameterRegex.exec(text)) !== null) {
      // Add text before the parameter
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      // Add the highlighted parameter
      parts.push(
        <span 
          key={match.index}
          className="inline-flex items-center px-2 py-1 mx-1 bg-purple-100 text-purple-800 rounded-md border border-purple-200 font-semibold text-sm"
          title={`Parameter: ${match[1]}`}
        >
          <span className="text-purple-600 mr-1">{'{{'}</span>
          {match[1]}
          <span className="text-purple-600 ml-1">{'}}'}</span>
        </span>
      );
      
      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  const loadPromptLab = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const promptLabData = await promptLabService.getPromptLab(id);
      setPromptLab(promptLabData);
      setError(null);
    } catch (err) {
      setError('Failed to load prompt lab');
      console.error('Error loading prompt lab:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPromptLab();
    
    // Check for tab parameter in URL
    const tabParam = searchParams.get('tab');
    if (tabParam && ['prompt', 'progress', 'evaluations'].includes(tabParam)) {
      setActiveTab(tabParam as 'prompt' | 'progress' | 'evaluations');
    }
  }, [id, searchParams]);
  
  // Load evaluation datasets when evaluations tab is active
  useEffect(() => {
    if (activeTab === 'evaluations' && id) {
      loadDatasets();
    }
  }, [activeTab, id, filterByParams]);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };

    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportMenu]);

  const handleSavePrompt = async (prompt: string) => {
    if (!promptLab || !id) return;
    
    try {
      // Update prompt lab prompt via API
      await promptLabService.updatePromptLabPrompt(id, prompt);
      
      // Update local state immediately for responsive UI
      setPromptLab(prev => prev ? { 
        ...prev, 
        active_prompt: prev.active_prompt ? { 
          ...prev.active_prompt, 
          content: prompt 
        } : {
          id: null,
          version: null,
          content: prompt,
          parameters: []
        }
      } : null);
      setShowPromptEditor(false);
      
      // Reload prompt lab to get fresh data from server
      await loadPromptLab();
    } catch (err) {
      console.error('Error saving prompt:', err);
      setError('Failed to save prompt');
    }
  };

  const handleExportPrompt = (format: 'json' | 'txt' | 'md') => {
    if (!promptLab?.active_prompt?.content) return;

    const baseFilename = `${promptLab.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_prompt_v${promptLab.active_prompt.version}`;
    let content: string;
    let mimeType: string;
    let extension: string;

    switch (format) {
      case 'json':
        const exportData = {
          promptLab: {
            id: promptLab.id,
            name: promptLab.name,
            description: promptLab.description,
            created_at: promptLab.created_at,
            updated_at: promptLab.updated_at
          },
          prompt: {
            id: promptLab.active_prompt.id,
            content: promptLab.active_prompt.content,
            version: promptLab.active_prompt.version,
            parameters: promptLab.active_prompt.parameters || []
          },
          export_metadata: {
            exported_at: new Date().toISOString(),
            exported_by: 'LoopLearner Frontend',
            format_version: '1.0'
          }
        };
        content = JSON.stringify(exportData, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        break;

      case 'txt':
        content = `System Prompt for ${promptLab.name}
Version: ${promptLab.active_prompt.version}
Created: ${new Date(promptLab.created_at).toLocaleDateString()}
Updated: ${new Date(promptLab.updated_at).toLocaleDateString()}

${promptLab.description ? `Description: ${promptLab.description}\n\n` : ''}Parameters: ${(promptLab.active_prompt.parameters || []).map(p => `{{${p}}}`).join(', ')}

=== PROMPT CONTENT ===

${promptLab.active_prompt.content}

=== END ===

Exported from LoopLearner on ${new Date().toLocaleString()}`;
        mimeType = 'text/plain';
        extension = 'txt';
        break;

      case 'md':
        content = `# System Prompt: ${promptLab.name}

**Version:** ${promptLab.active_prompt.version}  
**Created:** ${new Date(promptLab.created_at).toLocaleDateString()}  
**Updated:** ${new Date(promptLab.updated_at).toLocaleDateString()}  

${promptLab.description ? `**Description:** ${promptLab.description}\n\n` : ''}## Parameters

${(promptLab.active_prompt.parameters || []).length > 0 
  ? (promptLab.active_prompt.parameters || []).map(p => `- \`{{${p}}}\``).join('\n')
  : 'No parameters detected'
}

## Prompt Content

\`\`\`
${promptLab.active_prompt.content}
\`\`\`

---
*Exported from LoopLearner on ${new Date().toLocaleString()}*`;
        mimeType = 'text/markdown';
        extension = 'md';
        break;
    }

    // Create and download the file
    const dataBlob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${baseFilename}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    setShowExportMenu(false);
  };
  
  const loadDatasets = async () => {
    if (!id) return;
    
    try {
      setDatasetsLoading(true);
      const data = await evaluationService.getDatasets(id, filterByParams);
      setDatasets(data);
      setDatasetsError(null);
    } catch (err) {
      setDatasetsError('Failed to load evaluation datasets');
      console.error('Error loading datasets:', err);
    } finally {
      setDatasetsLoading(false);
    }
  };
  
  const handleDeleteDataset = async (datasetId: number) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) {
      return;
    }

    try {
      await evaluationService.deleteDataset(datasetId);
      await loadDatasets();
    } catch (err) {
      setDatasetsError('Failed to delete dataset');
      console.error('Error deleting dataset:', err);
    }
  };

  // Optimization functions
  const handleDatasetSelection = (datasetId: number, selected: boolean) => {
    setSelectedDatasetIds(prev => 
      selected 
        ? [...prev, datasetId]
        : prev.filter(id => id !== datasetId)
    );
  };

  const handleSelectAllDatasets = () => {
    const allFilteredIds = filteredDatasets.map(d => d.id);
    setSelectedDatasetIds(
      selectedDatasetIds.length === allFilteredIds.length ? [] : allFilteredIds
    );
  };

  const handleTriggerOptimization = async () => {
    if (!id || selectedDatasetIds.length === 0) return;
    
    // Show confirmation modal
    setShowOptimizationModal(true);
  };

  const handleConfirmOptimization = async () => {
    if (!id || selectedDatasetIds.length === 0) return;

    setShowOptimizationModal(false);
    setOptimizationLoading(true);
    setOptimizationResult(null);

    try {
      const result = await optimizationService.triggerOptimizationWithDatasets({
        prompt_lab_id: id,
        dataset_ids: selectedDatasetIds,
        force: false
      });

      // Navigate to learning progress tab immediately
      setActiveTab('progress');
      navigate(`/prompt-labs/${id}?tab=progress`, { replace: true });
      
      // Clear selection after successful optimization
      setSelectedDatasetIds([]);
      
      // If we have a run_id, navigate directly to the optimization run detail page
      if (result.run_id) {
        // Small delay to let the progress tab load, then navigate to the specific run
        setTimeout(() => {
          navigate(`/prompt-labs/${id}/optimization/runs/${result.run_id}`);
        }, 1000);
      } else {
        // Show success message if no run_id
        setOptimizationResult(`Optimization started! ${result.message || 'View progress in the Learning Progress tab.'}`);
      }
      
      // Reload prompt lab to get latest data
      await loadPromptLab();
    } catch (err: any) {
      console.error('Optimization error:', err);
      const errorMessage = err.message || 'Optimization failed. Please try again.';
      setOptimizationResult(`Optimization failed: ${errorMessage}`);
    } finally {
      setOptimizationLoading(false);
    }
  };
  
  const filteredDatasets = datasets.filter(dataset =>
    dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dataset.description.toLowerCase().includes(searchTerm.toLowerCase())
  );


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Prompt Labs
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">Loading...</h1>
            </div>
          </div>
        </div>
        
        {/* Loading Content */}
        <div className="flex items-center justify-center min-h-[calc(100vh-120px)]">
          <div className="flex items-center gap-3 text-gray-600">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            <span className="text-lg">Loading prompt lab...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !promptLab) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Prompt Labs
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">Prompt Lab Not Found</h1>
            </div>
          </div>
        </div>
        
        {/* Error Content */}
        <div className="flex items-center justify-center min-h-[calc(100vh-120px)]">
          <div className="max-w-md mx-auto text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Prompt Lab Not Found</h2>
            <p className="text-gray-600 mb-6">{error || 'The requested prompt lab could not be found.'}</p>
            <Link 
              to="/" 
              className="btn-primary"
            >
              Back to Prompt Labs
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compact Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                to="/" 
                className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Prompt Labs
              </Link>
              <div className="w-px h-6 bg-white/30"></div>
              <h1 className="text-2xl font-bold text-white">
                {promptLab.name}
              </h1>
              {promptLab.description && (
                <>
                  <div className="hidden sm:block w-px h-6 bg-white/30"></div>
                  <p className="hidden sm:block text-white/90 text-sm max-w-md truncate">
                    {promptLab.description}
                  </p>
                </>
              )}
            </div>
            
            {/* Prompt Lab Status */}
            <div className="flex items-center gap-3 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${promptLab.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                <span className="text-white/80 text-sm font-medium">
                  {promptLab.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto bg-white shadow-sm border-b">
        <nav className="flex space-x-8 px-8">
          <button
            onClick={() => {
              setActiveTab('prompt');
              navigate(`/prompt-labs/${id}?tab=prompt`, { replace: true });
            }}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'prompt'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            System Prompt
          </button>
          <button
            onClick={() => {
              setActiveTab('progress');
              navigate(`/prompt-labs/${id}?tab=progress`, { replace: true });
            }}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'progress'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Learning Progress
          </button>
          <button
            onClick={() => {
              setActiveTab('evaluations');
              navigate(`/prompt-labs/${id}?tab=evaluations`, { replace: true });
            }}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'evaluations'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Evaluations
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="pt-0">
        <div className="max-w-7xl mx-auto bg-white shadow-lg min-h-[calc(100vh-120px)]">
          <div className="p-8">
            {/* Tab Content */}
            {activeTab === 'prompt' && (
              <>
                {/* Current System Prompt - Most Prominent Section */}
                <div className="mb-12">
              
              <div className="card-elevated p-8 mb-6">
                {promptLab.active_prompt?.content ? (
                  <div className="space-y-6">
                    {/* Prompt Content */}
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6 border-l-4 border-purple-500">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                            Active Prompt • Version {promptLab.active_prompt?.version || 1}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Last updated: {new Date(promptLab.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      
                      <div className="text-lg leading-relaxed text-gray-800 font-medium whitespace-pre-wrap">
                        <div className={`relative transition-all duration-300 ${
                          !isPromptExpanded ? 'max-h-screen overflow-hidden' : ''
                        }`}>
                          <div className={`${
                            !isPromptExpanded 
                              ? 'overflow-hidden' 
                              : ''
                          }`} style={{ 
                            maxHeight: !isPromptExpanded ? '100vh' : 'none',
                            maskImage: !isPromptExpanded ? 'linear-gradient(to bottom, black 85%, transparent 100%)' : 'none',
                            WebkitMaskImage: !isPromptExpanded ? 'linear-gradient(to bottom, black 85%, transparent 100%)' : 'none'
                          }}>
                            {highlightParameters(promptLab.active_prompt?.content || '')}
                          </div>
                          
                          {/* Show More/Less Button */}
                          {promptLab.active_prompt?.content && promptLab.active_prompt.content.split('\n').length > 20 && (
                            <div className="mt-4 text-center">
                              <button
                                onClick={() => setIsPromptExpanded(!isPromptExpanded)}
                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-lg transition-colors duration-200"
                              >
                                {isPromptExpanded ? (
                                  <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                    </svg>
                                    Show Less
                                  </>
                                ) : (
                                  <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                    Show More
                                  </>
                                )}
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Parameters Info */}
                      {promptLab.active_prompt?.parameters && promptLab.active_prompt.parameters.length > 0 && (
                        <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0">
                              <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                              </svg>
                            </div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-purple-900 mb-2">
                                Parameters ({promptLab.active_prompt.parameters.length})
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {promptLab.active_prompt.parameters.map((param, index) => (
                                  <span 
                                    key={index}
                                    className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-800 rounded-md border border-purple-200 font-mono text-sm"
                                  >
                                    <span className="text-purple-600 mr-1">{'{{'}</span>
                                    {param}
                                    <span className="text-purple-600 ml-1">{'}}'}</span>
                                  </span>
                                ))}
                              </div>
                              <p className="text-sm text-purple-700 mt-2">
                                These parameters can be dynamically filled with values when the prompt is used.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Prompt Actions */}
                    <div className="flex flex-wrap gap-3 justify-center">
                      <button 
                        onClick={() => setShowPromptEditor(true)}
                        className="btn-secondary flex items-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Edit Prompt
                      </button>
                      <div className="relative" ref={exportMenuRef}>
                        <button 
                          onClick={() => setShowExportMenu(!showExportMenu)}
                          className="btn-secondary flex items-center gap-2"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                          </svg>
                          Export Prompt
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        
                        {showExportMenu && (
                          <div className="absolute top-full mt-2 right-0 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50 min-w-48">
                            <button
                              onClick={() => handleExportPrompt('json')}
                              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3"
                            >
                              <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                                <span className="text-blue-700 font-mono text-xs font-bold">{'{}'}</span>
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">JSON</div>
                                <div className="text-sm text-gray-500">Structured data with metadata</div>
                              </div>
                            </button>
                            <button
                              onClick={() => handleExportPrompt('txt')}
                              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3"
                            >
                              <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">
                                <span className="text-gray-700 font-mono text-xs font-bold">TXT</span>
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">Plain Text</div>
                                <div className="text-sm text-gray-500">Simple text format</div>
                              </div>
                            </button>
                            <button
                              onClick={() => handleExportPrompt('md')}
                              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3"
                            >
                              <div className="w-8 h-8 bg-purple-100 rounded flex items-center justify-center">
                                <span className="text-purple-700 font-mono text-xs font-bold">MD</span>
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">Markdown</div>
                                <div className="text-sm text-gray-500">Formatted documentation</div>
                              </div>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No System Prompt Set</h3>
                    <p className="text-gray-600 mb-6">
                      This prompt lab needs a system prompt to begin learning.
                      {promptLab.description && (
                        <span className="block mt-2 text-sm italic">
                          Use your prompt lab description "{promptLab.description}" as inspiration.
                        </span>
                      )}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <a 
                        href="https://console.anthropic.com/dashboard"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Generate with Claude
                      </a>
                      <button 
                        onClick={() => setShowPromptEditor(true)}
                        className="btn-secondary flex items-center justify-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Write Manually
                      </button>
                    </div>
                    
                    {/* Helpful tip */}
                    <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-2xl mx-auto">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0">
                          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div className="text-left">
                          <p className="text-sm text-blue-800">
                            <strong>Tip:</strong> Ask Claude to create a system prompt for "{promptLab.name}"{promptLab.description && ` based on: "${promptLab.description}"`}. 
                            This will give you a great starting point for your prompt lab.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Secondary Info Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Prompt Lab Metadata */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Prompt Lab Info
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span className="font-medium">{new Date(promptLab.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Updated:</span>
                    <span className="font-medium">{new Date(promptLab.updated_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      promptLab.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {promptLab.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Learning Stats */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Progress
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Iterations:</span>
                    <span className="font-medium text-green-600">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Emails Processed:</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Feedback Collected:</span>
                    <span className="font-medium">0</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Quick Actions
                </h3>
                <div className="space-y-2">
                  <p className="text-sm text-gray-500 text-center py-4">
                    Quick actions will appear here as features are developed.
                  </p>
                </div>
              </div>
            </div>

              </>
            )}

            {/* Progress Tab Content */}
            {activeTab === 'progress' && id && (
              <PromptLabProgressVisualization 
                promptLabId={id}
                onOptimizationTrigger={() => {
                  // TODO: Integrate with optimization trigger
                  console.log('Optimization triggered from progress view');
                }}
              />
            )}

            {/* Evaluations Tab Content */}
            {activeTab === 'evaluations' && (
              <div className="space-y-8">
                <div className="text-center mb-8">
                  <h2 className="text-4xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                    Evaluation Datasets
                  </h2>
                  <p className="text-gray-600 text-lg">
                    Test your prompt performance against predefined evaluation datasets
                  </p>
                  {promptLab?.active_prompt?.parameters && promptLab.active_prompt.parameters.length > 0 && (
                    <div className="mt-6">
                      <p className="text-sm text-gray-700 mb-2">Prompt lab parameters:</p>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {promptLab.active_prompt.parameters.map((param: string) => (
                          <span
                            key={param}
                            className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800"
                          >
                            {param}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Error Alert */}
                {datasetsError && (
                  <div className="mb-6 rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{datasetsError}</p>
                  </div>
                )}

                {/* Actions Bar */}
                <div className="mb-6 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search datasets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-64 rounded-lg border border-gray-300 px-4 py-2 pl-10 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                      />
                      <svg
                        className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                    </div>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={filterByParams}
                        onChange={(e) => setFilterByParams(e.target.checked)}
                        className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="text-sm text-gray-700">Filter by parameters</span>
                    </label>
                  </div>

                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>New Dataset</span>
                    </button>
                  </div>
                </div>

                {/* Optimization Controls */}
                <div className="mb-6 rounded-lg bg-gradient-to-r from-purple-50 to-indigo-50 p-6 border border-purple-200">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Dataset-Based Optimization
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Select datasets to optimize your prompt against specific evaluation criteria
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      {filteredDatasets.length > 0 && (
                        <button
                          onClick={handleSelectAllDatasets}
                          className="text-sm text-purple-600 hover:text-purple-800 font-medium"
                        >
                          {selectedDatasetIds.length === filteredDatasets.length ? 'Deselect All' : 'Select All'}
                        </button>
                      )}
                      <button
                        onClick={handleTriggerOptimization}
                        disabled={selectedDatasetIds.length === 0 || optimizationLoading}
                        className={`btn-primary flex items-center space-x-2 ${
                          selectedDatasetIds.length === 0 || optimizationLoading
                            ? 'opacity-50 cursor-not-allowed'
                            : ''
                        }`}
                      >
                        {optimizationLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Optimizing...</span>
                          </>
                        ) : (
                          <>
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span>Optimize with Selected ({selectedDatasetIds.length})</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Optimization Result */}
                  {optimizationResult && (
                    <div className={`mt-4 rounded-md p-4 ${
                      optimizationResult.includes('failed') 
                        ? 'bg-red-50 text-red-800 border border-red-200' 
                        : 'bg-green-50 text-green-800 border border-green-200'
                    }`}>
                      <p className="text-sm font-medium">{optimizationResult}</p>
                    </div>
                  )}
                </div>

                {/* Dataset Grid */}
                {datasetsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                  </div>
                ) : filteredDatasets.length === 0 ? (
                  <div className="text-center py-12">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No datasets found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm ? 'Try adjusting your search' : 'Get started by creating a new dataset'}
                    </p>
                  </div>
                ) : (
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {filteredDatasets.map((dataset) => (
                      <DatasetCard
                        key={dataset.id}
                        dataset={dataset}
                        onDelete={() => handleDeleteDataset(dataset.id)}
                        onClick={() => navigate(`/evaluation/datasets/${dataset.id}`)}
                        selected={selectedDatasetIds.includes(dataset.id)}
                        onSelectionChange={(selected) => handleDatasetSelection(dataset.id, selected)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prompt Editor Modal */}
      {showPromptEditor && (
        <PromptEditor
          initialPrompt={promptLab?.active_prompt?.content || ''}
          promptLabName={promptLab?.name}
          promptLabDescription={promptLab?.description}
          onSave={handleSavePrompt}
          onCancel={() => setShowPromptEditor(false)}
          isCreating={!promptLab?.active_prompt?.content}
        />
      )}

      {/* Create Dataset Modal */}
      {showCreateModal && (
        <CreateDatasetModal
          promptLabId={id}
          promptLab={promptLab}
          onClose={() => setShowCreateModal(false)}
          onCreated={(datasetId: number) => {
            setShowCreateModal(false);
            navigate(`/evaluation/datasets/${datasetId}`);
          }}
        />
      )}

      {/* Optimization Confirmation Modal */}
      {showOptimizationModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowOptimizationModal(false)}></div>
            
            <div className="relative w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
              <div className="mb-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">Confirm Prompt Optimization</h3>
                </div>
                
                <div className="space-y-4 text-gray-700">
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <h4 className="font-semibold text-purple-900 mb-2">What will happen:</h4>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-start gap-2">
                        <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Your current prompt will be analyzed using {selectedDatasetIds.length} evaluation dataset{selectedDatasetIds.length > 1 ? 's' : ''}</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>AI will generate improved versions of your prompt based on the evaluation results</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>If improvements are found, a new version of your prompt will be created and activated</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <svg className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Your current prompt (v{promptLab?.active_prompt?.version || 1}) will be archived for reference</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div className="text-sm">
                        <p className="font-medium text-blue-900 mb-1">Note:</p>
                        <p className="text-blue-800">This process may take a few minutes. You'll be redirected to the Learning Progress tab to monitor the optimization.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowOptimizationModal(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmOptimization}
                  className="btn-primary flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Start Optimization
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Dataset Card Component
interface DatasetCardProps {
  dataset: EvaluationDataset;
  onClick: () => void;
  onDelete: () => void;
  selected: boolean;
  onSelectionChange: (selected: boolean) => void;
}

const DatasetCard: React.FC<DatasetCardProps> = ({ dataset, onClick, onDelete, selected, onSelectionChange }) => {
  return (
    <div className={`card-elevated group relative ${selected ? 'ring-2 ring-purple-500 bg-purple-50' : ''}`}>
      {/* Selection Checkbox */}
      <div className="absolute top-4 left-4 z-10">
        <input
          type="checkbox"
          checked={selected}
          onChange={(e) => {
            e.stopPropagation();
            onSelectionChange(e.target.checked);
          }}
          className="rounded border-gray-300 text-purple-600 focus:ring-purple-500 w-4 h-4"
        />
      </div>

      <div className="p-6 pl-12 cursor-pointer" onClick={onClick}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600">
              {dataset.name}
            </h3>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {dataset.description}
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="ml-2 p-1 text-gray-400 hover:text-red-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center">
            <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {dataset.case_count || 0} cases
          </div>
          {dataset.average_score !== undefined && (
            <div className="flex items-center">
              <svg className="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              {(dataset.average_score * 100).toFixed(1)}% avg
            </div>
          )}
        </div>

        {/* Parameters */}
        {dataset.parameters && dataset.parameters.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-2">
              {dataset.parameters.slice(0, 3).map((param) => (
                <span
                  key={param}
                  className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800"
                >
                  {param}
                </span>
              ))}
              {dataset.parameters.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{dataset.parameters.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Create Dataset Modal Component
interface CreateDatasetModalProps {
  promptLabId?: string;
  promptLab?: PromptLab | null;
  onClose: () => void;
  onCreated: (datasetId: number) => void;
}

const CreateDatasetModal: React.FC<CreateDatasetModalProps> = ({ promptLabId, promptLab, onClose, onCreated }) => {
  // Auto-generate initial name and description
  const initialData = generateDatasetNameAndDescription();
  
  // Get prompt lab parameters if available
  const promptLabParameters = promptLab?.active_prompt?.parameters || [];
  
  const [name, setName] = useState(initialData.name);
  const [description, setDescription] = useState(initialData.description);
  const [isEditingName, setIsEditingName] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateNewName = () => {
    const newData = generateDatasetNameAndDescription();
    setName(newData.name);
    setDescription(newData.description);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !description) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      
      const datasetData = {
        name,
        description,
        parameters: promptLabParameters,
        parameter_descriptions: {},
        prompt_lab_id: promptLabId,
      };
      
      const createdDataset = await evaluationService.createDataset(datasetData);
      onCreated(createdDataset.id);
    } catch (err) {
      setError('Failed to create dataset');
      console.error('Error creating dataset:', err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        
        <div className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Create Evaluation Dataset</h3>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Title Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Dataset Name
              </label>
              
              {isEditingName ? (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="flex-1 text-lg font-bold text-gray-900 border-0 border-b-2 border-purple-500 focus:outline-none focus:border-purple-600 bg-transparent"
                    autoFocus
                    onBlur={() => setIsEditingName(false)}
                    onKeyPress={(e) => e.key === 'Enter' && setIsEditingName(false)}
                  />
                  <button
                    type="button"
                    onClick={() => setIsEditingName(false)}
                    className="text-green-600 hover:text-green-700"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-bold text-gray-900">{name}</h4>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setIsEditingName(true)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Edit name"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={handleGenerateNewName}
                      className="text-gray-400 hover:text-gray-600"
                      title="Generate new name"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Description Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                placeholder="Describe what this dataset will be used for..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="btn-primary"
              >
                {creating ? 'Creating...' : 'Create Dataset'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
