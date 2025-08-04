'use client';

import { useState } from 'react';
import ChatInterface from '@/components/chat/ChatInterface';
import StateVisualization from '@/components/visualization/StateVisualization';

export default function ChatPage() {
  const [showStatePanel, setShowStatePanel] = useState(true);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold">Agent Chat Interface</h1>
            <button
              onClick={() => setShowStatePanel(!showStatePanel)}
              className="btn btn-outline"
              aria-label="Toggle state panel"
            >
              {showStatePanel ? 'Hide' : 'Show'} State Panel
            </button>
          </div>
        </header>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface />
        </div>
      </div>

      {/* State Visualization Panel */}
      {showStatePanel && (
        <aside className="w-96 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800">
          <div className="h-full flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <h2 className="text-lg font-semibold">Agent State</h2>
            </div>
            <div className="flex-1 overflow-auto p-6">
              <StateVisualization />
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}