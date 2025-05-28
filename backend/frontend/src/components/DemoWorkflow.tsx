import React, { useState, useEffect } from 'react';

interface DemoScenario {
  name: string;
  description: string;
  email_scenarios: string[];
  expected_improvement: number;
  learning_objectives: string[];
}

interface DemoStep {
  step_number: number;
  title: string;
  description: string;
  action_type: string;
  expected_duration: number;
  success_criteria: Record<string, any>;
}

interface DemoResults {
  scenario_name: string;
  total_emails_processed: number;
  total_feedback_collected: number;
  optimizations_triggered: number;
  final_performance_improvement: number;
  learning_objectives_met: string[];
  execution_time: string;
  detailed_metrics: Record<string, any>;
}

interface DemoReport {
  executive_summary: {
    scenario: string;
    total_improvement: string;
    execution_time: string;
    success_status: string;
  };
  learning_metrics: Record<string, number>;
  system_performance: Record<string, any>;
  demonstration_highlights: string[];
  next_steps: string[];
}

const DemoWorkflow: React.FC = () => {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [currentView, setCurrentView] = useState<'scenarios' | 'guided' | 'running' | 'results'>('scenarios');
  const [guidedSteps, setGuidedSteps] = useState<DemoStep[]>([]);
  const [demoResults, setDemoResults] = useState<DemoResults | null>(null);
  const [demoReport, setDemoReport] = useState<DemoReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await fetch('/api/demo/workflow/');
      const result = await response.json();
      
      if (result.success) {
        setScenarios(result.data.available_scenarios);
        if (result.data.available_scenarios.length > 0) {
          setSelectedScenario(result.data.available_scenarios[0].name);
        }
      } else {
        setError('Failed to fetch demo scenarios');
      }
    } catch (err) {
      setError('Network error fetching scenarios');
    }
  };

  const fetchGuidedSteps = async (scenarioName: string) => {
    try {
      setLoading(true);
      const response = await fetch('/api/demo/workflow/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_guided_steps',
          scenario_name: scenarioName
        })
      });
      
      const result = await response.json();
      if (result.success) {
        setGuidedSteps(result.data.guided_steps);
        setCurrentView('guided');
      } else {
        setError('Failed to fetch guided steps');
      }
    } catch (err) {
      setError('Network error fetching guided steps');
    } finally {
      setLoading(false);
    }
  };

  const runDemo = async (scenarioName: string) => {
    try {
      setLoading(true);
      setCurrentView('running');
      setError(null);
      
      const response = await fetch('/api/demo/workflow/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'run_demo',
          scenario_name: scenarioName
        })
      });
      
      const result = await response.json();
      if (result.success) {
        setDemoResults(result.data.demo_results);
        setDemoReport(result.data.demo_report);
        setCurrentView('results');
      } else {
        setError(`Demo failed: ${result.error}`);
        setCurrentView('scenarios');
      }
    } catch (err) {
      setError('Network error running demo');
      setCurrentView('scenarios');
    } finally {
      setLoading(false);
    }
  };

  const runQuickDemo = async () => {
    try {
      setLoading(true);
      setCurrentView('running');
      setError(null);
      
      const response = await fetch('/api/demo/workflow/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'quick_demo'
        })
      });
      
      const result = await response.json();
      if (result.success && result.data.success) {
        const demoData = result.data.demo_results;
        setDemoResults(demoData);
        setDemoReport(result.data.demo_report);
        setCurrentView('results');
      } else {
        setError(`Quick demo failed: ${result.data?.error || result.error}`);
        setCurrentView('scenarios');
      }
    } catch (err) {
      setError('Network error running quick demo');
      setCurrentView('scenarios');
    } finally {
      setLoading(false);
    }
  };

  const resetDemo = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/demo/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      if (result.success) {
        setCurrentView('scenarios');
        setDemoResults(null);
        setDemoReport(null);
        setCurrentStep(0);
        setError(null);
      } else {
        setError('Failed to reset demo data');
      }
    } catch (err) {
      setError('Network error resetting demo');
    } finally {
      setLoading(false);
    }
  };

  const renderScenarios = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Choose Demo Scenario</h2>
        <p className="text-gray-600 text-lg">Select a learning scenario to demonstrate adaptive optimization</p>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {scenarios.map((scenario) => (
          <div
            key={scenario.name}
            className={`border-2 rounded-xl p-6 cursor-pointer transition-all ${
              selectedScenario === scenario.name
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedScenario(scenario.name)}
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-3">{scenario.name}</h3>
            <p className="text-gray-600 mb-4">{scenario.description}</p>
            
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-500">Email Types:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {scenario.email_scenarios.map((type) => (
                    <span
                      key={type}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {type}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-500">Expected Improvement:</span>
                <span className="ml-2 text-green-600 font-semibold">+{scenario.expected_improvement}%</span>
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-500">Learning Objectives:</span>
                <ul className="mt-1 text-sm text-gray-600">
                  {scenario.learning_objectives.slice(0, 2).map((objective, index) => (
                    <li key={index} className="truncate">• {objective}</li>
                  ))}
                  {scenario.learning_objectives.length > 2 && (
                    <li className="text-gray-500">• +{scenario.learning_objectives.length - 2} more...</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex justify-center gap-4">
        <button
          onClick={() => fetchGuidedSteps(selectedScenario)}
          disabled={!selectedScenario || loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          View Guided Steps
        </button>
        
        <button
          onClick={() => runDemo(selectedScenario)}
          disabled={!selectedScenario || loading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Run Full Demo
        </button>
        
        <button
          onClick={runQuickDemo}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Quick Demo
        </button>
      </div>
    </div>
  );

  const renderGuidedSteps = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Guided Demo Steps</h2>
        <button
          onClick={() => setCurrentView('scenarios')}
          className="text-blue-600 hover:text-blue-700"
        >
          ← Back to Scenarios
        </button>
      </div>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900">Scenario: {selectedScenario}</h3>
        <p className="text-blue-700">Total estimated time: {guidedSteps.reduce((sum, step) => sum + step.expected_duration, 0)} seconds</p>
      </div>
      
      <div className="space-y-4">
        {guidedSteps.map((step, index) => (
          <div
            key={step.step_number}
            className={`border rounded-lg p-6 ${
              index === currentStep ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  index < currentStep
                    ? 'bg-green-500 text-white'
                    : index === currentStep
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {index < currentStep ? '✓' : step.step_number}
              </div>
              
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h4>
                <p className="text-gray-600 mb-3">{step.description}</p>
                
                <div className="flex gap-4 text-sm">
                  <span className="text-gray-500">
                    <strong>Type:</strong> {step.action_type}
                  </span>
                  <span className="text-gray-500">
                    <strong>Duration:</strong> ~{step.expected_duration}s
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex justify-center gap-4">
        <button
          onClick={() => runDemo(selectedScenario)}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Start Demo
        </button>
      </div>
    </div>
  );

  const renderRunning = () => (
    <div className="text-center space-y-6">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
      <h2 className="text-3xl font-bold text-gray-900">Running Demo Workflow</h2>
      <p className="text-gray-600 text-lg">
        Executing adaptive learning demonstration...
      </p>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
        <p className="text-blue-700 text-sm">
          This may take 30-60 seconds to complete all optimization cycles
        </p>
      </div>
    </div>
  );

  const renderResults = () => {
    if (!demoResults || !demoReport) return null;

    return (
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Demo Results</h2>
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
            demoReport.executive_summary.success_status === 'Completed Successfully'
              ? 'bg-green-100 text-green-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {demoReport.executive_summary.success_status}
          </div>
        </div>

        {/* Executive Summary */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Executive Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {demoReport.executive_summary.total_improvement}
              </div>
              <div className="text-sm text-gray-600">Total Improvement</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {demoResults.total_emails_processed}
              </div>
              <div className="text-sm text-gray-600">Emails Processed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {demoResults.optimizations_triggered}
              </div>
              <div className="text-sm text-gray-600">Optimizations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {demoReport.executive_summary.execution_time}
              </div>
              <div className="text-sm text-gray-600">Execution Time</div>
            </div>
          </div>
        </div>

        {/* Learning Metrics */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Learning Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(demoReport.learning_metrics).map(([key, value]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-lg font-semibold text-gray-900">{value}</div>
                <div className="text-sm text-gray-600 capitalize">
                  {key.replace(/_/g, ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Objectives Met */}
        {demoResults.learning_objectives_met.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Learning Objectives Achieved</h3>
            <div className="space-y-2">
              {demoResults.learning_objectives_met.map((objective, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center text-xs">
                    ✓
                  </span>
                  <span className="text-gray-700">{objective}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Demonstration Highlights */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Demonstration Highlights</h3>
          <ul className="space-y-2">
            {demoReport.demonstration_highlights.map((highlight, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-gray-700">{highlight}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex justify-center gap-4">
          <button
            onClick={() => setCurrentView('scenarios')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Run Another Demo
          </button>
          
          <button
            onClick={resetDemo}
            disabled={loading}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Reset Demo Data
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Demo Workflow</h1>
        <p className="text-gray-600 text-lg">
          Experience the complete adaptive learning cycle in action
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800">
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {currentView === 'scenarios' && renderScenarios()}
      {currentView === 'guided' && renderGuidedSteps()}
      {currentView === 'running' && renderRunning()}
      {currentView === 'results' && renderResults()}
    </div>
  );
};

export default DemoWorkflow;