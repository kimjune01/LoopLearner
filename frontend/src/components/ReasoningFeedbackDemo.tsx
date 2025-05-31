/**
 * Reasoning Feedback Demo Page
 * Demonstrates the reasoning feedback UI functionality
 */

import React, { useState } from 'react';
import EnhancedDraftViewer from './EnhancedDraftViewer';
import type { EmailDraft } from '../types/email';

const ReasoningFeedbackDemo: React.FC = () => {
  const [feedbackLog, setFeedbackLog] = useState<Array<{
    timestamp: string;
    action: string;
    details: any;
  }>>([]);

  // Sample drafts with reasoning
  const sampleDrafts: EmailDraft[] = [
    {
      id: '1',
      content: `Thank you for reaching out about the project timeline concerns.

I understand your urgency and have reviewed the current status with our team. We can accelerate the delivery by reallocating resources from the beta phase to focus on the critical features you mentioned.

Here's what we propose:
- Complete core functionality by end of next week
- Begin user testing in parallel rather than sequentially
- Deliver the MVP two weeks ahead of the original schedule

Would you be available for a brief call tomorrow to discuss the revised timeline in detail?

Best regards,
Sarah`,
      reasons: [
        { text: 'Acknowledges the client\'s concerns upfront', confidence: 0.92 },
        { text: 'Provides a specific solution with clear action items', confidence: 0.88 },
        { text: 'Maintains professional tone while showing flexibility', confidence: 0.85 },
        { text: 'Suggests next steps to maintain momentum', confidence: 0.79 }
      ]
    },
    {
      id: '2',
      content: `Hi there!

Thanks for your message about the project timeline. I totally get that you need this done sooner - deadlines can be stressful!

Good news: I think we can make it work. The team and I had a quick huddle, and we've got some ideas to speed things up without cutting corners.

Let's chat tomorrow? I'll send over a calendar invite. We'll figure out a plan that works for everyone.

Cheers,
Sarah`,
      reasons: [
        { text: 'Uses casual, friendly tone', confidence: 0.90 },
        { text: 'Shows empathy for the client\'s situation', confidence: 0.87 },
        { text: 'Indicates willingness to accommodate without over-promising', confidence: 0.82 },
        { text: 'Keeps response brief and action-oriented', confidence: 0.75 }
      ]
    }
  ];

  const handleDraftAction = (
    draftId: string, 
    action: 'accept' | 'reject' | 'edit' | 'ignore', 
    reason?: string, 
    editedContent?: string
  ) => {
    const logEntry = {
      timestamp: new Date().toLocaleTimeString(),
      action: `Draft ${draftId} - ${action}`,
      details: {
        reason,
        editedContent: editedContent ? `${editedContent.substring(0, 50)}...` : undefined
      }
    };
    
    setFeedbackLog(prev => [logEntry, ...prev]);
  };

  const handleRatingSubmitted = () => {
    const logEntry = {
      timestamp: new Date().toLocaleTimeString(),
      action: 'Reasoning factor rated',
      details: { message: 'User provided feedback on reasoning' }
    };
    
    setFeedbackLog(prev => [logEntry, ...prev]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Reasoning Feedback Demo
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                Test the AI reasoning feedback interface with sample email drafts
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                Demo Mode
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - Draft Viewer */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                  How to Use This Demo
                </h2>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-2">1.</span>
                    Review the AI-generated draft responses below
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-2">2.</span>
                    Click "Show Reasoning" to see why the AI made specific choices
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-2">3.</span>
                    Rate individual reasoning factors with thumbs up/down
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-2">4.</span>
                    Use bulk actions to rate multiple factors at once
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-2">5.</span>
                    Accept, reject, edit, or ignore the draft with optional feedback
                  </li>
                </ul>
              </div>
            </div>

            <EnhancedDraftViewer
              sessionId="demo-session"
              drafts={sampleDrafts}
              onDraftAction={handleDraftAction}
              onRatingSubmitted={handleRatingSubmitted}
            />
          </div>

          {/* Sidebar - Feedback Log */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Feedback Activity Log
              </h3>
              
              {feedbackLog.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">
                  No feedback provided yet. Try interacting with the drafts!
                </p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {feedbackLog.map((entry, index) => (
                    <div key={index} className="border-l-4 border-purple-200 pl-3 py-2">
                      <div className="text-xs text-gray-500">{entry.timestamp}</div>
                      <div className="text-sm font-medium text-gray-900">{entry.action}</div>
                      {entry.details.reason && (
                        <div className="text-xs text-gray-600 mt-1">
                          Reason: {entry.details.reason}
                        </div>
                      )}
                      {entry.details.editedContent && (
                        <div className="text-xs text-gray-600 mt-1">
                          Edited: {entry.details.editedContent}
                        </div>
                      )}
                      {entry.details.message && (
                        <div className="text-xs text-gray-600 mt-1">
                          {entry.details.message}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {feedbackLog.length > 0 && (
                <button
                  onClick={() => setFeedbackLog([])}
                  className="mt-4 w-full text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear Log
                </button>
              )}
            </div>

            {/* Feature Highlights */}
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-6 mt-6">
              <h4 className="font-semibold text-gray-900 mb-3">
                Key Features
              </h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start">
                  <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Individual reasoning factor ratings
                </li>
                <li className="flex items-start">
                  <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Bulk selection and rating
                </li>
                <li className="flex items-start">
                  <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Confidence score visualization
                </li>
                <li className="flex items-start">
                  <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Rating statistics display
                </li>
                <li className="flex items-start">
                  <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Integrated draft feedback
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReasoningFeedbackDemo;