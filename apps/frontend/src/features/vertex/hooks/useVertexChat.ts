// ---------------------------------------------------------------------------
// useVertexChat — Chat state management with action execution
// ---------------------------------------------------------------------------

import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  VertexMessage,
  VertexMode,
  VertexContext,
  VertexRequest,
  UIAction,
} from '../types/vertex';
import { streamMessage } from '../services/vertexApi';
import { usePageContext } from './usePageContext';
import { useVertexActions } from './useVertexActions';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useTheme } from '@/shared/theme/ThemeContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function deriveMode(roles: string[] | undefined): VertexMode {
  if (!roles || roles.length === 0) return 'guest';
  const primary = roles[0].toUpperCase();
  const modeMap: Record<string, VertexMode> = {
    STUDENT: 'student',
    COUNSELLOR: 'counsellor',
    FACULTY: 'faculty',
    HOD: 'hod',
    ADMIN: 'admin',
  };
  return modeMap[primary] || 'student';
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseVertexChatReturn {
  messages: VertexMessage[];
  isStreaming: boolean;
  error: string | null;
  mode: VertexMode;
  userName: string | null;
  sendMessage: (text: string) => void;
  clearChat: () => void;
  newChat: () => void;
  regenerate: (messageId: string) => void;
  stopStreaming: () => void;
}

export function useVertexChat(): UseVertexChatReturn {
  const [messages, setMessages] = useState<VertexMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Live Theme State
  const { theme: themePref, resolved: resolvedTheme } = useTheme();

  // Auth state
  const { status: authStatus, user: authUser } = useAuth();
  const isAuthenticated = authStatus === 'authenticated' && authUser !== null;
  const mode = isAuthenticated ? deriveMode(authUser?.roles) : 'guest';
  const userName = isAuthenticated ? authUser?.full_name ?? null : null;

  // Page context
  const pageContext = usePageContext();

  // Action executor — handles navigate, theme, toast, logout, etc.
  const { executeAction } = useVertexActions();

  // Build VertexContext
  const buildContext = useCallback((): VertexContext => {
    return {
      user: isAuthenticated && authUser
        ? {
            id: authUser.id,
            name: authUser.full_name,
            role: authUser.roles[0] || undefined,
            department: authUser.department_id || undefined,
            permissions: authUser.permissions,
          }
        : {},
      page: {
        ...pageContext,
        state: {
          ...(pageContext.params || {}),
          theme: themePref,
          resolvedTheme,
        },
      },
      mode,
      timestamp: new Date().toISOString(),
    };
  }, [isAuthenticated, authUser, pageContext, mode, themePref, resolvedTheme]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Send a message
  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);

      const userMsg: VertexMessage = {
        id: generateId(),
        role: 'user',
        content: trimmed,
        timestamp: Date.now(),
        status: 'complete',
      };

      const assistantMsg: VertexMessage = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        status: 'streaming',
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const allMessages = [
        ...messages.map((m) => ({ role: m.role, content: m.content })),
        { role: 'user' as const, content: trimmed },
      ];

      const request: VertexRequest = {
        messages: allMessages,
        context: buildContext(),
        metadata: {},
      };

      const controller = new AbortController();
      abortRef.current = controller;
      const assistantId = assistantMsg.id;

      streamMessage(
        request,
        // onToken — append token to assistant message
        (token: string) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m,
            ),
          );
        },
        // onDone
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, status: 'complete' } : m,
            ),
          );
          setIsStreaming(false);
          abortRef.current = null;
        },
        // onError
        (errorMsg: string) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content || errorMsg,
                    status: 'error',
                    responseType: 'error',
                  }
                : m,
            ),
          );
          setError(errorMsg);
          setIsStreaming(false);
          abortRef.current = null;
        },
        // onAction — execute UI actions immediately
        (action: UIAction) => {
          executeAction(action);
        },
        controller.signal,
      );
    },
    [messages, isStreaming, buildContext, executeAction],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setMessages((prev) =>
      prev.map((m) =>
        m.status === 'streaming' ? { ...m, status: 'complete' } : m,
      ),
    );
    setIsStreaming(false);
  }, []);

  const clearChat = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
    setError(null);
  }, []);

  const newChat = useCallback(() => {
    clearChat();
  }, [clearChat]);

  const regenerate = useCallback(
    (messageId: string) => {
      const idx = messages.findIndex((m) => m.id === messageId);
      if (idx <= 0) return;

      const userMsg = messages[idx - 1];
      if (userMsg.role !== 'user') return;

      setMessages((prev) => prev.filter((m) => m.id !== messageId));

      setTimeout(() => {
        sendMessage(userMsg.content);
      }, 0);
    },
    [messages, sendMessage],
  );

  return {
    messages,
    isStreaming,
    error,
    mode,
    userName,
    sendMessage,
    clearChat,
    newChat,
    regenerate,
    stopStreaming,
  };
}
