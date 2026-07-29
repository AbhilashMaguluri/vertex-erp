import { useTheme, ThemePreference } from '@/shared/theme/ThemeContext';
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

const OPTIONS: { value: ThemePreference; label: string; icon: React.ElementType; hint: string }[] = [
  { value: 'light', label: 'Light', icon: Sun, hint: 'Always use the light theme' },
  { value: 'dark', label: 'Dark', icon: Moon, hint: 'Always use the dark theme' },
  { value: 'system', label: 'System', icon: Monitor, hint: 'Match your device setting' },
];

export function AppearanceSection() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h3 className="text-base font-bold text-foreground">Appearance</h3>
        <p className="text-xs text-muted-foreground">Choose how the portal looks on this device.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {OPTIONS.map((opt) => {
          const Icon = opt.icon;
          const isActive = theme === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => setTheme(opt.value)}
              className={cn(
                'flex flex-col items-center gap-2 rounded-xl border p-5 text-center transition-all cursor-pointer',
                isActive
                  ? 'border-primary bg-primary/5 ring-2 ring-primary/30'
                  : 'border-border/80 bg-card hover:border-primary/40 hover:bg-accent/40'
              )}
            >
              <Icon className={cn('h-6 w-6', isActive ? 'text-primary' : 'text-muted-foreground')} />
              <span className="text-xs font-bold text-foreground">{opt.label}</span>
              <span className="text-[10px] text-muted-foreground leading-tight">{opt.hint}</span>
            </button>
          );
        })}
      </div>

      <p className="text-[11px] text-muted-foreground leading-relaxed">
        Your choice is remembered in this browser only.
      </p>
    </div>
  );
}
