'use client';

import { useState, useEffect } from 'react';
import { AgentState } from '@/types/agent';

export default function StateVisualization() {
  const [agentStates, setAgentStates] = useState<AgentState[]>([
    {
      id: 'orchestrator',
      name: 'Orchestrator Agent',
      status: 'active',
      currentTask: 'Waiting for input',
      memory: {
        shortTerm: ['User query received', 'Processing request'],
        longTerm: ['Session started', 'Context initialized'],
      },
      connections: ['python-executor', 'web-search'],
    },
    {
      id: 'python-executor',
      name: 'Python Executor',
      status: 'idle',
      currentTask: null,
      memory: {
        shortTerm: [],
        longTerm: ['Executor initialized'],
      },
      connections: ['orchestrator'],
    },
    {
      id: 'web-search',
      name: 'Web Search Agent',
      status: 'idle',
      currentTask: null,
      memory: {
        shortTerm: [],
        longTerm: ['Search API connected'],
      },
      connections: ['orchestrator'],
    },
  ]);

  // TODO: Connect to backend WebSocket for real-time updates
  useEffect(() => {
    // Simulate state updates
    const interval = setInterval(() => {
      setAgentStates(prev => 
        prev.map(agent => ({
          ...agent,
          status: Math.random() > 0.7 ? 'active' : 'idle',
        }))
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      {agentStates.map((agent) => (
        <AgentStateCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}

interface AgentStateCardProps {
  agent: AgentState;
}

function AgentStateCard({ agent }: AgentStateCardProps) {
  const statusColors = {
    active: 'bg-green-500',
    idle: 'bg-yellow-500',
    error: 'bg-red-500',
  };

  return (
    <div className={`state-node ${agent.status === 'active' ? 'state-node-active' : ''}`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-sm">{agent.name}</h3>
        <span className="relative flex h-2 w-2">
          {agent.status === 'active' && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${statusColors[agent.status]}`}></span>
        </span>
      </div>
      
      {agent.currentTask && (
        <div className="mb-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Current Task:</p>
          <p className="text-sm">{agent.currentTask}</p>
        </div>
      )}

      {agent.memory.shortTerm.length > 0 && (
        <div className="mb-2">
          <p className="text-xs text-gray-500 dark:text-gray-400">Recent Memory:</p>
          <ul className="text-xs mt-1 space-y-1">
            {agent.memory.shortTerm.slice(0, 2).map((mem, idx) => (
              <li key={idx} className="truncate">• {mem}</li>
            ))}
          </ul>
        </div>
      )}

      {agent.connections.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Connected to:</p>
          <div className="flex flex-wrap gap-1 mt-1">
            {agent.connections.map((conn) => (
              <span
                key={conn}
                className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded"
              >
                {conn}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}