# CopilotKit Integration

## Overview

The application is now integrated with CopilotKit to provide an AI-powered assistant that connects to your AG-UI backend endpoint.

## Components

### 1. API Route (`/app/api/copilotkit/route.ts`)

This route acts as a proxy between the CopilotKit frontend and your AG-UI backend:

- **Endpoint**: `/api/copilotkit`
- **Backend URL**: Configurable via `NEXT_PUBLIC_BACKEND_URL` environment variable
- **Default**: `http://localhost:8000/ag-ui`
- **Agent**: Uses the `AgnoAgent` from `@ag-ui/agno` package to communicate with your backend

### 2. CopilotProvider Component (`/components/providers/CopilotProvider.tsx`)

A client-side component that:
- Wraps the application with CopilotKit context
- Provides the CopilotPopup UI component
- Configures the runtime URL to point to `/api/copilotkit`

### 3. Layout Integration (`/app/layout.tsx`)

The root layout wraps all children with the `CopilotProvider` to ensure CopilotKit is available throughout the application.

## Configuration

### Environment Variables

Create or update `.env.local` with:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/ag-ui
```

This sets the backend AG-UI endpoint that CopilotKit will connect to.

## Usage

### Opening the Assistant

The CopilotPopup will appear as a chat widget in your application. Users can:
1. Click the chat icon to open the assistant
2. Type questions or commands
3. The assistant will process requests through your AG-UI backend

### Customization

You can customize the assistant by modifying `/components/providers/CopilotProvider.tsx`:

```typescript
<CopilotPopup
  instructions="Your custom instructions here"
  defaultOpen={true}  // Opens by default
  clickOutsideToClose={true}  // Allows closing by clicking outside
  labels={{
    title: "Your Assistant Title",
    initial: "Your welcome message",
  }}
/>
```

## Backend Requirements

Ensure your backend AG-UI endpoint is:
1. Running on the configured URL (default: `http://localhost:8000/ag-ui`)
2. Properly implementing the AG-UI protocol
3. Configured to handle CopilotKit requests

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify the backend is running and accessible at the configured URL
2. **CORS Issues**: Ensure your backend allows requests from your Next.js frontend URL
3. **TypeScript Errors**: Run `npm run type-check` to verify type compatibility

### Debugging

Check the browser console and network tab for:
- API requests to `/api/copilotkit`
- Response status and content
- Any error messages from CopilotKit

## Next Steps

1. Start your backend AG-UI server
2. Run the Next.js development server: `npm run dev`
3. Open the application and test the CopilotKit integration
4. Customize the assistant instructions and UI as needed