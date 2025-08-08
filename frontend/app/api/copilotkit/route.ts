import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";
import { NextRequest } from "next/server";

// Create OpenAI client instance
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "dummy-key-for-build",
});

// Create a service adapter using the OpenAI client
const serviceAdapter = new OpenAIAdapter({ openai });

// Create the runtime with remote actions for AG-UI
const runtime = new CopilotRuntime({
  remoteActions: [
    {
      url: process.env.NEXT_PUBLIC_BACKEND_URL + "/ag-ui" || "http://localhost:8000/ag-ui",
    },
  ],
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