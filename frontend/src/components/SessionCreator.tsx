import React, { useState } from 'react';

interface SessionCreatorProps {
  onCancel: () => void;
  onSubmit: (data: { name: string; description: string; initial_prompt?: string }) => void;
}

export const SessionCreator: React.FC<SessionCreatorProps> = ({ onCancel, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    initial_prompt: ''
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Session name is required';
    } else if (formData.name.length > 200) {
      newErrors.name = 'Session name must be less than 200 characters';
    }
    
    if (formData.description.length > 1000) {
      newErrors.description = 'Description must be less than 1000 characters';
    }
    
    if (formData.initial_prompt.length > 2000) {
      newErrors.initial_prompt = 'Initial prompt must be less than 2000 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const submitData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        ...(formData.initial_prompt.trim() && { initial_prompt: formData.initial_prompt.trim() })
      };
      
      await onSubmit(submitData);
    } catch (err) {
      console.error('Error creating session:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900">Create New Session</h2>
          <button 
            onClick={onCancel}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors duration-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Session Name */}
          <div>
            <label htmlFor="session-name" className="block text-sm font-medium text-gray-700 mb-2">
              Session Name *
            </label>
            <input
              id="session-name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="e.g., Professional Email Training"
              className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 ${
                errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              maxLength={200}
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
          </div>
          
          {/* Description */}
          <div>
            <label htmlFor="session-description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="session-description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Describe what this session is for and what you want to achieve..."
              className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 resize-none ${
                errors.description ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              rows={3}
              maxLength={1000}
            />
            {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
            <p className="mt-1 text-xs text-gray-500 text-right">{formData.description.length}/1000 characters</p>
          </div>
          
          {/* Initial Prompt */}
          <div>
            <label htmlFor="initial-prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Initial System Prompt (Optional)
            </label>
            <textarea
              id="initial-prompt"
              value={formData.initial_prompt}
              onChange={(e) => handleInputChange('initial_prompt', e.target.value)}
              placeholder="You are a helpful email assistant that generates professional and appropriate email responses."
              className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 resize-none ${
                errors.initial_prompt ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              rows={4}
              maxLength={2000}
            />
            {errors.initial_prompt && <p className="mt-1 text-sm text-red-600">{errors.initial_prompt}</p>}
            <p className="mt-1 text-xs text-gray-500">
              Leave empty to use the default prompt. You can always modify this later through the optimization process.
            </p>
            <p className="mt-1 text-xs text-gray-500 text-right">{formData.initial_prompt.length}/2000 characters</p>
          </div>
          
          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Creating...
                </div>
              ) : (
                'Create Session'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};