// ---------------------------------------------------------------------------
// VertexMessages — Scrollable message list with auto-scroll and workspace layout
// ---------------------------------------------------------------------------

import { useEffect, useRef } from 'react';
import type { VertexMessage as VertexMessageType, VertexMode } from '../types/vertex';
import { VertexMessage } from './VertexMessage';
import { SuggestedPrompts } from './SuggestedPrompts';
import { TypingIndicator } from './TypingIndicator';
import { cn } from '@/shared/utils/cn';

interface VertexMessagesProps {
  messages: VertexMessageType[];
  isStreaming: boolean;
  mode: VertexMode;
  userName: string | null;
  isExpanded?: boolean;
  onPromptClick: (prompt: string) => void;
  onRegenerate: (id: string) => void;
}

export function VertexMessages({
  messages,
  isStreaming,
  mode,
  userName,
  isExpanded = false,
  onPromptClick,
  onRegenerate,
}: VertexMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or content streams
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Empty state — show welcome screen
  if (messages.length === 0) {
    return (
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className={cn('h-full w-full', isExpanded && 'max-w-4xl mx-auto px-4')}>
          <SuggestedPrompts
            mode={mode}
            userName={userName}
            onPromptClick={onPromptClick}
          />
        </div>
      </div>
    );
  }

  // Show typing indicator when streaming and assistant message has no content yet
  const lastMessage = messages[messages.length - 1];
  const showTyping =
    isStreaming &&
    lastMessage?.role === 'assistant' &&
    !lastMessage.content;

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto py-3">
      <div className={cn('w-full', isExpanded && 'max-w-4xl mx-auto px-2 sm:px-6')}>
        {messages.map((msg) => (
          <VertexMessage
            key={msg.id}
            message={msg}
            onRegenerate={onRegenerate}
          />
        ))}
        {showTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
