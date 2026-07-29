import * as React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

export interface BreadcrumbItem {
  label: string;
  to?: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  showHome?: boolean;
  className?: string;
}

export function Breadcrumbs({ items, showHome = true, className }: BreadcrumbsProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center space-x-1.5 text-xs text-muted-foreground mb-4 select-none', className)}
    >
      {showHome && (
        <>
          <Link
            to="/dashboard"
            className="flex items-center text-muted-foreground/80 hover:text-foreground transition-colors p-0.5 rounded-xs"
            title="Home Dashboard"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />
        </>
      )}

      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const targetPath = item.to || item.href;

        return (
          <React.Fragment key={index}>
            {targetPath && !isLast ? (
              <Link
                to={targetPath}
                className="hover:text-foreground transition-colors font-medium hover:underline underline-offset-2"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  isLast ? 'font-semibold text-foreground' : 'text-muted-foreground'
                )}
                aria-current={isLast ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}

            {!isLast && (
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
