// AG-UI Protocol types
export interface AGUIMessage {
  type: 'display' | 'input' | 'action' | 'state' | 'error';
  payload: unknown;
  metadata?: {
    timestamp: Date;
    agentId?: string;
    sessionId?: string;
    correlationId?: string;
  };
}

export interface AGUIDisplayMessage extends AGUIMessage {
  type: 'display';
  payload: {
    content: string;
    format?: 'text' | 'markdown' | 'html' | 'json';
    style?: Record<string, unknown>;
  };
}

export interface AGUIInputMessage extends AGUIMessage {
  type: 'input';
  payload: {
    prompt: string;
    inputType?: 'text' | 'number' | 'boolean' | 'select' | 'multiselect';
    options?: string[];
    validation?: {
      required?: boolean;
      min?: number;
      max?: number;
      pattern?: string;
    };
  };
}

export interface AGUIActionMessage extends AGUIMessage {
  type: 'action';
  payload: {
    action: string;
    parameters?: Record<string, unknown>;
    confirmation?: {
      required: boolean;
      message: string;
    };
  };
}

export interface AGUIStateMessage extends AGUIMessage {
  type: 'state';
  payload: {
    agentId: string;
    state: Record<string, unknown>;
    transitions?: string[];
  };
}

export interface AGUIErrorMessage extends AGUIMessage {
  type: 'error';
  payload: {
    code: string;
    message: string;
    details?: unknown;
    recoverable?: boolean;
  };
}