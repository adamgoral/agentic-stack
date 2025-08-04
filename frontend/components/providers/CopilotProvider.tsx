'use client';

import { CopilotKit } from '@copilotkit/react-core';
import { CopilotPopup } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

interface CopilotProviderProps {
  children: React.ReactNode;
}

export function CopilotProvider({ children }: CopilotProviderProps) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      {children}
      <CopilotPopup
        instructions="You are an AI assistant helping with the Agentic Stack application. Help users understand and interact with the AI agent orchestration system."
        defaultOpen={false}
        clickOutsideToClose={false}
        labels={{
          title: "Agentic Stack Assistant",
          initial: "Hi! I'm here to help you with the Agentic Stack. How can I assist you today?",
        }}
      />
    </CopilotKit>
  );
}