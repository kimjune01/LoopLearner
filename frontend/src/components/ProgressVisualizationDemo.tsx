/**
 * Progress Visualization Demo Page
 * Demonstrates the progress visualization capabilities without requiring a real session
 */

import React, { useState } from 'react';
import SessionProgressVisualization from './SessionProgressVisualization';

const ProgressVisualizationDemo: React.FC = () => {
  const [selectedDemo, setSelectedDemo] = useState<'session1' | 'session2' | 'session3'>('session1');
  
  // Mock session IDs for different demo scenarios
  const demoSessions = {
    session1: {
      id: 'demo-session-early',
      name: 'Early Learning Session',
      description: 'A session in early stages of learning with active optimization'
    },
    session2: {
      id: 'demo-session-mature',
      name: 'Mature Learning Session',
      description: 'A well-established session approaching convergence'
    },
    session3: {
      id: 'demo-session-converged',
      name: 'Converged Session',
      description: 'A session that has reached optimal performance'
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Progress Visualization Demo
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                Experience comprehensive learning progress visualization across different session stages
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                Demo Mode
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Demo Session Selector */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Choose a Demo Scenario
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(demoSessions).map(([key, session]) => (
              <button
                key={key}
                onClick={() => setSelectedDemo(key as any)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  selectedDemo === key
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <h3 className="font-semibold text-gray-900 mb-2">{session.name}</h3>
                <p className="text-sm text-gray-600">{session.description}</p>
                {selectedDemo === key && (
                  <div className="mt-2 inline-flex items-center text-sm text-purple-600">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Selected
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Demo Features Info */}
        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-3 flex items-center">
            <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Demo Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="flex items-start">
              <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <div>
                <div className="font-medium text-gray-900">Real-time Metrics</div>
                <div className="text-gray-600">Live confidence and performance tracking</div>
              </div>
            </div>
            <div className="flex items-start">
              <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <div>
                <div className="font-medium text-gray-900">Optimization Timeline</div>
                <div className="text-gray-600">Historical improvement visualization</div>
              </div>
            </div>
            <div className="flex items-start">
              <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <div className="font-medium text-gray-900">Convergence Detection</div>
                <div className="text-gray-600">Intelligent stopping criteria analysis</div>
              </div>
            </div>
            <div className="flex items-start">
              <svg className="w-4 h-4 mr-2 text-purple-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <div>
                <div className="font-medium text-gray-900">Feedback Analysis</div>
                <div className="text-gray-600">User interaction pattern insights</div>
              </div>
            </div>
          </div>
        </div>

        {/* Progress Visualization Component */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {demoSessions[selectedDemo].name} - Progress Overview
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {demoSessions[selectedDemo].description}
            </p>
          </div>
          
          <div className="p-6">
            <SessionProgressVisualization 
              sessionId={demoSessions[selectedDemo].id}
              onOptimizationTrigger={() => {
                console.log(`Demo optimization triggered for ${demoSessions[selectedDemo].name}`);
                alert(`Demo: Optimization triggered for ${demoSessions[selectedDemo].name}. In a real session, this would start the optimization process.`);
              }}
            />
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            How to Use Progress Visualization
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">📊 Monitoring Progress</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Track confidence scores in real-time</li>
                <li>• Monitor performance improvements over time</li>
                <li>• Observe feedback patterns and trends</li>
                <li>• Assess optimization effectiveness</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🎯 Making Decisions</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Use convergence assessment to stop optimization</li>
                <li>• Review recommendations for next steps</li>
                <li>• Analyze feedback to understand user preferences</li>
                <li>• Track ROI and computational efficiency</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressVisualizationDemo;