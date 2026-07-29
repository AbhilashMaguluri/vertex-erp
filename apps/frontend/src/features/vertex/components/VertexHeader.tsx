// ---------------------------------------------------------------------------
// VertexHeader — Panel Header with Docked Sidebar Controls
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
    <div className="flex items-center justify-between border-b border-border/40 bg-card/60 px-4 py-3 select-none">
      {/* Left — Branding + Status */}
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-sm shadow-brand-600/20">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold leading-tight text-foreground">
              {isDocked ? 'Vertex AI Workspace' : 'Vertex'}
            </span>
            {isDocked && (
              <span className="rounded-md bg-brand-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand-600 dark:text-brand-400">
                Docked
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className={cn(
                'inline-block h-1.5 w-1.5 rounded-full',
                isGuest ? 'bg-amber-400' : 'bg-emerald-500',
              )}
            />
            <span className="text-[11px] text-muted-foreground leading-tight">
              {statusText}
            </span>
          </div>
        </div>
      </div>

      {/* Right — Action Controls */}
      <div className="flex items-center gap-0.5">
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
            label={isDocked ? 'Collapse to Floating Assistant' : 'Dock AI Sidebar to Right'}
            onClick={onToggleDock}
          />
        </div>

        <HeaderButton
          icon={<X className="h-4 w-4" />}
          label="Close"
          onClick={onClose}
        />
      </div>
    </div>
  );
}

function HeaderButton({
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
      aria-label={label}
      className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
    >
      {icon}
    </button>
  );
}
