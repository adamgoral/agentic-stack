import { Message } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Components } from 'react-markdown';

interface MessageItemProps {
  message: Message;
}

export default function MessageItem({ message }: MessageItemProps) {
  const roleStyles = {
    user: 'chat-message chat-message-user',
    assistant: 'chat-message chat-message-assistant',
    system: 'chat-message chat-message-system',
  };

  const roleLabels = {
    user: 'You',
    assistant: 'AI Assistant',
    system: 'System',
  };

  // Format time consistently to avoid hydration mismatch
  const formatTime = (date: Date) => {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hours12 = hours % 12 || 12;
    return `${hours12}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')} ${ampm}`;
  };

  return (
    <div className={roleStyles[message.role]}>
      <div className="flex items-start space-x-2">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-semibold">
              {roleLabels[message.role]}
            </span>
            <span className="text-xs opacity-60" suppressHydrationWarning>
              {formatTime(message.timestamp)}
            </span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const inline = !match;
                  return !inline ? (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match[1]}
                      PreTag="div"
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              } as Components}
            >
              {message.content}
            </ReactMarkdown>
          </div>
          {message.metadata && (
            <div className="mt-2 text-xs opacity-60">
              {Object.entries(message.metadata).map(([key, value]) => (
                <span key={key} className="mr-3">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}