// API client for backend communication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.message || 'An error occurred',
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  // Chat endpoints
  async sendMessage(message: string, sessionId?: string) {
    return this.request('/api/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, sessionId }),
    });
  }

  async getChatHistory(sessionId: string) {
    return this.request(`/api/chat/history/${sessionId}`);
  }

  // Agent endpoints
  async getAgentStates() {
    return this.request('/api/agents/states');
  }

  async getAgentCapabilities(agentId: string) {
    return this.request(`/api/agents/${agentId}/capabilities`);
  }

  // Orchestration endpoints
  async startOrchestration(config: unknown) {
    return this.request('/api/orchestrate/start', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async stopOrchestration(orchestrationId: string) {
    return this.request(`/api/orchestrate/stop/${orchestrationId}`, {
      method: 'POST',
    });
  }

  // Health check
  async health() {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();