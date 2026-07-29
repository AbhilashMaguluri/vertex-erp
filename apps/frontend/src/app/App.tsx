import { AppProviders } from './providers';
import { AppRouter } from './router';
import { VertexButton } from '@/features/vertex';
import { VertexPanel } from '@/features/vertex';
import { useVertexWindow } from '@/features/vertex/hooks/useVertexWindow';

export function App() {
  const {
    width,
    height,
    dockedWidth,
    isOpen,
    isDocked,
    setSize,
    setOpen,
    toggleOpen,
    toggleDock,
    minWidth,
    maxWidth,
  } = useVertexWindow();

  const isDockedActive = isOpen && isDocked;

  return (
    <AppProviders>
      {/* When Vertex is docked to the right sidebar, reserve space so the main app content resizes side-by-side */}
      <style>{`
        @media (min-width: 640px) {
          body {
            padding-right: ${isDockedActive ? dockedWidth : 0}px !important;
            transition: padding-right 0.05s ease-out;
          }
        }
      `}</style>
      <AppRouter />
      <VertexButton isOpen={isOpen} onToggle={toggleOpen} />
      <VertexPanel
        isOpen={isOpen}
        isDocked={isDocked}
        onClose={() => setOpen(false)}
        onToggleDock={toggleDock}
        width={width}
        height={height}
        dockedWidth={dockedWidth}
        onResize={setSize}
        minWidth={minWidth}
        maxWidth={maxWidth}
      />
    </AppProviders>
  );
}
