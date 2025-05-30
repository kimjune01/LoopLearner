import React, { useState } from 'react';
import type { EmailMessage } from '../types/email';
import { emailService } from '../services/emailService';

interface EmailGeneratorProps {
  onEmailGenerated: (email: EmailMessage) => void;
}

export const EmailGenerator: React.FC<EmailGeneratorProps> = ({ onEmailGenerated }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [scenarioType, setScenarioType] = useState('random');

  const handleGenerateEmail = async () => {
    setIsGenerating(true);
    try {
      const email = await emailService.generateFakeEmail(scenarioType);
      onEmailGenerated(email);
    } catch (error) {
      console.error('Failed to generate email:', error);
      // TODO: Add proper error handling/display
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="email-generator">
      <h3>Generate Fake Email</h3>
      <div>
        <label htmlFor="scenario-select">Scenario Type:</label>
        <select 
          id="scenario-select"
          value={scenarioType} 
          onChange={(e) => setScenarioType(e.target.value)}
          disabled={isGenerating}
        >
          <option value="random">Random</option>
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="complaint">Complaint</option>
          <option value="inquiry">Inquiry</option>
        </select>
      </div>
      <button 
        onClick={handleGenerateEmail} 
        disabled={isGenerating}
        className="generate-button"
      >
        {isGenerating ? 'Generating...' : 'Generate Email'}
      </button>
    </div>
  );
};