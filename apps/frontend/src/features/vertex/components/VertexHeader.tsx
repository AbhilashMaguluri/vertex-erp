// ---------------------------------------------------------------------------
// VertexHeader — Panel Header with Workspace Controls
// ---------------------------------------------------------------------------
// Contains: Branding + status (left), action controls (right).
// Close action is HERE — the floating FAB is hidden while the panel is open.
// ---------------------------------------------------------------------------

import { Sparkles, MessageSquarePlus, Trash2, X, PanelRightOpen, PanelRightClose } from 'lucide-react';
import type { VertexMode } from '../types/vertex';
import { pageDisplayName } from '../hooks/usePageContext';
import { cn } from '@/shared/utils/cn';

interface VertexHeaderProps {
  mode: VertexMode;
  currentPage: string;
  isDocked: boolean;
  onToggleDock: () => void;
  onNewChat: () => void;
  onClearChat: () => void;
  onClose: () => void;
  hasMessages: boolean;
}

export function VertexHeader({
  mode,
  currentPage,
  isDocked,
  onToggleDock,
  onNewChat,
  onClearChat,
  onClose,
  hasMessages,
}: VertexHeaderProps) {
  const isGuest = mode === 'guest';
  const statusText = isGuest ? 'Guest Mode' : pageDisplayName(currentPage);

  return (
    <div className="flex items-center justify-between border-b border-border/40 bg-card/60 px-3 py-2.5 select-none shrink-0">
      {/* Left — Branding + Status */}
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-sm shadow-brand-600/20">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold leading-tight text-foreground truncate">
              {isDocked ? 'Vertex AI Workspace' : 'Vertex'}
            </span>
            {isDocked && (
              <span className="shrink-0 rounded-md bg-brand-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand-600 dark:text-brand-400">
                Docked
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className={cn(
                'inline-block h-1.5 w-1.5 shrink-0 rounded-full',
                isGuest ? 'bg-amber-400' : 'bg-emerald-500',
              )}
            />
            <span className="text-[11px] text-muted-foreground leading-tight truncate">
              {statusText}
            </span>
          </div>
        </div>
      </div>

      {/* Right — Action Controls */}
      <div className="flex items-center gap-0.5 shrink-0">
        <HeaderButton
          icon={<MessageSquarePlus className="h-4 w-4" />}
          label="New Chat"
          onClick={onNewChat}
        />
        {hasMessages && (
          <HeaderButton
            icon={<Trash2 className="h-4 w-4" />}
            label="Clear Chat"
            onClick={onClearChat}
          />
        )}
        
        {/* Desktop Dock / Floating toggle button */}
        <div className="hidden sm:block">
          <HeaderButton
            icon={isDocked ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
            label={isDocked ? 'Undock to floating window' : 'Dock sidebar to right'}
            onClick={onToggleDock}
          />
        </div>

        {/* Visual separator before close */}
        <div className="mx-0.5 h-5 w-px bg-border/50" aria-hidden="true" />

        {/* Close — primary dismiss action */}
        <HeaderButton
          icon={<X className="h-4 w-4" />}
          label="Close Vertex"
          onClick={onClose}
          variant="close"
        />
      </div>
    </div>
  );
}

function HeaderButton({
  icon,
  label,
  onClick,
  variant = 'default',
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: 'default' | 'close';
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      className={cn(
        // 44×44 minimum touch target (WCAG 2.5.8). The visual icon is small
        // but the clickable/tappable area is large enough for touch.
        'flex h-8 w-8 items-center justify-center rounded-lg transition-colors cursor-pointer',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400/60 focus-visible:ring-offset-1',
        variant === 'close'
          ? 'text-muted-foreground hover:bg-red-500/10 hover:text-red-500'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground',
      )}
    >
      {icon}
    </button>
  );
}

