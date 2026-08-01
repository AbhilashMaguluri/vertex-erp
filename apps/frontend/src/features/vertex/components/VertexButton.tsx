// ---------------------------------------------------------------------------
// VertexButton — Floating AI launcher button (visible only when panel closed)
// ---------------------------------------------------------------------------
// When the panel is open, the close action lives in VertexHeader. This FAB is
// purely a launcher — it never needs to render an X icon or compete for z-index
// space with the chat input area.
// ---------------------------------------------------------------------------

import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';

interface VertexButtonProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function VertexButton({ isOpen, onToggle }: VertexButtonProps) {
  return (
    <AnimatePresence>
      {!isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="fixed bottom-6 right-6 z-50"
        >
          {/* Tooltip */}
          <div className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-foreground/90 px-2.5 py-1 text-xs font-medium text-background opacity-0 shadow-lg transition-opacity group-hover:opacity-100 peer-hover:opacity-100">
            Vertex AI
            <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-foreground/90" />
          </div>

          {/* Launcher Button — 48×48 hit target for accessibility (WCAG 2.5.8) */}
          <motion.button
            onClick={onToggle}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.95 }}
            className="peer group relative flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg shadow-brand-600/30 transition-shadow hover:shadow-xl hover:shadow-brand-600/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 cursor-pointer"
            aria-label="Open Vertex AI assistant"
          >
            {/* Pulse ring */}
            <span className="absolute inset-0 animate-ping rounded-full bg-brand-500/30 duration-[2000ms]" />

            <span className="relative z-10">
              <Sparkles className="h-5 w-5" />
            </span>
          </motion.button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

