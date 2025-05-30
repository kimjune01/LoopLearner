import React, { useState } from 'react';
import './InnerLoopProgress.css';

export interface RewriteCandidate {
  content: string;
  confidence: number;
  reasoning: string;
}

export interface LoopMetrics {
  iteration: number;
  mode: 'conservative' | 'exploratory' | 'hybrid';
  candidates_generated: number;
  best_candidate_score: number;
  reward_components: {
    f1_score: number;
    perplexity: number;
    human_feedback: number;
    exact_match: number;
  };
  training_examples_collected: number;
  scenario: string;
  rewrite_triggered: boolean;
  performance_improvement: number;
}

export interface InnerLoopState {
  status: 'idle' | 'generating' | 'evaluating' | 'training' | 'completed';
  current_metrics: LoopMetrics;
  candidates: RewriteCandidate[];
  selected_candidate: RewriteCandidate | null;
  meta_prompt_template: string;
  dual_llm_coordination: {
    rewriter_performance: number;
    task_llm_performance: number;
    coordination_score: number;
  };
  human_feedback_queue: Array<{
    action: 'accept' | 'reject' | 'edit' | 'ignore';
    confidence: number;
    timestamp: string;
  }>;
}

export const InnerLoopProgress: React.FC = () => {
  const [loopState, setLoopState] = useState<InnerLoopState>({
    status: 'idle',
    current_metrics: {
      iteration: 0,
      mode: 'conservative',
      candidates_generated: 0,
      best_candidate_score: 0,
      reward_components: { f1_score: 0, perplexity: 0, human_feedback: 0, exact_match: 0 },
      training_examples_collected: 0,
      scenario: 'professional',
      rewrite_triggered: false,
      performance_improvement: 0
    },
    candidates: [],
    selected_candidate: null,
    meta_prompt_template: '',
    dual_llm_coordination: {
      rewriter_performance: 0,
      task_llm_performance: 0,
      coordination_score: 0
    },
    human_feedback_queue: []
  });

  const [isRunning, setIsRunning] = useState(false);

  // Simulate the innermost loop progression
  const simulateLoopProgress = () => {
    setIsRunning(true);
    
    // Phase 1: Generating candidates
    setTimeout(() => {
      setLoopState(prev => ({
        ...prev,
        status: 'generating',
        current_metrics: {
          ...prev.current_metrics,
          iteration: prev.current_metrics.iteration + 1,
          candidates_generated: 3
        },
        candidates: [
          { content: 'You are a highly professional email assistant focused on clear communication.', confidence: 0.85, reasoning: 'Enhanced clarity and professionalism' },
          { content: 'You are an expert email writer specializing in business correspondence.', confidence: 0.78, reasoning: 'Domain-specific expertise emphasis' },
          { content: 'You are a skilled communication assistant optimized for professional email drafting.', confidence: 0.92, reasoning: 'Combined optimization and skill focus' }
        ]
      }));
    }, 1000);

    // Phase 2: Evaluating candidates
    setTimeout(() => {
      setLoopState(prev => ({
        ...prev,
        status: 'evaluating',
        current_metrics: {
          ...prev.current_metrics,
          best_candidate_score: 0.92,
          reward_components: {
            f1_score: 0.89,
            perplexity: 0.76,
            human_feedback: 0.95,
            exact_match: 0.82
          }
        },
        selected_candidate: prev.candidates[2],
        dual_llm_coordination: {
          rewriter_performance: 0.87,
          task_llm_performance: 0.91,
          coordination_score: 0.89
        }
      }));
    }, 2500);

    // Phase 3: Training feedback integration
    setTimeout(() => {
      setLoopState(prev => ({
        ...prev,
        status: 'training',
        current_metrics: {
          ...prev.current_metrics,
          training_examples_collected: prev.current_metrics.training_examples_collected + 1,
          performance_improvement: 0.15
        },
        human_feedback_queue: [
          { action: 'accept', confidence: 0.9, timestamp: new Date().toISOString() },
          { action: 'edit', confidence: 0.7, timestamp: new Date().toISOString() }
        ]
      }));
    }, 4000);

    // Phase 4: Completed
    setTimeout(() => {
      setLoopState(prev => ({
        ...prev,
        status: 'completed',
        current_metrics: {
          ...prev.current_metrics,
          rewrite_triggered: true
        }
      }));
      setIsRunning(false);
    }, 5500);
  };

  const resetLoop = () => {
    setLoopState(prev => ({
      ...prev,
      status: 'idle',
      candidates: [],
      selected_candidate: null,
      human_feedback_queue: []
    }));
  };

  const getStatusColor = (status: InnerLoopState['status']) => {
    switch (status) {
      case 'idle': return '#6b7280';
      case 'generating': return '#3b82f6';
      case 'evaluating': return '#f59e0b';
      case 'training': return '#8b5cf6';
      case 'completed': return '#10b981';
      default: return '#6b7280';
    }
  };

  return (
    <div className="inner-loop-progress">
      <div className="loop-header">
        <h2>PRewrite Innermost Loop Progress</h2>
        <div className="loop-controls">
          <button 
            onClick={simulateLoopProgress} 
            disabled={isRunning}
            className="start-button"
          >
            {isRunning ? 'Running...' : 'Start Loop'}
          </button>
          <button onClick={resetLoop} className="reset-button">
            Reset
          </button>
        </div>
      </div>

      <div className="status-indicator">
        <div 
          className="status-dot" 
          style={{ backgroundColor: getStatusColor(loopState.status) }}
        />
        <span className="status-text">{loopState.status.toUpperCase()}</span>
        <span className="iteration-counter">Iteration {loopState.current_metrics.iteration}</span>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <h4>Mode</h4>
          <div className="metric-value">{loopState.current_metrics.mode}</div>
        </div>
        <div className="metric-card">
          <h4>Candidates</h4>
          <div className="metric-value">{loopState.current_metrics.candidates_generated}</div>
        </div>
        <div className="metric-card">
          <h4>Best Score</h4>
          <div className="metric-value">{loopState.current_metrics.best_candidate_score.toFixed(3)}</div>
        </div>
        <div className="metric-card">
          <h4>Training Examples</h4>
          <div className="metric-value">{loopState.current_metrics.training_examples_collected}</div>
        </div>
      </div>

      <div className="reward-breakdown">
        <h3>Reward Components</h3>
        <div className="reward-bars">
          {Object.entries(loopState.current_metrics.reward_components).map(([key, value]) => (
            <div key={key} className="reward-bar">
              <label>{key.replace('_', ' ').toUpperCase()}</label>
              <div className="bar-container">
                <div 
                  className="bar-fill" 
                  style={{ width: `${value * 100}%` }}
                />
                <span className="bar-value">{value.toFixed(3)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="candidates-section">
        <h3>Generated Candidates</h3>
        {loopState.candidates.length > 0 ? (
          <div className="candidates-list">
            {loopState.candidates.map((candidate, index) => (
              <div 
                key={index} 
                className={`candidate-card ${loopState.selected_candidate === candidate ? 'selected' : ''}`}
              >
                <div className="candidate-header">
                  <span className="confidence-score">
                    Confidence: {candidate.confidence.toFixed(3)}
                  </span>
                  {loopState.selected_candidate === candidate && (
                    <span className="selected-badge">SELECTED</span>
                  )}
                </div>
                <div className="candidate-content">{candidate.content}</div>
                <div className="candidate-reasoning">{candidate.reasoning}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-candidates">No candidates generated yet</div>
        )}
      </div>

      <div className="coordination-metrics">
        <h3>Dual-LLM Coordination</h3>
        <div className="coordination-grid">
          <div className="coord-metric">
            <label>Rewriter Performance</label>
            <div className="coord-value">{loopState.dual_llm_coordination.rewriter_performance.toFixed(3)}</div>
          </div>
          <div className="coord-metric">
            <label>Task LLM Performance</label>
            <div className="coord-value">{loopState.dual_llm_coordination.task_llm_performance.toFixed(3)}</div>
          </div>
          <div className="coord-metric">
            <label>Coordination Score</label>
            <div className="coord-value">{loopState.dual_llm_coordination.coordination_score.toFixed(3)}</div>
          </div>
        </div>
      </div>

      <div className="feedback-queue">
        <h3>Human Feedback Queue</h3>
        {loopState.human_feedback_queue.length > 0 ? (
          <div className="feedback-list">
            {loopState.human_feedback_queue.map((feedback, index) => (
              <div key={index} className={`feedback-item feedback-${feedback.action}`}>
                <span className="feedback-action">{feedback.action.toUpperCase()}</span>
                <span className="feedback-confidence">Confidence: {feedback.confidence.toFixed(2)}</span>
                <span className="feedback-time">{new Date(feedback.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-feedback">No feedback in queue</div>
        )}
      </div>

      {loopState.current_metrics.performance_improvement > 0 && (
        <div className="improvement-indicator">
          <h3>Performance Improvement</h3>
          <div className="improvement-value">
            +{(loopState.current_metrics.performance_improvement * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  );
};