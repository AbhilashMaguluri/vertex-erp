// ---------------------------------------------------------------------------
// TypingIndicator — Randomized thinking messages with animated dots
// ---------------------------------------------------------------------------

import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

const THINKING_PHRASES = [
  'Vertex is thinking',
  'Analyzing your request',
  'Searching knowledge base',
  'Preparing response',
  'Reviewing context',
  'Processing',
];

function getRandomPhrase(): string {
  return THINKING_PHRASES[Math.floor(Math.random() * THINKING_PHRASES.length)];
}

export function TypingIndicator() {
  const [phrase] = useState(getRandomPhrase);

  // Animated dots
  const [dotCount, setDotCount] = useState(1);
  useEffect(() => {
    const interval = setInterval(() => {
      setDotCount((c) => (c % 3) + 1);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const dots = '.'.repeat(dotCount);
  const spacer = '\u00A0'.repeat(3 - dotCount); // Non-breaking spaces to prevent layout shift

  return (
    <div className="flex items-start gap-3 px-4 py-3">
      {/* Avatar */}
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 shadow-sm">
        <Sparkles className="h-3.5 w-3.5 text-white" />
      </div>
      {/* Text */}
      <div className="flex items-center gap-1 pt-1">
        <span className="text-sm text-muted-foreground">
          {phrase}
          <span className="inline-block w-[1.5ch] text-left">{dots}{spacer}</span>
        </span>
      </div>
    </div>
  );
}
