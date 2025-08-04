export interface AgentState {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  currentTask: string | null;
  memory: {
    shortTerm: string[];
    longTerm: string[];
  };
  connections: string[];
}

export interface AgentMessage {
  from: string;
  to: string;
  type: 'request' | 'response' | 'event';
  content: unknown;
  timestamp: Date;
}

export interface AgentCapability {
  name: string;
  description: string;
  parameters?: Record<string, unknown>;
}