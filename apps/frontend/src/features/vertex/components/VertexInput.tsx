// ---------------------------------------------------------------------------
// VertexInput — Multi-line input with send, stop, and workspace support
// ---------------------------------------------------------------------------

import { useRef, useCallback, type KeyboardEvent, type ChangeEvent } from 'react';
import { Send, Square, Paperclip } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

interface VertexInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  isExpanded?: boolean;
  disabled?: boolean;
}

export function VertexInput({
  onSend,
  onStop,
  isStreaming,
  isExpanded = false,
  disabled,
}: VertexInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    const text = textarea.value.trim();
    if (!text || isStreaming) return;
    onSend(text);
    textarea.value = '';
    textarea.style.height = 'auto';
    textarea.focus();
  }, [onSend, isStreaming]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    // Auto-resize up to 6 lines (~140px)
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, isExpanded ? 140 : 96)}px`;
  }, [isExpanded]);

  return (
    <div className="border-t border-border/40 bg-card/60 px-3 py-3">
      <div className={cn('w-full', isExpanded && 'max-w-4xl mx-auto px-2 sm:px-6')}>
        <div className="flex items-end gap-2 rounded-xl border border-border/60 bg-background/80 px-3 py-2 transition-colors focus-within:border-brand-400/60 focus-within:ring-1 focus-within:ring-brand-400/20">
          {/* Attachment placeholder — disabled */}
          <button
            disabled
            title="Attachments coming soon"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground/40 cursor-not-allowed"
          >
            <Paperclip className="h-4 w-4" />
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            placeholder="Ask Vertex anything or type a command..."
            rows={1}
            disabled={disabled}
            onKeyDown={handleKeyDown}
            onChange={handleChange}
            className={cn(
              'flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground/60',
              'outline-none scrollbar-none',
              isExpanded ? 'max-h-36' : 'max-h-24',
            )}
          />

          {/* Send / Stop button */}
          {isStreaming ? (
            <button
              onClick={onStop}
              title="Stop generating"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-500 transition-colors hover:bg-red-500/20 cursor-pointer"
            >
              <Square className="h-3 w-3 fill-current" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={disabled}
              title="Send message"
              className={cn(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-all cursor-pointer',
                'bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-sm',
                'hover:from-brand-500 hover:to-brand-600 hover:shadow-md',
                'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-sm',
              )}
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Footer hint */}
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground/50">
          Vertex can execute actions and answer questions. Verify important ERP information.
        </p>
      </div>
    </div>
  );
}
