import React, { useState, useEffect } from 'react';

interface SystemStatus {
  scheduler_running: boolean;
  active_prompt_version: number | null;
  active_prompt_score: number | null;
  recent_feedback_count: number;
  recent_optimizations: number;
  last_optimization: string | null;
  next_check: string | null;
  daily_optimization_count: number;
  can_optimize: boolean;
}

interface PerformanceMetrics {
  total_improvement: number;
  current_score: number | null;
  baseline_score: number | null;
  feedback_quality: {
    total_feedback: number;
    acceptance_rate: number;
    rejection_rate: number;
    edit_rate: number;
  };
}

interface OptimizationActivity {
  total_runs: number;
  successful_runs: number;
  success_rate: number;
  average_improvement: number;
  recent_optimizations: Array<{
    id: number;
    old_version: number;
    new_version: number | null;
    status: string;
    improvement: number | null;
    started_at: string;
  }>;
}

interface DashboardData {
  system_status: SystemStatus;
  performance_metrics: PerformanceMetrics;
  optimization_activity: OptimizationActivity;
  real_time_status: {
    recent_activity: {
      emails_generated: number;
      drafts_created: number;
      feedback_received: number;
    };
    system_health: {
      active_prompt_exists: boolean;
      learning_velocity: number;
      system_operational: boolean;
    };
  };
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard/overview/');
      const result = await response.json();
      
      if (result.success) {
        setDashboardData(result.data);
        setLastUpdate(new Date().toLocaleTimeString());
        setError(null);
      } else {
        setError(result.error || 'Failed to fetch dashboard data');
      }
    } catch (err) {
      setError('Network error fetching dashboard data');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (isHealthy: boolean) => {
    return isHealthy ? 'text-green-600' : 'text-red-600';
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-600 text-lg">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="text-red-600 text-lg mb-4">Error: {error}</div>
          <button 
            onClick={fetchDashboardData} 
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-gray-600 text-lg">No dashboard data available</div>
      </div>
    );
  }

  const { system_status, performance_metrics, optimization_activity, real_time_status } = dashboardData;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex justify-between items-center pb-6 border-b-2 border-gray-200">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Loop Learner Dashboard</h1>
            <p className="text-gray-600">Real-time optimization monitoring and analytics</p>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>Last updated: {lastUpdate}</span>
            <button 
              onClick={fetchDashboardData} 
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              ↻ Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        
        {/* System Status Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Scheduler:</span>
              <span className={`font-semibold ${getStatusColor(system_status.scheduler_running)}`}>
                {system_status.scheduler_running ? 'Running' : 'Stopped'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Active Prompt:</span>
              <span className="font-semibold text-gray-900">
                v{system_status.active_prompt_version || 'None'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Performance Score:</span>
              <span className="font-semibold text-gray-900">
                {system_status.active_prompt_score ? 
                  `${(system_status.active_prompt_score * 100).toFixed(1)}%` : 
                  'N/A'
                }
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Daily Optimizations:</span>
              <span className="font-semibold text-gray-900">
                {system_status.daily_optimization_count}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Metrics Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Performance Metrics</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {performance_metrics.total_improvement > 0 ? '+' : ''}
                {performance_metrics.total_improvement.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 font-medium">Total Improvement</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {performance_metrics.feedback_quality.acceptance_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 font-medium">Acceptance Rate</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {performance_metrics.feedback_quality.total_feedback}
              </div>
              <div className="text-sm text-gray-600 font-medium">Total Feedback</div>
            </div>
          </div>
        </div>

        {/* Real-time Activity Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity (1h)</h2>
          <div className="space-y-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600 mb-1">
                {real_time_status.recent_activity.emails_generated}
              </div>
              <div className="text-sm text-gray-600 font-medium">Emails Generated</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600 mb-1">
                {real_time_status.recent_activity.drafts_created}
              </div>
              <div className="text-sm text-gray-600 font-medium">Drafts Created</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600 mb-1">
                {real_time_status.recent_activity.feedback_received}
              </div>
              <div className="text-sm text-gray-600 font-medium">Feedback Received</div>
            </div>
          </div>
          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <span className={`font-semibold ${getStatusColor(real_time_status.system_health.system_operational)}`}>
              System {real_time_status.system_health.system_operational ? 'Operational' : 'Issues Detected'}
            </span>
            <span className="text-sm text-gray-600">
              {real_time_status.system_health.learning_velocity} feedback/hour
            </span>
          </div>
        </div>

        {/* Optimization Activity Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 lg:col-span-2">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Optimization Activity</h2>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="flex justify-between py-3 border-b border-gray-200">
              <span className="text-gray-600">Success Rate:</span>
              <span className="font-semibold">{optimization_activity.success_rate}%</span>
            </div>
            <div className="flex justify-between py-3 border-b border-gray-200">
              <span className="text-gray-600">Average Improvement:</span>
              <span className="font-semibold">+{optimization_activity.average_improvement}%</span>
            </div>
            <div className="flex justify-between py-3 border-b border-gray-200">
              <span className="text-gray-600">Total Runs:</span>
              <span className="font-semibold">{optimization_activity.total_runs}</span>
            </div>
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Recent Optimizations</h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {optimization_activity.recent_optimizations.slice(0, 5).map((opt) => (
              <div key={opt.id} className="grid grid-cols-4 gap-4 items-center p-3 border border-gray-200 rounded-lg bg-gray-50">
                <div className="font-semibold text-gray-900">
                  v{opt.old_version} → v{opt.new_version || '?'}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getStatusBadgeClass(opt.status)}`}>
                    {opt.status}
                  </span>
                  {opt.improvement && (
                    <span className="text-green-600 font-semibold text-sm">
                      +{opt.improvement.toFixed(1)}%
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-600">
                  {formatDateTime(opt.started_at)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Timeline Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Timeline</h2>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 font-medium mb-2">Last Optimization:</div>
              <div className="font-semibold text-gray-900">
                {formatDateTime(system_status.last_optimization)}
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 font-medium mb-2">Next Check:</div>
              <div className="font-semibold text-gray-900">
                {formatDateTime(system_status.next_check)}
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 font-medium mb-2">Can Optimize:</div>
              <div className={`font-semibold ${getStatusColor(system_status.can_optimize)}`}>
                {system_status.can_optimize ? 'Yes' : 'No'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;