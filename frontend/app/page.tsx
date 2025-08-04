import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
            Agentic Stack
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            AI Agent Orchestration Platform with AG-UI Protocol
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <FeatureCard
            title="Agent Orchestration"
            description="Coordinate multiple AI agents with sophisticated state management and A2A protocol support"
            icon="🤖"
          />
          <FeatureCard
            title="AG-UI Protocol"
            description="Advanced agent-user interaction protocol for seamless communication and state visualization"
            icon="💬"
          />
          <FeatureCard
            title="CopilotKit Integration"
            description="Powerful AI assistance with full CopilotKit support for enhanced user experiences"
            icon="✨"
          />
        </div>

        {/* Quick Start Section */}
        <div className="ag-ui-container mt-12">
          <div className="ag-ui-header">
            <h2 className="text-2xl font-semibold">Quick Start</h2>
          </div>
          <div className="ag-ui-content space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              Get started with the Agentic Stack platform. Access the chat interface to interact with AI agents,
              or explore the dashboard to monitor agent state and orchestration.
            </p>
            <div className="flex gap-4">
              <Link href="/chat" className="btn btn-primary">
                Open Chat Interface
              </Link>
              <Link href="/dashboard" className="btn btn-outline">
                View Dashboard
              </Link>
            </div>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span>System Online - Backend API: localhost:8000</span>
        </div>
      </div>
    </main>
  );
}

interface FeatureCardProps {
  title: string;
  description: string;
  icon: string;
}

function FeatureCard({ title, description, icon }: FeatureCardProps) {
  return (
    <div className="ag-ui-container hover:shadow-lg transition-shadow">
      <div className="ag-ui-content text-center space-y-3">
        <div className="text-4xl">{icon}</div>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      </div>
    </div>
  );
}