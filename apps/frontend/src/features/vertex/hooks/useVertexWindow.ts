// ---------------------------------------------------------------------------
// useVertexWindow — Dual Mode Window State Manager (Compact vs Docked Sidebar)
// ---------------------------------------------------------------------------
// Compact Floating Mode: Quick access assistant, anchored bottom-right.
// Docked Workspace Mode: Docked persistent right AI sidebar (VS Code Copilot / Cursor style).
// ---------------------------------------------------------------------------

import { useState, useCallback, useEffect } from 'react';
import type { VertexWindowState } from '../types/vertex';

const STORAGE_KEY = 'vertex-window-state-v3';

const DEFAULT_STATE: VertexWindowState = {
  isOpen: false,
  isDocked: false,
  compactWidth: 420,
  compactHeight: 600,
  dockedWidth: 420,
};

const COMPACT_MIN_WIDTH = 420;
const COMPACT_MIN_HEIGHT = 600;

const DOCKED_MIN_WIDTH = 420;
const DOCKED_MAX_WIDTH = 700;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function loadState(): VertexWindowState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<VertexWindowState>;
      return {
        isOpen: parsed.isOpen ?? false,
        isDocked: parsed.isDocked ?? false,
        compactWidth: clamp(parsed.compactWidth ?? DEFAULT_STATE.compactWidth, COMPACT_MIN_WIDTH, 800),
        compactHeight: clamp(parsed.compactHeight ?? DEFAULT_STATE.compactHeight, COMPACT_MIN_HEIGHT, 900),
        dockedWidth: clamp(parsed.dockedWidth ?? DEFAULT_STATE.dockedWidth, DOCKED_MIN_WIDTH, DOCKED_MAX_WIDTH),
      };
    }
  } catch {
    // Fallback on defaults
  }
  return { ...DEFAULT_STATE };
}

function saveState(state: VertexWindowState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Non-fatal
  }
}

export function useVertexWindow() {
  const [state, setState] = useState<VertexWindowState>(loadState);

  useEffect(() => {
    saveState(state);
  }, [state]);

  const setOpen = useCallback((isOpen: boolean) => {
    setState((prev) => ({ ...prev, isOpen }));
  }, []);

  const toggleOpen = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  }, []);

  const toggleDock = useCallback(() => {
    setState((prev) => ({ ...prev, isDocked: !prev.isDocked }));
  }, []);

  const setSize = useCallback((width: number, height: number) => {
    setState((prev) => {
      if (prev.isDocked) {
        return {
          ...prev,
          dockedWidth: clamp(width, DOCKED_MIN_WIDTH, DOCKED_MAX_WIDTH),
        };
      }
      return {
        ...prev,
        compactWidth: clamp(width, COMPACT_MIN_WIDTH, 800),
        compactHeight: clamp(height, COMPACT_MIN_HEIGHT, 900),
      };
    });
  }, []);

  const currentWidth = state.isDocked ? state.dockedWidth : state.compactWidth;
  const currentHeight = state.compactHeight;
  const minWidth = state.isDocked ? DOCKED_MIN_WIDTH : COMPACT_MIN_WIDTH;
  const maxWidth = state.isDocked ? DOCKED_MAX_WIDTH : 800;

  return {
    isOpen: state.isOpen,
    isDocked: state.isDocked,
    width: currentWidth,
    height: currentHeight,
    compactWidth: state.compactWidth,
    compactHeight: state.compactHeight,
    dockedWidth: state.dockedWidth,
    minWidth,
    maxWidth,
    setOpen,
    toggleOpen,
    toggleDock,
    setSize,
  };
}
