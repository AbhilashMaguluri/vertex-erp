// ---------------------------------------------------------------------------
// useVertexActions — Executes UI actions received from Vertex backend
// ---------------------------------------------------------------------------
// Actions execute immediately. The AI confirms after.
// Uses React Router navigation (no window.location), preserves SPA behavior.
// ---------------------------------------------------------------------------

import { useCallback } from 'react';
import { useTheme, type ThemePreference } from '@/shared/theme/ThemeContext';
import type { UIAction } from '../types/vertex';

/**
 * Hook that returns an executeAction function.
 *
 * Navigation uses history.pushState (patched by usePageContext) so
 * react-router picks it up without a full page reload.
 */
export function useVertexActions() {
  const { setTheme } = useTheme();

  const executeAction = useCallback(
    (action: UIAction) => {
      switch (action.type) {
        case 'navigate': {
          const route = action.route || '/dashboard';
          // Use history.pushState so react-router detects the navigation
          // without a full page reload. Our usePageContext patches pushState
          // to notify listeners — this preserves SPA behavior.
          window.history.pushState({}, '', route);
          // Dispatch popstate so react-router re-renders
          window.dispatchEvent(new PopStateEvent('popstate'));
          break;
        }

        case 'setTheme': {
          const mode = (action.mode || 'system') as ThemePreference;
          setTheme(mode);
          break;
        }

        case 'showToast': {
          // Use a simple native approach for MVP. Replace with your
          // toast library when one is added to the project.
          const msg = action.message || '';
          if (msg) {
            // Create a lightweight toast notification
            _showNativeToast(msg, action.variant || 'info');
          }
          break;
        }

        case 'logout': {
          // Navigate to login — AuthContext will handle cleanup
          window.history.pushState({}, '', '/login');
          window.dispatchEvent(new PopStateEvent('popstate'));
          // Clear auth tokens
          try {
            localStorage.removeItem('access_token');
            sessionStorage.clear();
          } catch {
            // Non-fatal
          }
          // Force reload to reset all state cleanly
          window.location.reload();
          break;
        }

        case 'openDialog': {
          // Dispatch a custom event that dialog components can listen to
          window.dispatchEvent(
            new CustomEvent('vertex:dialog', {
              detail: { action: 'open', dialog: action.dialog },
            }),
          );
          break;
        }

        case 'closeDialog': {
          window.dispatchEvent(
            new CustomEvent('vertex:dialog', {
              detail: { action: 'close' },
            }),
          );
          break;
        }
      }
    },
    [setTheme],
  );

  return { executeAction };
}

// ---------------------------------------------------------------------------
// Lightweight toast implementation (no external dependency)
// ---------------------------------------------------------------------------

function _showNativeToast(message: string, variant: string) {
  const toast = document.createElement('div');
  const colors: Record<string, string> = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6',
  };
  const bg = colors[variant] || colors.info;

  Object.assign(toast.style, {
    position: 'fixed',
    bottom: '80px',
    right: '24px',
    padding: '12px 20px',
    borderRadius: '12px',
    background: bg,
    color: 'white',
    fontSize: '14px',
    fontWeight: '500',
    zIndex: '9999',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    opacity: '0',
    transform: 'translateY(8px)',
    transition: 'opacity 0.3s, transform 0.3s',
  });
  toast.textContent = message;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  // Auto-dismiss after 3s
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
