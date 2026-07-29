// ---------------------------------------------------------------------------
// VertexMessage — Individual message bubble with response type renderer
// ---------------------------------------------------------------------------

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, RefreshCw, ThumbsUp, ThumbsDown, Check, Sparkles } from 'lucide-react';
import type { VertexMessage as VertexMessageType } from '../types/vertex';
import { cn } from '@/shared/utils/cn';

interface VertexMessageProps {
  message: VertexMessageType;
  onRegenerate?: (id: string) => void;
}

export function VertexMessage({ message, onRegenerate }: VertexMessageProps) {
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'streaming';
  const isError = message.status === 'error' || message.responseType === 'error';

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-2',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 shadow-sm mt-0.5">
          <Sparkles className="h-3.5 w-3.5 text-white" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          'group relative max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-sm shadow-brand-600/15'
            : isError
              ? 'bg-red-50 border border-red-200/60 text-red-800 dark:bg-red-950/30 dark:border-red-800/40 dark:text-red-300'
              : 'bg-card border border-border/40 text-foreground shadow-xs',
        )}
      >
        {/* Content */}
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <MessageContent content={message.content} isStreaming={isStreaming} />
        )}

        {/* Actions bar — assistant messages only, visible on hover */}
        {!isUser && message.status === 'complete' && message.content && (
          <MessageActions
            messageId={message.id}
            content={message.content}
            onRegenerate={onRegenerate}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Markdown renderer
// ---------------------------------------------------------------------------

function MessageContent({
  content,
  isStreaming,
}: {
  content: string;
  isStreaming: boolean;
}) {
  if (!content && isStreaming) return null; // TypingIndicator handles this

  return (
    <div className="vertex-markdown prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-pre:my-2 prose-code:text-xs">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom code block renderer
          code({ className, children, ...props }) {
            const isInline = !className;
            if (isInline) {
              return (
                <code
                  className="rounded-md bg-muted/80 px-1.5 py-0.5 text-xs font-mono text-foreground"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={cn('text-xs', className)} {...props}>
                {children}
              </code>
            );
          },
          pre({ children }) {
            return (
              <pre className="overflow-x-auto rounded-xl bg-navy-950 p-3 text-xs text-navy-100 dark:bg-navy-900/60">
                {children}
              </pre>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto rounded-lg border border-border/50">
                <table className="w-full text-xs">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border-b border-border/50 bg-muted/50 px-3 py-1.5 text-left font-semibold">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="border-b border-border/30 px-3 py-1.5">
                {children}
              </td>
            );
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-600 underline decoration-brand-300 underline-offset-2 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
              >
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
      {/* Streaming cursor */}
      {isStreaming && (
        <span className="ml-0.5 inline-block animate-pulse text-brand-500">
          ▊
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Message actions (Copy, Regenerate, Like, Dislike)
// ---------------------------------------------------------------------------

function MessageActions({
  messageId,
  content,
  onRegenerate,
}: {
  messageId: string;
  content: string;
  onRegenerate?: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState<'up' | 'down' | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may be unavailable
    }
  };

  return (
    <div className="mt-1.5 flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
      <ActionButton
        icon={copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
        label={copied ? 'Copied' : 'Copy'}
        onClick={handleCopy}
      />
      {onRegenerate && (
        <ActionButton
          icon={<RefreshCw className="h-3 w-3" />}
          label="Regenerate"
          onClick={() => onRegenerate(messageId)}
        />
      )}
      <ActionButton
        icon={<ThumbsUp className={cn('h-3 w-3', liked === 'up' && 'fill-current text-brand-600')} />}
        label="Like"
        onClick={() => setLiked((p) => (p === 'up' ? null : 'up'))}
      />
      <ActionButton
        icon={<ThumbsDown className={cn('h-3 w-3', liked === 'down' && 'fill-current text-red-500')} />}
        label="Dislike"
        onClick={() => setLiked((p) => (p === 'down' ? null : 'down'))}
      />
    </div>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
    >
      {icon}
    </button>
  );
}
