// ---------------------------------------------------------------------------
// VertexButton — Floating AI launcher button
// ---------------------------------------------------------------------------

import { motion } from 'framer-motion';
import { Sparkles, X } from 'lucide-react';

interface VertexButtonProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function VertexButton({ isOpen, onToggle }: VertexButtonProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 sm:bottom-6 sm:right-6">
      {/* Tooltip */}
      {!isOpen && (
        <div className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-foreground/90 px-2.5 py-1 text-xs font-medium text-background opacity-0 shadow-lg transition-opacity group-hover:opacity-100 peer-hover:opacity-100">
          Vertex
          <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-foreground/90" />
        </div>
      )}

      {/* Button */}
      <motion.button
        onClick={onToggle}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        className="peer group relative flex h-13 w-13 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg shadow-brand-600/30 transition-shadow hover:shadow-xl hover:shadow-brand-600/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 cursor-pointer"
        aria-label={isOpen ? 'Close Vertex' : 'Open Vertex'}
      >
        {/* Pulse ring — only when closed */}
        {!isOpen && (
          <span className="absolute inset-0 animate-ping rounded-full bg-brand-500/30 duration-[2000ms]" />
        )}

        {/* Icon with rotation transition */}
        <motion.span
          initial={false}
          animate={{ rotate: isOpen ? 90 : 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          className="relative z-10"
        >
          {isOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Sparkles className="h-5 w-5" />
          )}
        </motion.span>
      </motion.button>
    </div>
  );
}
