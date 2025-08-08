import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { CopilotProvider } from '@/components/providers/CopilotProvider';
import './globals.css';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Agentic Stack - AI Agent Orchestration Platform',
  description: 'A modern platform for orchestrating AI agents with AG-UI protocol support',
  keywords: ['AI', 'Agents', 'CopilotKit', 'AG-UI', 'Orchestration'],
  authors: [{ name: 'Agentic Stack Team' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#111827',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100">
        <CopilotProvider>
          {children}
        </CopilotProvider>
      </body>
    </html>
  );
}