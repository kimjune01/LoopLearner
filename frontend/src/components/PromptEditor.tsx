import React, { useState } from 'react';

interface PromptEditorProps {
  initialPrompt?: string;
  sessionName?: string;
  sessionDescription?: string;
  onSave: (prompt: string) => void;
  onCancel: () => void;
  isCreating?: boolean;
}

export const PromptEditor: React.FC<PromptEditorProps> = ({
  initialPrompt = '',
  sessionName,
  sessionDescription,
  onSave,
  onCancel,
  isCreating = false
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [isSaving, setIsSaving] = useState(false);

  // Detect parameters in the prompt
  const detectParameters = (text: string) => {
    const parameterRegex = /(?<!\{)\{\{([^{}]+)\}\}(?!\})/g;
    const parameters = [];
    let match;
    while ((match = parameterRegex.exec(text)) !== null) {
      parameters.push(match[1].trim());
    }
    return [...new Set(parameters)]; // Remove duplicates
  };

  const parameters = detectParameters(prompt);

  const handleSave = async () => {
    if (!prompt.trim()) return;
    
    setIsSaving(true);
    try {
      await onSave(prompt);
    } catch (error) {
      console.error('Error saving prompt:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const suggestPrompt = () => {
    let suggestion = '';
    if (sessionName && sessionDescription) {
      suggestion = `You are an AI assistant designed for ${sessionName}. ${sessionDescription}

Key responsibilities:
- Provide helpful and accurate responses
- Maintain a professional and friendly tone
- Focus on delivering value to the user
- Ask clarifying questions when needed

Please respond thoughtfully and consider the context of each interaction.`;
    } else if (sessionName) {
      suggestion = `You are an AI assistant for ${sessionName}. Provide helpful, accurate, and professional responses while maintaining a friendly tone.`;
    } else {
      suggestion = `You are a helpful AI assistant. Provide accurate, thoughtful responses and ask clarifying questions when needed to better assist the user.`;
    }
    setPrompt(suggestion);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {isCreating ? 'Create System Prompt' : 'Edit System Prompt'}
              </h2>
              <p className="text-gray-600 mt-1">
                {sessionName && `For session: ${sessionName}`}
              </p>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Session Context */}
          {sessionDescription && (
            <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-purple-900 mb-1">Session Context</h3>
                  <p className="text-purple-800 text-sm">{sessionDescription}</p>
                </div>
              </div>
            </div>
          )}

          {/* Prompt Editor */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
                System Prompt
              </label>
              <button
                onClick={suggestPrompt}
                className="text-sm text-purple-600 hover:text-purple-800 transition-colors duration-200"
              >
                Generate suggestion based on context
              </button>
            </div>
            
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your system prompt here..."
              className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none font-mono text-sm leading-relaxed"
            />
            
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center gap-4">
                <span>{prompt.length} characters</span>
                {parameters.length > 0 && (
                  <span className="text-purple-600">
                    {parameters.length} parameter{parameters.length === 1 ? '' : 's'} detected
                  </span>
                )}
              </div>
              {prompt.length > 1000 && (
                <span className="text-orange-600">Long prompts may affect performance</span>
              )}
            </div>

            {/* Parameters Section */}
            {parameters.length > 0 && (
              <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-purple-900 mb-2">Detected Parameters</h4>
                    <div className="flex flex-wrap gap-2">
                      {parameters.map((param, index) => (
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
                      Parameters will be highlighted when the prompt is saved. They can be used for dynamic content injection.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tips */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">Tips for effective system prompts:</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Be specific about the AI's role and responsibilities</li>
              <li>• Include context about the domain or use case</li>
              <li>• Set expectations for tone and communication style</li>
              <li>• Mention any constraints or guidelines to follow</li>
              <li>• Use <code className="bg-blue-100 px-1 rounded text-blue-900">{'{{parameter_name}}'}</code> for dynamic content that can be filled in later</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onCancel}
              className="btn-secondary"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!prompt.trim() || isSaving}
              className="btn-primary flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {isCreating ? 'Create Prompt' : 'Save Changes'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};