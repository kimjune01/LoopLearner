/**
 * OutputVariationSelector Component
 * Allows users to select from multiple AI-generated output variations or provide custom output
 */
import React, { useState } from 'react';

interface OutputVariation {
  index: number;
  text: string;
  style: string;
}

interface SelectionChange {
  type: 'variation' | 'custom';
  index: number | null;
  customOutput: string | null;
}

interface OutputVariationSelectorProps {
  variations: OutputVariation[];
  selectedIndex: number | null;
  customOutput: string;
  onSelectionChange: (change: SelectionChange) => void;
  showCustomInput?: boolean;
}

const OutputVariationSelector: React.FC<OutputVariationSelectorProps> = ({
  variations,
  selectedIndex,
  customOutput,
  onSelectionChange,
  showCustomInput = false
}) => {
  const [localCustomOutput, setLocalCustomOutput] = useState(customOutput);

  const handleVariationSelect = (index: number) => {
    setCustomSelected(false);
    onSelectionChange({
      type: 'variation',
      index,
      customOutput: null
    });
  };

  const handleCustomSelect = () => {
    setCustomSelected(true);
    onSelectionChange({
      type: 'custom',
      index: null,
      customOutput: localCustomOutput
    });
  };

  const handleCustomTextChange = (text: string) => {
    setLocalCustomOutput(text);
    onSelectionChange({
      type: 'custom',
      index: null,
      customOutput: text
    });
  };

  const [customSelected, setCustomSelected] = useState(selectedIndex === null && customOutput !== "");
  const isCustomSelected = customSelected || (selectedIndex === null && customOutput !== "");
  const showValidationError = isCustomSelected && customOutput.trim() === "";

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Select Output:</h3>
      
      {/* AI-Generated Variations */}
      <div className="space-y-3">
        {variations.map((variation) => (
          <div key={variation.index} className="relative">
            <div className="flex items-start space-x-3">
              <input
                type="radio"
                id={`variation-${variation.index}`}
                name="output-selection"
                value={variation.index}
                checked={selectedIndex === variation.index}
                onChange={() => handleVariationSelect(variation.index)}
                className="mt-1 h-4 w-4 text-purple-600 border-gray-300 focus:ring-purple-500"
              />
              <div className="flex-1">
                <label htmlFor={`variation-${variation.index}`} className="cursor-pointer">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Option {variation.index + 1}
                    </span>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                      {variation.style}
                    </span>
                  </div>
                  <div className={`p-3 rounded-lg border-2 transition-colors ${
                    selectedIndex === variation.index 
                      ? 'border-purple-500 bg-purple-50' 
                      : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                  }`}>
                    <p className="text-sm text-gray-700">{variation.text}</p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Custom Output Option */}
      <div className="relative">
        <div className="flex items-start space-x-3">
          <input
            type="radio"
            id="custom-output"
            name="output-selection"
            value="custom"
            checked={isCustomSelected}
            onChange={handleCustomSelect}
            className="mt-1 h-4 w-4 text-purple-600 border-gray-300 focus:ring-purple-500"
          />
          <div className="flex-1">
            <label htmlFor="custom-output" className="cursor-pointer">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-medium text-gray-700">Custom Output</span>
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Your Response
                </span>
              </div>
            </label>
            
            {isCustomSelected && (
              <div className="mt-2">
                <textarea
                  placeholder="Enter your custom response..."
                  value={localCustomOutput}
                  onChange={(e) => handleCustomTextChange(e.target.value)}
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-vertical ${
                    showValidationError 
                      ? 'border-red-500 bg-red-50' 
                      : 'border-gray-300'
                  }`}
                />
                {showValidationError && (
                  <p className="mt-1 text-sm text-red-600">
                    Custom output cannot be empty
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OutputVariationSelector;