// ---------------------------------------------------------------------------
// VertexPanel — Dual Mode AI Assistant & Docked Sidebar Workspace
// ---------------------------------------------------------------------------
// Compact Floating Mode: Quick access assistant, anchored bottom-right.
// Docked Workspace Mode: Persistent right AI sidebar (Copilot / Cursor style).
// The floating FAB (VertexButton) is hidden when this panel is open.
// Close action is in VertexHeader — no floating close button exists.
// ---------------------------------------------------------------------------

import { useEffect, useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useVertexChat } from '../hooks/useVertexChat';
import { usePageContext } from '../hooks/usePageContext';
import { VertexHeader } from './VertexHeader';
import { VertexMessages } from './VertexMessages';
import { VertexInput } from './VertexInput';
import { cn } from '@/shared/utils/cn';

interface VertexPanelProps {
  isOpen: boolean;
  isDocked: boolean;
  onClose: () => void;
  onToggleDock: () => void;
  width: number;
  height: number;
  dockedWidth: number;
  onResize: (width: number, height: number) => void;
  minWidth: number;
  maxWidth: number;
}

export function VertexPanel({
  isOpen,
  isDocked,
  onClose,
  onToggleDock,
  width,
  height,
  dockedWidth,
  onResize,
  minWidth,
  maxWidth,
}: VertexPanelProps) {
  const {
    messages,
    isStreaming,
    mode,
    userName,
    sendMessage,
    clearChat,
    newChat,
    regenerate,
    stopStreaming,
  } = useVertexChat();

  const pageContext = usePageContext();

  // Keyboard shortcuts (Escape to close)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
      }
    },
    [isOpen, onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // ----- Drag Resize Logic -----
  const isResizing = useRef(false);
  const startPos = useRef({ x: 0, y: 0 });
  const startSize = useRef({ w: width, h: height });
  const [resizing, setResizing] = useState(false);

  const onResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      isResizing.current = true;
      startPos.current = { x: e.clientX, y: e.clientY };
      startSize.current = { w: width, h: height };
      setResizing(true);

      const onMouseMove = (ev: MouseEvent) => {
        if (!isResizing.current) return;
        
        if (isDocked) {
          // Dragging left edge of right-docked sidebar:
          // Moving mouse left (smaller ev.clientX) INCREASES sidebar width
          const deltaX = startPos.current.x - ev.clientX;
          const newW = Math.max(minWidth, Math.min(maxWidth, startSize.current.w + deltaX));
          onResize(newW, startSize.current.h);
        } else {
          // Bottom-left handle in compact bottom-right floating mode
          const deltaX = startPos.current.x - ev.clientX;
          const deltaY = ev.clientY - startPos.current.y;
          const newW = Math.max(minWidth, Math.min(800, startSize.current.w + deltaX));
          const newH = Math.max(600, Math.min(900, startSize.current.h + deltaY));
          onResize(newW, newH);
        }
      };

      const onMouseUp = () => {
        isResizing.current = false;
        setResizing(false);
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    },
    [width, height, onResize, minWidth, maxWidth, isDocked],
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Mobile backdrop only (NO backdrop on desktop in any mode) */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 z-[51] bg-black/30 backdrop-blur-[2px] sm:hidden"
          />

          {/* Panel Container */}
          <motion.div
            initial={isDocked ? { x: '100%' } : { opacity: 0, scale: 0.95, y: 20 }}
            animate={isDocked ? { x: 0 } : { opacity: 1, scale: 1, y: 0 }}
            exit={isDocked ? { x: '100%' } : { opacity: 0, scale: 0.95, y: 20 }}
            transition={{
              type: 'spring',
              stiffness: 380,
              damping: 30,
              mass: 0.8,
            }}
            role="dialog"
            aria-label="Vertex AI assistant"
            className={cn(
              'flex flex-col overflow-hidden',
              'bg-card/98 backdrop-blur-2xl text-foreground',
              'shadow-2xl shadow-black/20 dark:shadow-black/40',

              /* Mobile: Always Fullscreen */
              'fixed inset-2 z-[52] sm:inset-auto rounded-2xl sm:rounded-none',

              /* Desktop Positioning */
              isDocked
                ? 'sm:fixed sm:right-0 sm:top-0 sm:bottom-0 sm:z-40 sm:border-l sm:border-border/80'
                : 'sm:fixed sm:z-[52] sm:bottom-6 sm:right-6 sm:rounded-2xl sm:border sm:border-border/60',
            )}
          >
            {/* Dynamic CSS Sizing for Desktop */}
            <style>{`
              @media (min-width: 640px) {
                [data-vertex-panel] {
                  width: ${isDocked ? dockedWidth : width}px !important;
                  height: ${isDocked ? '100vh' : `${height}px`} !important;
                }
              }
            `}</style>

            <div
              data-vertex-panel
              className="flex h-full w-full flex-col relative"
            >
              {/* Header */}
              <VertexHeader
                mode={mode}
                currentPage={pageContext.page}
                isDocked={isDocked}
                onToggleDock={onToggleDock}
                onNewChat={newChat}
                onClearChat={clearChat}
                onClose={onClose}
                hasMessages={messages.length > 0}
              />

              {/* Scrollable Conversation Area */}
              <VertexMessages
                messages={messages}
                isStreaming={isStreaming}
                mode={mode}
                userName={userName}
                isExpanded={isDocked}
                onPromptClick={sendMessage}
                onRegenerate={regenerate}
              />

              {/* Fixed Input Area */}
              <VertexInput
                onSend={sendMessage}
                onStop={stopStreaming}
                isStreaming={isStreaming}
                isExpanded={isDocked}
              />

              {/* Desktop Resize Handles */}
              {isDocked ? (
                /* Docked Mode: Draggable Left Border Handle */
                <div
                  onMouseDown={onResizeStart}
                  className={cn(
                    'hidden sm:block absolute left-0 top-0 bottom-0 z-20 w-1.5 cursor-ew-resize transition-colors',
                    resizing ? 'bg-brand-500/50' : 'hover:bg-brand-500/30',
                  )}
                  title="Drag left/right to resize AI sidebar (420px - 700px)"
                />
              ) : (
                /* Compact Mode: Bottom-Left Corner Handle */
                <div
                  onMouseDown={onResizeStart}
                  className={cn(
                    'hidden sm:block absolute bottom-0 left-0 z-20 h-5 w-5 cursor-nesw-resize transition-opacity',
                    resizing ? 'opacity-90' : 'opacity-0 hover:opacity-70',
                  )}
                  title="Drag to resize assistant"
                >
                  <svg viewBox="0 0 20 20" className="h-full w-full text-muted-foreground" fill="currentColor">
                    <circle cx="4" cy="16" r="1.5" />
                    <circle cx="4" cy="10" r="1.5" />
                    <circle cx="10" cy="16" r="1.5" />
                  </svg>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
