# Agentic Stack Frontend

A modern Next.js 14+ application with TypeScript for the Agentic Stack AI orchestration platform.

## Features

- **Next.js 14+ App Router**: Modern React framework with server components support
- **TypeScript**: Full type safety throughout the application
- **TailwindCSS**: Utility-first CSS framework for rapid UI development
- **AG-UI Protocol**: Support for advanced agent-user interaction protocol
- **Real-time Communication**: WebSocket integration for live agent state updates
- **Chat Interface**: Interactive chat with AI agents
- **State Visualization**: Real-time visualization of agent states and orchestration

## Project Structure

```
frontend/
├── app/                    # App Router pages and layouts
│   ├── chat/              # Chat interface page
│   ├── dashboard/         # Dashboard page
│   ├── globals.css        # Global styles and Tailwind imports
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── chat/             # Chat-related components
│   └── visualization/    # State visualization components
├── lib/                   # Utility functions and API clients
│   ├── api.ts            # Backend API client
│   ├── websocket.ts      # WebSocket client
│   └── utils.ts          # Utility functions
├── types/                 # TypeScript type definitions
│   ├── agent.ts          # Agent-related types
│   ├── agui.ts           # AG-UI protocol types
│   └── chat.ts           # Chat interface types
└── public/               # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn package manager

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Configure environment variables in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Development

Run the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Key Features

### Chat Interface (`/chat`)
- Real-time messaging with AI agents
- Markdown support with syntax highlighting
- Message history and session management
- State visualization panel

### Dashboard (`/dashboard`)
- Agent status monitoring
- Performance metrics
- Activity logs
- System health indicators

### Components

#### Chat Components
- `ChatInterface`: Main chat container with message handling
- `MessageList`: Displays chat messages
- `MessageItem`: Individual message rendering with markdown support
- `MessageInput`: User input with multi-line support

#### Visualization Components
- `StateVisualization`: Real-time agent state display
- Shows agent connections, memory, and current tasks

### API Integration

The frontend communicates with the backend through:
- REST API endpoints (via `/lib/api.ts`)
- WebSocket connections for real-time updates (via `/lib/websocket.ts`)

### Styling

- TailwindCSS for utility classes
- Custom AG-UI component styles in `globals.css`
- Dark mode support
- Responsive design

## Integration with Backend

The frontend expects the backend API to be running on `http://localhost:8000`. Key endpoints:

- `/api/chat/message` - Send chat messages
- `/api/agents/states` - Get agent states
- `/ws` - WebSocket connection for real-time updates

## Next Steps

1. **CopilotKit Integration**: Add CopilotKit providers and hooks
2. **Authentication**: Implement user authentication
3. **Persistence**: Add session storage and history
4. **Testing**: Add unit and integration tests
5. **Performance**: Implement React Query for data fetching

## Technologies Used

- Next.js 14.2+
- React 18.3+
- TypeScript 5.4+
- TailwindCSS 3.4+
- Zustand (state management)
- React Markdown
- React Syntax Highlighter

## License

Part of the Agentic Stack project.