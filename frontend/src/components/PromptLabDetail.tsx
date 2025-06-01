import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { PromptLab } from '../types/promptLab';
import { promptLabService } from '../services/promptLabService';
import { PromptEditor } from './PromptEditor';
import PromptLabProgressVisualization from './PromptLabProgressVisualization';

export const PromptLabDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [promptLab, setPromptLab] = useState<PromptLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isPromptExpanded, setIsPromptExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'prompt' | 'progress'>('prompt');
  const exportMenuRef = useRef<HTMLDivElement>(null);

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
  }, [id]);

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

  const handleRunEvals = async () => {
    // Scroll to the evaluation section where users can manage their evaluation datasets
    const evaluationSection = document.querySelector('[data-section="evaluation"]');
    if (evaluationSection) {
      evaluationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

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
            onClick={() => setActiveTab('prompt')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'prompt'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            System Prompt
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'progress'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Learning Progress
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
              <div className="text-center mb-8">
                <h2 className="text-4xl font-bold text-gray-900 mb-3 bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  Current System Prompt
                </h2>
                <p className="text-gray-600 text-lg">
                  The evolving intelligence guiding this prompt lab
                </p>
              </div>
              
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
                        onClick={handleRunEvals}
                        title="Scroll to evaluation section to manage evaluation datasets and test prompt performance"
                        className="btn-primary flex items-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Manage Evaluations
                      </button>
                      <button 
                        onClick={() => setShowPromptEditor(true)}
                        className="btn-secondary flex items-center gap-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Edit Prompt
                      </button>
                      <button className="btn-secondary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        View History
                      </button>
                      <button className="btn-secondary flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Performance Metrics
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
                  <button className="w-full btn-secondary text-left justify-start">
                    Start Learning Lab
                  </button>
                  <button className="w-full btn-secondary text-left justify-start">
                    Generate Test Email
                  </button>
                  <button className="w-full btn-secondary text-left justify-start">
                    Export Prompt Lab Data
                  </button>
                </div>
              </div>
            </div>

                {/* Evaluation Section */}
                <div className="mt-12" data-section="evaluation">
              <div className="card-elevated p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Evaluation Datasets
                </h3>
                <p className="text-gray-600 mb-4">
                  Test your prompt performance against predefined evaluation datasets.
                </p>
                <Link 
                  to={`/prompt-labs/${id}/evaluation/datasets`}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  View Evaluation Datasets
                </Link>
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
    </div>
  );
};
