export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-semibold">Agent Dashboard</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stats Cards */}
          <StatsCard
            title="Active Agents"
            value="3"
            description="Currently running"
            trend="up"
          />
          <StatsCard
            title="Messages Processed"
            value="1,247"
            description="Last 24 hours"
            trend="up"
          />
          <StatsCard
            title="Average Response Time"
            value="1.2s"
            description="Last hour"
            trend="down"
          />
        </div>

        {/* Agent Status Table */}
        <div className="mt-8 ag-ui-container">
          <div className="ag-ui-header">
            <h2 className="text-lg font-semibold">Agent Status</h2>
          </div>
          <div className="ag-ui-content">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agent ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Activity
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  <AgentRow
                    id="agent-001"
                    type="Orchestrator"
                    status="active"
                    lastActivity="2 minutes ago"
                  />
                  <AgentRow
                    id="agent-002"
                    type="Python Executor"
                    status="idle"
                    lastActivity="5 minutes ago"
                  />
                  <AgentRow
                    id="agent-003"
                    type="Web Search"
                    status="active"
                    lastActivity="Just now"
                  />
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Activity Log */}
        <div className="mt-8 ag-ui-container">
          <div className="ag-ui-header">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
          </div>
          <div className="ag-ui-content">
            <div className="space-y-3">
              <ActivityItem
                timestamp="2024-01-15 14:32:45"
                type="info"
                message="Agent orchestrator initialized successfully"
              />
              <ActivityItem
                timestamp="2024-01-15 14:32:30"
                type="success"
                message="Python executor completed task: data_analysis"
              />
              <ActivityItem
                timestamp="2024-01-15 14:32:15"
                type="warning"
                message="Web search agent rate limit approaching"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

interface StatsCardProps {
  title: string;
  value: string;
  description: string;
  trend?: 'up' | 'down' | 'neutral';
}

function StatsCard({ title, value, description, trend = 'neutral' }: StatsCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div className="ag-ui-container">
      <div className="ag-ui-content">
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="mt-2 text-3xl font-bold">{value}</p>
        <p className={`mt-2 text-sm ${trendColors[trend]}`}>
          {trend === 'up' && '↑'}
          {trend === 'down' && '↓'}
          {' '}{description}
        </p>
      </div>
    </div>
  );
}

interface AgentRowProps {
  id: string;
  type: string;
  status: 'active' | 'idle' | 'error';
  lastActivity: string;
}

function AgentRow({ id, type, status, lastActivity }: AgentRowProps) {
  const statusColors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    idle: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        {id}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
        {type}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[status]}`}>
          {status}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
        {lastActivity}
      </td>
    </tr>
  );
}

interface ActivityItemProps {
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

function ActivityItem({ timestamp, type, message }: ActivityItemProps) {
  const typeColors = {
    info: 'border-blue-500',
    success: 'border-green-500',
    warning: 'border-yellow-500',
    error: 'border-red-500',
  };

  return (
    <div className={`border-l-4 ${typeColors[type]} pl-4 py-2`}>
      <p className="text-xs text-gray-500 dark:text-gray-400">{timestamp}</p>
      <p className="text-sm mt-1">{message}</p>
    </div>
  );
}