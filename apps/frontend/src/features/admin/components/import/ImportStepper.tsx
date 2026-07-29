import { Check, LucideIcon } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export type ImportStep = 1 | 2 | 3 | 4 | 5;

export interface StepDefinition {
  id: ImportStep;
  label: string;
  hint: string;
  icon: LucideIcon;
}

interface ImportStepperProps {
  steps: StepDefinition[];
  current: ImportStep;
  /** Steps the administrator may jump back to — never forward. */
  onNavigate?: (step: ImportStep) => void;
  /** Upper bound on which earlier steps are reachable. Pass 0 once the import
   *  is running to lock the whole trail: the plan has already been committed. */
  navigableUpTo?: number;
}

export function ImportStepper({ steps, current, onNavigate, navigableUpTo = 1 }: ImportStepperProps) {
  return (
    <ol className="flex w-full items-stretch gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-card/80 p-2 shadow-xs">
      {steps.map((step, index) => {
        const isComplete = step.id < current;
        const isCurrent = step.id === current;
        const canNavigate = Boolean(onNavigate) && step.id < current && step.id <= navigableUpTo;
        const Icon = step.icon;

        return (
          <li key={step.id} className="flex min-w-[9.5rem] flex-1 items-center gap-1">
            <button
              type="button"
              disabled={!canNavigate}
              onClick={() => canNavigate && onNavigate?.(step.id)}
              aria-current={isCurrent ? 'step' : undefined}
              className={cn(
                'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all duration-150',
                isCurrent && 'bg-brand-600 shadow-md shadow-brand-600/25',
                !isCurrent && isComplete && 'bg-emerald-500/10',
                !isCurrent && !isComplete && 'bg-transparent',
                canNavigate ? 'cursor-pointer hover:bg-emerald-500/20' : 'cursor-default'
              )}
            >
              <span
                className={cn(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[11px] font-black',
                  isCurrent && 'bg-white/20 text-white',
                  !isCurrent && isComplete && 'bg-emerald-500 text-white',
                  !isCurrent && !isComplete && 'bg-muted text-muted-foreground'
                )}
              >
                {isComplete ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
              </span>

              <span className="flex min-w-0 flex-col">
                <span
                  className={cn(
                    'truncate text-[11px] font-black uppercase tracking-wider',
                    isCurrent ? 'text-white/70' : 'text-muted-foreground/70'
                  )}
                >
                  Step {index + 1}
                </span>
                <span
                  className={cn(
                    'truncate text-xs font-bold',
                    isCurrent && 'text-white',
                    !isCurrent && isComplete && 'text-emerald-700 dark:text-emerald-300',
                    !isCurrent && !isComplete && 'text-muted-foreground'
                  )}
                  title={step.hint}
                >
                  {step.label}
                </span>
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
