import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { AgnoAgent } from "@ag-ui/agno";
import { NextRequest } from "next/server";

// Create the service adapter
const serviceAdapter = new ExperimentalEmptyAdapter();

// Create the runtime with the AG-UI agent
const runtime = new CopilotRuntime({
  agents: {
    orchestrator: new AgnoAgent({
      url: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/ag-ui",
    }),
  },
});

// Export the POST handler for the API route
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};