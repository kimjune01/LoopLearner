/**
 * CaseWithOutputSelection Component
 * Displays a case with input parameters and allows output selection
 */
import React, { useState } from 'react';
import OutputVariationSelector from './OutputVariationSelector';

interface OutputVariation {
  index: number;
  text: string;
  style: string;
}

interface CaseData {
  preview_id: string;
  input_text: string;
  parameters: Record<string, string>;
  prompt_content: string;
  output_variations: OutputVariation[];
  selected_output_index: number | null;
  custom_output: string | null;
}

interface CaseWithOutputSelectionProps {
  caseData: CaseData;
  onCaseUpdate: (updatedCase: CaseData) => void;
  caseNumber?: number;
}

const CaseWithOutputSelection: React.FC<CaseWithOutputSelectionProps> = ({
  caseData,
  onCaseUpdate,
  caseNumber
}) => {
  const [showFullPrompt, setShowFullPrompt] = useState(false);
  const handleSelectionChange = (change: { type: 'variation' | 'custom'; index: number | null; customOutput: string | null }) => {
    const updatedCase: CaseData = {
      ...caseData,
      selected_output_index: change.type === 'variation' ? change.index : null,
      custom_output: change.type === 'custom' ? change.customOutput : null
    };
    onCaseUpdate(updatedCase);
  };

  const isValid = () => {
    if (caseData.selected_output_index !== null) {
      return true; // Valid variation selected
    }
    if (caseData.custom_output && caseData.custom_output.trim() !== '') {
      return true; // Valid custom output
    }
    return false; // No valid selection
  };

  const getSelectedOutputText = () => {
    if (caseData.selected_output_index !== null) {
      const variation = caseData.output_variations[caseData.selected_output_index];
      return variation?.text || '';
    }
    return caseData.custom_output || '';
  };

  const getSelectedOutputStyle = () => {
    if (caseData.selected_output_index !== null) {
      const variation = caseData.output_variations[caseData.selected_output_index];
      return variation?.style || '';
    }
    return 'custom';
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {caseNumber ? `Case ${caseNumber}` : 'Evaluation Case'}
        </h3>
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          isValid() 
            ? 'bg-green-100 text-green-800' 
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          {isValid() ? '✓ Ready to add' : '⚠ Please select an output option'}
        </div>
      </div>

      {/* Input Parameters */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Input Parameters</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(caseData.parameters).map(([key, value]) => (
            <div
              key={key}
              className="bg-blue-50 border border-blue-200 rounded-lg p-3"
            >
              <span className="text-xs font-medium text-blue-800 uppercase tracking-wider block mb-1">
                {key.replace(/_/g, ' ')}
              </span>
              <p className="text-sm text-blue-900 font-medium">{String(value)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* View Full Prompt Button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowFullPrompt(true)}
          className="text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded-md transition-colors"
        >
          View Full Prompt
        </button>
      </div>

      {/* Output Selection */}
      <div className="mb-6">
        <OutputVariationSelector
          variations={caseData.output_variations}
          selectedIndex={caseData.selected_output_index}
          customOutput={caseData.custom_output || ''}
          onSelectionChange={handleSelectionChange}
          showCustomInput={caseData.selected_output_index === null && caseData.custom_output !== null}
        />
      </div>

      {/* Selected Output Preview */}
      {isValid() && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Selected Output Preview:</h4>
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-purple-700 uppercase tracking-wide">
                Selected Response
              </span>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 capitalize">
                {getSelectedOutputStyle()}
              </span>
            </div>
            <p className="text-sm text-gray-800">{getSelectedOutputText()}</p>
          </div>
        </div>
      )}

      {/* Full Prompt Modal */}
      {showFullPrompt && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowFullPrompt(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Full Prompt with Parameter Substitutions</h3>
                <button
                  onClick={() => setShowFullPrompt(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Complete Prompt (With Substitutions)</h4>
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{caseData.input_text}</pre>
                  </div>
                </div>
                
                {caseData.prompt_content && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Original Template</h4>
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <pre className="text-sm text-blue-900 whitespace-pre-wrap font-mono">
                        {caseData.prompt_content}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowFullPrompt(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CaseWithOutputSelection;