import React, { useState, useEffect } from 'react';
import type { SystemState } from '../types/state';
import type { OptimizationStatus } from '../services/optimizationService';
import { optimizationService } from '../services/optimizationService';

export const ProgressDashboard: React.FC = () => {
  const [systemState] = useState<SystemState | null>(null);
  const [optimizationStatus, setOptimizationStatus] = useState<OptimizationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // TODO: Implement state loading when state service is added
      const optStatus = await optimizationService.getOptimizationStatus();
      setOptimizationStatus(optStatus);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // TODO: Add proper error handling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const triggerOptimization = async () => {
    try {
      await optimizationService.triggerOptimization();
      // Refresh status after triggering
      await loadDashboardData();
    } catch (error) {
      console.error('Failed to trigger optimization:', error);
    }
  };

  if (loading) {
    return <div className="progress-dashboard loading">Loading dashboard...</div>;
  }

  return (
    <div className="progress-dashboard">
      <h3>Learning Progress</h3>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h4>Confidence Score</h4>
          <div className="metric-value">
            {systemState?.confidence_score?.toFixed(2) || 'N/A'}
          </div>
        </div>

        <div className="metric-card">
          <h4>Prompt Version</h4>
          <div className="metric-value">
            v{systemState?.current_prompt?.version || 'N/A'}
          </div>
        </div>

        <div className="metric-card">
          <h4>User Preferences</h4>
          <div className="metric-value">
            {systemState?.user_preferences?.length || 0}
          </div>
        </div>

        <div className="metric-card">
          <h4>Evaluation Snapshots</h4>
          <div className="metric-value">
            {systemState?.evaluation_snapshots?.length || 0}
          </div>
        </div>
      </div>

      <div className="optimization-section">
        <h4>Optimization Status</h4>
        <p>Status: {optimizationStatus?.status || 'Unknown'}</p>
        {optimizationStatus?.progress && (
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${optimizationStatus.progress}%` }}
            />
          </div>
        )}
        <button onClick={triggerOptimization} className="optimize-button">
          Trigger Optimization
        </button>
      </div>

      <div className="current-prompt-section">
        <h4>Current System Prompt</h4>
        <div className="prompt-content">
          {systemState?.current_prompt?.content || 'No prompt loaded'}
        </div>
      </div>
    </div>
  );
};